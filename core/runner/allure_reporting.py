"""Маскирование данных результата перед сохранением Allure JSON."""

from allure_commons import hookimpl

from core.logger import scrub


def _scrub_entry(entry) -> None:
    if entry.name:
        entry.name = scrub(entry.name)
    details = entry.statusDetails
    if details is not None:
        if details.message:
            details.message = scrub(details.message)
        if details.trace:
            details.trace = scrub(details.trace)
    for parameter in entry.parameters:
        parameter.value = scrub(parameter.value)
    for step in entry.steps:
        _scrub_entry(step)


class AllureRedaction:
    """Обработать результаты тестов и фикстур до записи на диск."""

    @hookimpl(tryfirst=True)
    def report_result(self, result) -> None:
        _scrub_entry(result)

    @hookimpl(tryfirst=True)
    def report_container(self, container) -> None:
        for fixture in (*container.befores, *container.afters):
            _scrub_entry(fixture)
