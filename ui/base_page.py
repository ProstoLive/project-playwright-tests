"""Общая логика Page Object: навигация, ожидания, клики, логирование."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect

from core.config import settings
from core.logger import get_logger, log_step, register_secret, scrub


class BasePage:
    """Базовый класс всех страниц приложения.

    Playwright автоматически ждёт готовности элементов при действиях, а
    `expect` — их ожидаемого состояния. В коде нет `time.sleep()`.
    """

    def __init__(self, page: Page) -> None:
        self.page = page
        self.log = get_logger(self.__class__.__name__)

    @log_step("Открыть главную страницу сайта")
    def open_home(self) -> "BasePage":
        self.log.info("Открываю главную страницу")
        self.log.debug("URL: %s", scrub(settings.base_url))
        self.page.goto(settings.base_url, wait_until="domcontentloaded")
        self.dismiss_city_popup()
        return self

    def dismiss_city_popup(self) -> None:
        """Закрыть вопрос «Ваш город Москва?», если он появился."""
        city_confirm = self.page.get_by_text("Да, все верно", exact=True)
        if city_confirm.count() and city_confirm.first.is_visible():
            self.log.info("Подтверждаю выбранный город")
            city_confirm.first.click()

    def _click(self, locator: Locator, name: str) -> None:
        """Прокрутить элемент к видимой области и кликнуть (с auto-wait)."""
        self.log.info("Нажимаю: %s", name)
        self.log.debug("Локатор для %s: %s", name, locator)
        locator.scroll_into_view_if_needed()
        locator.click()

    def _fill(self, locator: Locator, value: str, name: str, *, sensitive: bool = False) -> None:
        """Очистить поле и ввести текст реальными нажатиями клавиш.

        На zvet.ru проверка формы привязана к `onkeyup`, поэтому обычный
        `locator.fill()` не обновляет состояние кнопки отправки.
        """
        self.log.info("Заполняю поле: %s", name)
        if sensitive:
            register_secret(value)
        safe_value = "********" if sensitive else scrub(value)
        self.log.debug("Поле %s: значение=%s; локатор=%s", name, safe_value, locator)
        locator.scroll_into_view_if_needed()
        locator.clear()
        locator.press_sequentially(value)

    def _fill_phone(self, locator: Locator, phone: str, *, allow_incomplete: bool = False) -> None:
        """Заполнить телефон целиком и сверить цифры после обработки маской."""
        register_secret(phone)
        digits = re.sub(r"\D", "", phone)
        if not allow_incomplete:
            if len(digits) == 10:
                digits = f"7{digits}"
            if len(digits) != 11 or digits[0] not in "78":
                raise ValueError("Для формы zvet.ru нужен российский номер из 10 цифр и кода +7")
            digits = f"7{digits[1:]}"
        value = f"+{digits}"
        register_secret(value)
        self.log.info("Заполняю поле: номер телефона")
        self.log.debug("Локатор поля телефона: %s", locator)
        locator.fill(value)
        locator.press("End")
        locator.blur()
        if not allow_incomplete:
            displayed = locator.input_value()
            register_secret(displayed)
            if re.sub(r"\D", "", displayed) != digits:
                raise AssertionError("Цифры телефона в форме отличаются от номера в конфигурации")

    def _expect_visible(self, locator: Locator, name: str) -> None:
        self.log.info("Проверяю видимость: %s", name)
        expect(locator, f"Не виден элемент: {name}").to_be_visible()

    @log_step("Принять политику обработки персональных данных")
    def accept_policy(self, checkbox_box: Locator) -> None:
        """Открыть окно согласия, прокрутить документ до конца, принять.

        Кнопка «Принять» доступна после прокрутки текста политики.
        """
        self._click(checkbox_box, "чекбокс согласия")
        self.confirm_policy(self.page.locator("#policyPopup"))

    def confirm_policy(self, popup: Locator) -> None:
        self._expect_visible(popup, "окно политики")
        content = popup.locator(".policy-popup__content")
        self.log.info("Прокручиваю политику до конца")
        content.evaluate("el => { el.scrollTop = el.scrollHeight; el.dispatchEvent(new Event('scroll')); }")
        accept = popup.get_by_role("button", name="Принять", exact=True)
        expect(accept, "Кнопка принятия политики не разблокировалась").to_be_enabled()
        self._click(accept, "Принять политику")
        expect(popup, "Окно политики не закрылось").to_be_hidden()
