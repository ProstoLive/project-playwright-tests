"""Page Object карточки товара."""

import re

from playwright.sync_api import expect

from core.logger import log_step
from ui.base_page import BasePage


class ProductPage(BasePage):
    """Название, цена, артикул и добавление товара в корзину."""

    PRICE = ".detail-price__item.current"
    ADD_TO_CART = ".detail-buy__button.add_basket"
    IN_CART = ".detail-buy__button.remove_basket"

    @log_step("Проверить, что карточка товара открылась")
    def wait_loaded(self) -> "ProductPage":
        expect(self.page.get_by_role("heading", level=1)).to_be_visible()
        expect(self.page.locator(self.PRICE).filter(visible=True).first).to_be_visible()
        return self

    def product_name(self) -> str:
        return self.page.get_by_role("heading", level=1).inner_text().strip()

    def product_price(self) -> str:
        return self.page.locator(self.PRICE).filter(visible=True).first.inner_text().strip()

    def product_article(self) -> str:
        """Артикул указан рядом с подписью в характеристиках."""
        prefix = re.compile(r"^\s*Артикул\s*:?\s*#?\s*", re.IGNORECASE)
        row = self.page.get_by_role("listitem").filter(has_text=prefix)
        return prefix.sub("", row.inner_text()).strip()

    @log_step("Добавить товар в корзину")
    def add_to_cart(self) -> None:
        self._click(self.page.locator(self.ADD_TO_CART).filter(visible=True).first, "кнопка «В корзину»")
        expect(
            self.page.locator(self.IN_CART).filter(visible=True).first,
            "Карточка товара не отразила добавление в корзину",
        ).to_be_visible()
