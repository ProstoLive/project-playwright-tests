"""Консольный и файловый лог с общей функцией маскирования."""

from __future__ import annotations

import functools
import html
import json
import logging
import re
import sys
import time
from urllib.parse import quote, quote_plus

import allure

from core.config import settings

_SECRETS: set[str] = set()
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?7|8)[\s()-]*\d{3}[\s()-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)")
_TOKEN_PATTERN = re.compile(
    r"""(\bbearer\s+|\b[\w-]*(?:token|authorization|password|cookie)[\w-]*["']?\s*[:=]\s*["']?(?:bearer\s+)?)([^\s"'&,;]+)""",
    re.IGNORECASE,
)


def register_secret(value: str | None) -> None:
    """Запомнить значение и его URL-представления для фильтра отчётов."""
    if value and len(value) >= 3:
        _SECRETS.update((
            value, quote(value, safe=""), quote_plus(value),
            json.dumps(value, ensure_ascii=False)[1:-1], html.escape(value),
        ))


def scrub(text: str) -> str:
    """Скрыть известные секреты, телефоны, email и типовые поля токенов."""
    for secret in sorted(_SECRETS, key=len, reverse=True):
        text = text.replace(secret, "********")
    text = EMAIL_PATTERN.sub("***@***", text)
    text = PHONE_PATTERN.sub("***********", text)
    return _TOKEN_PATTERN.sub(r"\g<1>********", text)


class MaskedFormatter(logging.Formatter):
    """Маскировать итоговую строку вместе с аргументами и исключениями."""

    def format(self, record: logging.LogRecord) -> str:
        return scrub(super().format(record))


class ConsoleHandler(logging.StreamHandler):
    """Писать в активный stdout, включая захват вывода pytest."""

    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stdout
        super().emit(record)


def get_logger(name: str) -> logging.Logger:
    root = logging.getLogger("autotests")
    if not root.handlers:
        root.setLevel(settings.log_level)
        root.propagate = False
        for value in (settings.email, settings.phone, settings.password,
                      settings.customer_email, settings.customer_phone, settings.customer_address):
            register_secret(value)
        log_path = settings.path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        formatter = MaskedFormatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        for handler in (ConsoleHandler(), logging.FileHandler(log_path, encoding="utf-8")):
            handler.setFormatter(formatter)
            root.addHandler(handler)
    return logging.getLogger(f"autotests.{name}")


def log_step(description: str):
    """Записать название и длительность шага без его аргументов."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__.rsplit(".", 1)[-1])
            logger.info("Шаг: %s", description)
            started = time.monotonic()
            try:
                with allure.step(scrub(description)):
                    result = func(*args, **kwargs)
            except Exception:
                logger.error("Ошибка на шаге «%s»", description)
                raise
            logger.debug("Шаг «%s» завершён за %.2f с", description, time.monotonic() - started)
            return result

        return wrapper

    return decorator
