"""Page Object поиска и выдачи каталога."""

from urllib.parse import parse_qs, urljoin, urlsplit

from playwright.sync_api import Locator, expect

from core.logger import log_step
from ui.base_page import BasePage
from ui.pages.product_page import ProductPage


class SearchPage(BasePage):
    """Искать из шапки и открывать первую карточку с кнопкой покупки."""

    RESULT_CARD = ".product-card"
    CARD_TITLE = "a.product-card__title"
    CARD_PRICE = ".product-card__costs span"
    CARD_ADD_BUTTON = ".product-card__btn--add"

    @property
    def first_available_card(self) -> Locator:
        available = self.page.locator(self.CARD_ADD_BUTTON).filter(visible=True)
        return self.page.locator(self.RESULT_CARD).filter(has=available).first

    @log_step("Выполнить поиск по каталогу")
    def search(self, query: str) -> None:
        field = self.page.locator('input[name="q"]').filter(visible=True)
        self._fill(field, query, "поиск товара")
        field.press("Enter")
        self.page.wait_for_url(
            lambda url: urlsplit(url).path.startswith("/catalog/")
            and parse_qs(urlsplit(url).query).get("q") == [query],
            wait_until="domcontentloaded",
        )
        expect(self.first_available_card, "В выдаче нет доступных для покупки товаров").to_be_visible()

    def first_product_title(self) -> str:
        return self.first_available_card.locator(self.CARD_TITLE).inner_text().strip()

    def first_product_price(self) -> str:
        return self.first_available_card.locator(self.CARD_PRICE).first.inner_text().strip()

    @log_step("Открыть карточку товара из выдачи")
    def open_first_product(self) -> ProductPage:
        title = self.first_available_card.locator(self.CARD_TITLE)
        href = title.get_attribute("href")
        assert href, "У названия товара отсутствует ссылка на карточку"
        self.page.goto(urljoin(self.page.url, href), wait_until="domcontentloaded")
        return ProductPage(self.page)
