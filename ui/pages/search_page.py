"""Page Object поиска и выдачи каталога."""

import re
from urllib.parse import parse_qs, urljoin, urlsplit

from playwright.sync_api import Locator, expect

from core.logger import log_step
from ui.base_page import BasePage
from ui.pages.product_page import ProductPage


class SearchPage(BasePage):
    """Искать из шапки и открывать первую карточку с кнопкой покупки."""

    RESULT_CARD = "._catalog-products-wr .product-card"
    CARD_TITLE = "a.product-card__title"
    CARD_PRICE = ".product-card__costs span"
    CARD_ADD_BUTTON = ".product-card__btn--add"
    DIGI_CARD = ".digi-products-grid .digi-product"
    DIGI_TITLE = "a.digi-product__label"
    DIGI_PRICE = re.compile(r"^\s*\d[\d\s]*(?:[,.]\d{1,2})?\s*₽\s*$")

    @property
    def first_available_card(self) -> Locator:
        add_to_cart = self.page.locator(self.CARD_ADD_BUTTON).filter(visible=True)
        catalogue = self.page.locator(self.RESULT_CARD).filter(has=add_to_cart)
        digi = self.page.locator(self.DIGI_CARD).filter(has=self.page.get_by_text(self.DIGI_PRICE))
        return catalogue.or_(digi).filter(visible=True).first

    @staticmethod
    def _matches_query(url: str, query: str) -> bool:
        address = urlsplit(url)
        params = parse_qs(address.query, keep_blank_values=True)
        if address.path.startswith("/catalog/") and params.get("q") == [query]:
            return True
        return "digiSearch" in params and params.get("term") == [query]

    @log_step("Выполнить поиск по каталогу")
    def search(self, query: str) -> None:
        field = self.page.locator('input[name="q"]').filter(visible=True)
        field.fill(query)
        field.press("Enter")
        self.page.wait_for_url(
            lambda url: self._matches_query(url, query), wait_until="commit",
        )
        expect(self.first_available_card, "В выдаче нет доступных для покупки товаров").to_be_visible()

    @property
    def _first_title(self) -> Locator:
        return self.first_available_card.locator(f"{self.CARD_TITLE}, {self.DIGI_TITLE}")

    def first_product_title(self) -> str:
        return self._first_title.inner_text().strip()

    def first_product_price(self) -> str:
        card = self.first_available_card
        is_digi = card.locator(self.DIGI_TITLE).count() > 0
        price = card.get_by_text(self.DIGI_PRICE) if is_digi else card.locator(self.CARD_PRICE)
        self.log.debug("Источник карточки поиска: %s", "DigiSearch" if is_digi else "каталог")
        return price.filter(visible=True).first.inner_text().strip()

    @log_step("Открыть карточку товара из выдачи")
    def open_first_product(self) -> ProductPage:
        href = self._first_title.get_attribute("href")
        assert href, "У названия товара отсутствует ссылка на карточку"
        self.page.goto(urljoin(self.page.url, href), wait_until="domcontentloaded")
        return ProductPage(self.page)
