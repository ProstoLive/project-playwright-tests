"""Конфигурация тестового прогона.

Все секреты и адреса читаются из `.env` (шаблон — `.env.example`),
в коде тестов нет ни одного хардкодного URL или пароля.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Корень проекта (project/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env", override=False)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Неизменяемый снимок окружения для одного прогона."""

    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", "").rstrip("/"))

    # --- тестовый аккаунт (заполняется в .env) -------------------------------
    email: str = field(repr=False, default_factory=lambda: os.getenv("TEST_EMAIL", ""))
    password: str = field(repr=False, default_factory=lambda: os.getenv("TEST_PASSWORD", ""))
    phone: str = field(repr=False, default_factory=lambda: os.getenv("TEST_PHONE", ""))

    # --- ручные шаги (капча / SMS) -------------------------------------------
    manual_tests: bool = field(default_factory=lambda: _env_bool("MANUAL_TESTS", False))
    manual_timeout: int = field(default_factory=lambda: _env_int("MANUAL_TIMEOUT", 180))

    # --- браузер --------------------------------------------------------------
    headless: bool = field(default_factory=lambda: _env_bool("HEADLESS", True))
    browser: str = field(default_factory=lambda: os.getenv("BROWSER", "chromium"))
    browser_slow_mo: int = field(default_factory=lambda: _env_int("BROWSER_SLOW_MO", 0))
    default_timeout: int = field(default_factory=lambda: _env_int("DEFAULT_TIMEOUT", 15000))
    navigation_timeout: int = field(default_factory=lambda: _env_int("NAVIGATION_TIMEOUT", 45000))
    viewport_width: int = field(default_factory=lambda: _env_int("VIEWPORT_WIDTH", 1440))
    viewport_height: int = field(default_factory=lambda: _env_int("VIEWPORT_HEIGHT", 900))

    # --- логирование ---------------------------------------------------------
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/test.log"))

    # --- тестовые данные -----------------------------------------------------
    search_query: str = field(default_factory=lambda: os.getenv("SEARCH_QUERY", "диван"))
    customer_name: str = field(repr=False, default_factory=lambda: os.getenv("CUSTOMER_NAME", "Тестовый Покупатель"))
    customer_phone: str = field(repr=False, default_factory=lambda: os.getenv("CUSTOMER_PHONE", ""))
    customer_city: str = field(repr=False, default_factory=lambda: os.getenv("CUSTOMER_CITY", "Москва"))
    customer_address: str = field(repr=False, default_factory=lambda: os.getenv("CUSTOMER_ADDRESS", "ул. Тверская, д. 1"))
    customer_email: str = field(repr=False, default_factory=lambda: os.getenv("CUSTOMER_EMAIL", ""))

    # --- пути артефактов -----------------------------------------------------
    reports_dir: str = field(default_factory=lambda: os.getenv("REPORTS_DIR", "reports"))

    @property
    def has_account(self) -> bool:
        """Есть ли заполненные креды существующего аккаунта."""
        return bool(self.email and self.password)

    def path(self, relative: str) -> Path:
        return PROJECT_ROOT / relative


settings = Settings()
