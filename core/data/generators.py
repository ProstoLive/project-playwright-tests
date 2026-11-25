"""Синтетические данные для негативных сценариев."""

from faker import Faker

faker = Faker("ru_RU")


def unknown_email() -> str:
    """Уникальная синтетическая почта в зарезервированном домене."""
    return f"qa.{faker.uuid4()[:12]}@example.invalid"


def password(length: int = 12) -> str:
    """Пароль заданной длины без символов, требующих раскладки клавиатуры."""
    return faker.password(length=length, special_chars=False)


def short_phone() -> str:
    """Десять цифр вместе с кодом страны."""
    return f"+7{faker.random_int(900_000_000, 999_999_999):09d}"[:-1]
