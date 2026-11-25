"""Сквозная покупка до отправки заказа (ТК-А02, М10, М11, М18, М19)."""

import allure
import pytest

from core.config import settings
from ui.pages.checkout_page import CheckoutPage
from ui.pages.login_page import LoginPage
from ui.pages.search_page import SearchPage


@pytest.mark.e2e
@allure.epic("Цвет диванов")
@allure.feature("Покупка")
@allure.story("Оформление заказа")
def test_e2e_purchase(
    checkout_data: None,
    guest_login: LoginPage,
    search_page: SearchPage,
    checkout_page: CheckoutPage,
    restore_cart: set[str],
) -> None:
    """Войти, найти товар, сверить карточку и корзину, заполнить форму заказа."""
    guest_login.sign_in_by_email(settings.email, settings.password)
    checkout_page.open().expect_empty()

    search_page.open_home()
    search_page.search(settings.search_query)
    card_title = " ".join(search_page.first_product_title().casefold().split())
    card_price = checkout_page.normalize_price(search_page.first_product_price())
    product = search_page.open_first_product().wait_loaded()

    title = " ".join(product.product_name().casefold().split())
    price = checkout_page.normalize_price(product.product_price())
    article = product.product_article()
    assert card_title and card_title in title, "Название товара отличается от названия в поиске"
    assert card_price == price and price > 0, "Текущая цена товара отличается от цены в поиске"
    assert article, "На странице товара отсутствует артикул"

    restore_cart.add(article)
    product.add_to_cart()
    checkout_page.open().expect_single_item(article)
    cart_title = " ".join(checkout_page.item_title().casefold().split())
    assert card_title in cart_title, "Название в корзине отличается от названия в поиске"
    assert checkout_page.normalize_price(checkout_page.item_price()) == price, "В корзине другая цена"
    assert checkout_page.item_quantity() == 1, "В корзине должна быть одна единица товара"

    checkout_page.accept_personal_data_consent()
    checkout_page.prepare_contacts(settings.customer_name, settings.customer_phone or settings.phone)
    checkout_page.fill_city(settings.customer_city)
    checkout_page.fill_address(settings.customer_address)
    checkout_page.fill_email(settings.customer_email or settings.email)
    checkout_page.expect_ready_for_order()
    total = checkout_page.normalize_price(checkout_page.total_amount())
    assert total >= price, "Итоговая сумма меньше стоимости товара без доставки"
