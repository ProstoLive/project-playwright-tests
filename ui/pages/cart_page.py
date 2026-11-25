"""Page Object корзины на странице оформления заказа."""

import re
from decimal import Decimal

from playwright.sync_api import Locator, expect

from core.config import settings
from core.logger import log_step
from ui.base_page import BasePage


class CartPage(BasePage):
    """Содержимое корзины и рассчитанная сумма заказа."""

    URL = "/vue/basket/"
    ITEM = ".basket-item"
    ITEM_CODE = ".basket-item__code"
    ITEM_PRICE = ".basket-item__price:not(.basket-item__price--old)"
    EMPTY_CART = ".cart-empty"
    TOTAL_LABEL = "Итоговая сумма к оплате"

    @log_step("Открыть корзину")
    def open(self) -> "CartPage":
        self.page.goto(f"{settings.base_url}{self.URL}", wait_until="domcontentloaded")
        expect(
            self.items.first.or_(self.page.locator(self.EMPTY_CART)).first,
            "Корзина не отрисовалась",
        ).to_be_visible(timeout=settings.navigation_timeout)
        return self

    @property
    def items(self) -> Locator:
        return self.page.locator(self.ITEM).filter(visible=True)

    def expect_empty(self) -> None:
        expect(self.page.locator(self.EMPTY_CART), "Для E2E нужна исходно пустая корзина").to_be_visible()
        expect(self.items).to_have_count(0)

    def _with_article(self, article: str) -> Locator:
        pattern = re.compile(rf"^\s*(?:Артикул\s*:?\s*)?#?\s*{re.escape(article)}\s*$", re.IGNORECASE)
        code = self.page.locator(self.ITEM_CODE).filter(has_text=pattern)
        return self.items.filter(has=code)

    def expect_single_item(self, article: str) -> None:
        expect(self.items, "В корзине должна быть одна позиция").to_have_count(1)
        expect(self._with_article(article), "Артикул в корзине отличается от артикула карточки").to_be_visible()

    def item_title(self) -> str:
        return self.items.locator(".basket-item__title").inner_text().strip()

    def item_price(self) -> str:
        return self.items.locator(self.ITEM_PRICE).filter(visible=True).inner_text().strip()

    def item_quantity(self) -> int:
        quantity = self.items.locator(".vue-counter__value")
        if quantity.evaluate("el => el.matches('input')"):
            text = quantity.input_value()
        else:
            text = quantity.inner_text()
        match = re.fullmatch(r"\s*(\d+)(?:\s*шт\.?)?\s*", text)
        assert match, "Количество товара имеет неожиданный формат"
        return int(match[1])

    @log_step("Получить итоговую сумму к оплате")
    def total_amount(self) -> str:
        label = self.page.get_by_text(self.TOTAL_LABEL, exact=True)
        row = self.page.locator(".cart-summary__sums-row").filter(has=label)
        return row.locator("span").last.inner_text().strip()

    @log_step("Удалить из корзины товар, добавленный тестом")
    def remove_if_present(self, article: str) -> None:
        item = self._with_article(article)
        delete = item.locator(".basket-item__delete")
        if delete.is_visible():
            self._click(delete, "удалить позицию теста")
            expect(delete, "Кнопка удаления позиции осталась доступной").to_be_hidden()
            self.open()
            expect(item, "Позиция теста осталась в корзине").to_have_count(0)

    @staticmethod
    def normalize_price(value: str) -> Decimal:
        """Привести текстовую цену в рублях к числу для сравнения."""
        match = re.fullmatch(r"([\d\s]+(?:[,.]\d{1,2})?)\s*(?:₽|руб\.?)?", value.strip())
        assert match, "Цена отсутствует или имеет неожиданный формат"
        return Decimal("".join(match[1].split()).replace(",", "."))
