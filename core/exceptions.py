"""Собственные исключения фреймворка."""

from __future__ import annotations


class AutotestError(Exception):
    """Базовая ошибка автотестов."""


class ElementNotFound(AutotestError):
    """Ожидаемый элемент не найден на странице."""


class LoginFailed(AutotestError):
    """Авторизация не удалась."""


class NegativeScenarioFailed(AutotestError):
    """Ожидаемая негативная реакция сайта не наступила."""


class ManualStepTimeout(AutotestError):
    """Ручной шаг (капча / SMS) не выполнен в отведённое время."""
