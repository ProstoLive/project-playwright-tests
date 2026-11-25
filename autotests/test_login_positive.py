"""Вход существующего покупателя на zvet.ru."""

import allure
import pytest

from core.config import settings
from ui.pages.login_page import LoginPage

pytestmark = [
    pytest.mark.auth,
    allure.epic("Цвет диванов"),
    allure.feature("Авторизация"),
]


@pytest.mark.smoke
@allure.story("Вход по почте")
def test_login_by_email(email_account: None, guest_login: LoginPage) -> None:
    """ТК-А02. Войти по почте и проверить, что после обновления сеанс сохранился."""
    guest_login.sign_in_by_email(settings.email, settings.password)
    guest_login.page.reload(wait_until="domcontentloaded")
    guest_login.wait_for_login()


@pytest.mark.manual
@allure.story("Вход по телефону")
def test_login_by_phone(phone_account: None, guest_login: LoginPage) -> None:
    """ТК-А11. Войти по привязанному номеру с ручным прохождением капчи и вводом SMS."""
    guest_login.open().switch_to_phone().fill_phone(settings.phone).accept_consent(by_phone=True)
    guest_login.wait_for_manual_captcha()
    guest_login.wait_for_manual_sms()
