"""Page Object формы заказа внутри корзины."""

import re

from playwright.sync_api import Locator, expect

from core.logger import log_step
from ui.pages.cart_page import CartPage


class CheckoutPage(CartPage):
    """Подготовить контакты, адрес и согласие перед отправкой заказа."""

    NAME = "name"
    PHONE = "phone"
    CITY = "city"
    ADDRESS = "adress"
    EMAIL = "email"

    def _field(self, name: str) -> Locator:
        if name == self.EMAIL:
            return self.page.get_by_role("textbox", name="Электронная почта", exact=True)
        return self.page.locator(f'input[name="{name}"]').filter(visible=True)

    @property
    def edit_contacts(self) -> Locator:
        return self.page.get_by_role("button", name="Изменить", exact=True)

    @log_step("Подготовить контакты покупателя")
    def prepare_contacts(self, name: str, phone: str) -> None:
        expect(self.page.get_by_role("heading", name="Контактные данные", exact=True)).to_be_visible()
        field = self._field(self.NAME)
        expect(self.edit_contacts.or_(field).first, "Блок контактов не загрузился").to_be_visible()
        if not self.edit_contacts.is_visible():
            self._fill(field, name, "ФИО", sensitive=True)
            self._fill_phone(self._field(self.PHONE), phone)

    @log_step("Заполнить город доставки")
    def fill_city(self, city: str) -> None:
        field = self._field(self.CITY)
        field.fill(city)
        suggestion = self.page.get_by_text(city, exact=True).filter(visible=True)
        self._click(suggestion, "город из подсказок доставки")
        expect(field, "Выбранный город должен остаться в поле доставки").to_have_value(city)

    @log_step("Заполнить адрес доставки")
    def fill_address(self, address: str) -> None:
        field = self._field(self.ADDRESS)
        self._fill(field, address, "адрес доставки", sensitive=True)
        field.blur()

    @log_step("Заполнить почту покупателя")
    def fill_email(self, email: str) -> None:
        field = self._field(self.EMAIL)
        self._fill(field, email, "e-mail", sensitive=True)
        field.blur()

    @property
    def consent_label(self) -> Locator:
        return self.page.locator(".cart-summary__checkboxes label.g-checkbox").filter(
            has_text="персональных данных", visible=True
        )

    @log_step("Отметить согласие на обработку персональных данных")
    def accept_personal_data_consent(self) -> None:
        checkbox = self.consent_label.locator('input[type="checkbox"]')
        if not checkbox.is_checked():
            box = self.consent_label.locator(".g-checkbox__box")
            self._click(box, "согласие на обработку персональных данных")
            popup = self.page.get_by_role("dialog", name="Персональные данные")
            scroll = popup.get_by_role("button", name="Прокрутить вниз", exact=True)
            self._click(scroll, "прокрутить согласие до конца")
            accept = popup.get_by_role("button", name="Принять", exact=True)
            self._click(accept, "принять согласие")
            expect(popup).to_be_hidden()
        expect(checkbox).to_be_checked()

    @log_step("Проверить готовность формы к отправке")
    def expect_ready_for_order(self) -> None:
        for name in (self.CITY, self.ADDRESS, self.EMAIL):
            expect(self._field(name), f"Поле {name} осталось пустым").to_have_value(re.compile(r"\S"))
        if not self.edit_contacts.is_visible():
            for name in (self.NAME, self.PHONE):
                expect(self._field(name), f"Поле {name} осталось пустым").to_have_value(re.compile(r"\S"))
        errors = self.page.locator(".g-input__sub").filter(visible=True, has_text=re.compile(r"\S"))
        expect(errors, "В форме заказа видны ошибки валидации").to_have_count(0)
        submit = self.page.get_by_role("button", name="Оформить заказ", exact=True)
        expect(submit).to_be_visible()
        expect(submit).to_be_enabled()
