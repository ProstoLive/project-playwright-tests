"""Фикстуры Playwright и диагностика падений для локального прогона и Allure."""

import hashlib
import io
import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import allure
import pytest
from allure_commons import plugin_manager as allure_plugins
from playwright.sync_api import Browser, BrowserContext, Page, expect, sync_playwright

from core.config import settings
from core.logger import EMAIL_PATTERN, PHONE_PATTERN, MaskedFormatter, get_logger, scrub
from core.runner.allure_reporting import AllureRedaction
from ui.pages.checkout_page import CheckoutPage
from ui.pages.login_page import LoginPage
from ui.pages.search_page import SearchPage

log = get_logger("runner")
RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
TEST_LOG = pytest.StashKey[io.StringIO]()
PAGE = pytest.StashKey[Page]()

# Маркетинговая подложка перекрывает клики по интерфейсу магазина.
BLOCK_THIRD_PARTY_OVERLAY = """
document.addEventListener('DOMContentLoaded', () => {
  const remove = () => document.querySelectorAll(
    '#popmechanic-snippet, .popmechanic-js-clickable-overlay, .popmechanic-snippet__widget'
  ).forEach(element => element.remove());
  remove();
  new MutationObserver(remove).observe(document.documentElement, {childList: true, subtree: true});
});
"""


def pytest_configure(config: pytest.Config) -> None:
    expect.set_options(timeout=settings.default_timeout)
    settings.path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    if config.option.allure_report_dir:
        redaction = AllureRedaction()
        allure_plugins.register(redaction)
        config.add_cleanup(lambda: allure_plugins.unregister(redaction))


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Запустить браузер с настройками прогона."""
    if not settings.base_url:
        pytest.fail("Задайте BASE_URL в .env", pytrace=False)
    log.info("Запускаю браузер %s (headless=%s)", settings.browser, settings.headless)
    with sync_playwright() as playwright:
        launcher = getattr(playwright, settings.browser, None)
        if settings.browser not in {"chromium", "firefox", "webkit"}:
            pytest.fail("BROWSER должен быть chromium, firefox или webkit", pytrace=False)
        instance = launcher.launch(headless=settings.headless, slow_mo=settings.browser_slow_mo)
        try:
            yield instance
        finally:
            instance.close()


@pytest.fixture()
def context(browser: Browser) -> Iterator[BrowserContext]:
    """Открыть новый браузерный контекст для каждого теста."""
    instance = browser.new_context(
        viewport={"width": settings.viewport_width, "height": settings.viewport_height},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
    )
    instance.set_default_timeout(settings.default_timeout)
    instance.set_default_navigation_timeout(settings.navigation_timeout)
    instance.add_init_script(BLOCK_THIRD_PARTY_OVERLAY)
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture()
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Page:
    instance = context.new_page()
    request.node.stash[PAGE] = instance
    return instance


@pytest.fixture()
def guest_login(page: Page) -> Iterator[LoginPage]:
    """Открыть сайт гостем и завершить сеанс аккаунта при выходе из теста."""
    login = LoginPage(page)
    login.open_home()
    login.expect_guest()
    yield login
    login.logout()


@pytest.fixture()
def search_page(page: Page) -> SearchPage:
    return SearchPage(page)


@pytest.fixture()
def checkout_page(page: Page) -> CheckoutPage:
    return CheckoutPage(page)


@pytest.fixture(scope="session")
def email_account() -> None:
    if not settings.has_account:
        pytest.skip("Заполните TEST_EMAIL и TEST_PASSWORD в .env")


@pytest.fixture(scope="session")
def phone_account() -> None:
    if not settings.manual_tests or settings.headless:
        pytest.skip("Для капчи и SMS запустите с MANUAL_TESTS=1 HEADLESS=0")
    if not settings.phone:
        pytest.skip("Заполните TEST_PHONE номером существующего аккаунта")


@pytest.fixture(scope="session")
def checkout_data(email_account: None) -> None:
    if not (settings.customer_phone or settings.phone):
        pytest.skip("Для формы заказа нужен CUSTOMER_PHONE или TEST_PHONE")


@pytest.fixture()
def restore_cart(guest_login: LoginPage, checkout_page: CheckoutPage) -> Iterator[set[str]]:
    """Удалить только позицию теста перед выходом из аккаунта."""
    added_articles: set[str] = set()
    yield added_articles
    if added_articles:
        cart = checkout_page.open()
        for article in added_articles:
            cart.remove_if_present(article)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item: pytest.Item) -> Iterator[None]:
    """Захватить записи текущего теста, включая фикстуры."""
    stream = io.StringIO()
    item.stash[TEST_LOG] = stream
    handler = logging.StreamHandler(stream)
    handler.setFormatter(MaskedFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    logger = logging.getLogger("autotests")
    logger.addHandler(handler)
    try:
        return (yield)
    finally:
        logger.removeHandler(handler)
        handler.close()
        stream.close()


def _save_failure_screenshot(page: Page, path: Path) -> bytes:
    masks = [
        page.locator("input, textarea, [contenteditable], iframe, ._captchainer img"),
        page.get_by_text(EMAIL_PATTERN),
        page.get_by_text(PHONE_PATTERN),
    ]
    for value in (settings.customer_name, settings.customer_address):
        if value:
            masks.append(page.get_by_text(value, exact=False))
    return page.screenshot(path=path, mask=masks, animations="disabled", timeout=5000)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Iterator[pytest.TestReport]:
    """Сохранить маскированную диагностику и прикрепить её к результату теста."""
    report: pytest.TestReport = yield
    report.sections = [(name, scrub(value)) for name, value in report.sections]
    if report.passed and report.when == "call":
        log.info("Тест %s пройден", item.name)
    if not report.failed:
        return report

    report.longrepr = scrub(report.longreprtext)
    log.error("Ошибка в тесте %s (%s)", item.name, report.when)
    suffix = hashlib.sha256(item.nodeid.encode()).hexdigest()[:8]
    directory = settings.path(settings.reports_dir) / RUN_ID
    stem = f"{item.originalname or item.name}-{suffix}-{report.when}"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        traceback = report.longreprtext
        (directory / f"{stem}-traceback.txt").write_text(traceback, encoding="utf-8")
        allure.attach(traceback, name="Текст ошибки", attachment_type=allure.attachment_type.TEXT)
        stream = item.stash.get(TEST_LOG, None)
        if stream is not None:
            test_log = scrub(stream.getvalue())
            (directory / f"{stem}-test.log").write_text(test_log, encoding="utf-8")
            allure.attach(test_log, name="Журнал теста", attachment_type=allure.attachment_type.TEXT)
        page = item.stash.get(PAGE, None)
        if page is not None and not page.is_closed():
            screenshot = _save_failure_screenshot(page, directory / f"{stem}-screenshot.png")
            allure.attach(screenshot, name="Скриншот при падении", attachment_type=allure.attachment_type.PNG)
    except Exception as exc:
        log.warning("Не удалось сохранить диагностику: %s", exc)
    return report
