"""Представители классов ошибок, зафиксированных при разведке zvet.ru."""

from dataclasses import dataclass
from typing import Literal

from core.data import generators

WRONG_CREDENTIALS_MESSAGE = "Не верный логин или пароль"


@dataclass(frozen=True, repr=False)
class NegativeCase:
    """Параметры формы и ожидаемое проявление ошибки."""

    email: str
    password: str
    phone: str | None = None
    error_field: Literal["email", "password", "phone"] | None = None
    accept_consent: bool = True
    server_rejection: bool = False


def build_cases() -> dict[str, NegativeCase]:
    email = generators.unknown_email()
    password = generators.password()
    return {
        "required-password": NegativeCase(email, "", error_field="password"),
        "email-format": NegativeCase("qa.user@example", password, error_field="email"),
        "missing-consent": NegativeCase(email, password, accept_consent=False),
        "phone-length": NegativeCase("", "", phone=generators.short_phone(), error_field="phone"),
        "invalid-credentials": NegativeCase(email, password, server_rejection=True),
    }
