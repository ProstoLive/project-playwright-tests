"""Отдельный сценарий для показа диагностики на защите."""

import allure
import pytest

from core.data import generators
from core.logger import get_logger, scrub
from ui.pages.login_page import LoginPage


@allure.epic("Цвет диванов")
@allure.feature("Диагностика автотестов")
@allure.title("Демонстрационное падение после заполнения формы входа")
def test_report_demo(guest_login: LoginPage) -> None:
    """Заполнить форму синтетическими данными и показать вложения при падении."""
    email = generators.unknown_email()
    password = generators.password()
    guest_login.open().switch_to_email().fill_email(email).fill_password(password)
    get_logger("demo").info("Маскирование: email=%s, пароль=%s", scrub(email), scrub(password))
    pytest.fail("Контрольное падение для демонстрации скриншота", pytrace=False)
