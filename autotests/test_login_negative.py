"""Валидация формы и отказ при неверной паре (ТК-А04, А05, А06, А09)."""

import allure
import pytest

from core.data.negative_cases import WRONG_CREDENTIALS_MESSAGE, build_cases
from ui.pages.login_page import LoginPage

pytestmark = [
    pytest.mark.auth,
    pytest.mark.negative,
    allure.epic("Цвет диванов"),
    allure.feature("Авторизация"),
    allure.story("Ошибки входа"),
]
CASES = build_cases()


@pytest.mark.parametrize("case_id", list(CASES))
def test_login_negative(case_id: str, guest_login: LoginPage) -> None:
    """Проверить реакцию формы и сохранение гостевого состояния."""
    case = CASES[case_id]
    login = guest_login.open()
    by_phone = case.phone is not None
    if by_phone:
        login.switch_to_phone().fill_phone(case.phone, allow_incomplete=True)
        # Капча остаётся пустой. Отличительный сигнал — ошибка поля телефона.
    else:
        login.switch_to_email().fill_email(case.email).fill_password(case.password)
        if case.accept_consent:
            login.accept_consent()

    if case.server_rejection:
        login.submit()
        login.expect_credentials_error(WRONG_CREDENTIALS_MESSAGE)
    else:
        if case.error_field:
            login.expect_field_error(case.error_field)
        else:
            login.expect_field_error("email", present=False)
            login.expect_field_error("password", present=False)
        login.expect_submit_blocked(by_phone=by_phone)

    login.expect_guest()
