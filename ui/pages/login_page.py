"""Page Object окна входа на zvet.ru."""

import re

from playwright.sync_api import Locator, expect

from core.config import settings
from core.logger import log_step
from ui.base_page import BasePage


class LoginPage(BasePage):
    """Вход по почте и телефону в активном окне авторизации."""

    AUTH_TRIGGER = ".header__middle-nav-btn--auth"
    GUEST_ACTION = r"authPopup\.show"
    OVERLAY = "._overlay.open"
    EMAIL_PANEL = ".auth-popup__login-content._email"
    PHONE_PANEL = ".auth-popup__login-content._phone"
    EMAIL_INPUT = '[data-cy="email"]'
    PASSWORD_INPUT = '[data-cy="password"]'
    PHONE_INPUT = 'input[name="phone"]'
    CODE_WINDOW = "._window-code"

    @property
    def account_control(self) -> Locator:
        return self.page.locator(self.AUTH_TRIGGER).filter(visible=True)

    @property
    def login_window(self) -> Locator:
        return self.page.locator(self.OVERLAY).locator("._window-login")

    def _panel(self, *, by_phone: bool = False) -> Locator:
        return self.login_window.locator(self.PHONE_PANEL if by_phone else self.EMAIL_PANEL)

    def _field(self, name: str) -> Locator:
        selector = {"email": self.EMAIL_INPUT, "password": self.PASSWORD_INPUT, "phone": self.PHONE_INPUT}
        return self._panel(by_phone=name == "phone").locator(selector[name])

    def _submit_button(self, *, by_phone: bool = False) -> Locator:
        if by_phone:
            return self._panel(by_phone=True).locator("button._formSubmit")
        return self._panel().locator('[data-cy="loginBtnByEmail"]')

    @log_step("Открыть окно входа")
    def open(self) -> "LoginPage":
        self._click(self.account_control, "личный кабинет в шапке")
        self._expect_visible(self.login_window, "форма входа")
        return self

    @log_step("Выбрать вход по почте")
    def switch_to_email(self) -> "LoginPage":
        self._click(self.login_window.get_by_role("button", name="По почте", exact=True), "вкладка почты")
        self._expect_visible(self._panel(), "форма входа по почте")
        return self

    @log_step("Выбрать вход по телефону")
    def switch_to_phone(self) -> "LoginPage":
        panel = self._panel(by_phone=True)
        if not panel.is_visible():
            button = self.login_window.get_by_role("button", name="По номеру телефона", exact=True)
            self._click(button, "вкладка телефона")
        self._expect_visible(panel, "форма входа по телефону")
        return self

    @log_step("Ввести e-mail")
    def fill_email(self, email: str) -> "LoginPage":
        self._fill(self._field("email"), email, "e-mail", sensitive=True)
        return self

    @log_step("Ввести пароль")
    def fill_password(self, password: str) -> "LoginPage":
        self._fill(self._field("password"), password, "пароль", sensitive=True)
        return self

    @log_step("Ввести номер телефона")
    def fill_phone(self, phone: str, *, allow_incomplete: bool = False) -> "LoginPage":
        self._fill_phone(self._field("phone"), phone, allow_incomplete=allow_incomplete)
        return self

    @log_step("Отметить согласие на обработку персональных данных")
    def accept_consent(self, *, by_phone: bool = False) -> "LoginPage":
        panel = self._panel(by_phone=by_phone)
        checkbox_selector = 'input[name="confirm"]'
        checkbox = panel.locator(checkbox_selector)
        if not checkbox.is_checked():
            self.accept_policy(panel.locator("label").filter(has=self.page.locator(checkbox_selector)).locator(".g-checkbox__box"))
        expect(checkbox, "Согласие на обработку данных должно быть отмечено").to_be_checked()
        return self

    @log_step("Нажать «Войти»")
    def submit(self) -> "LoginPage":
        self._click(self._submit_button(), "кнопка входа по почте")
        return self

    def expect_field_error(self, field: str, *, present: bool = True) -> None:
        """Перевести фокус и проверить состояние обёртки конкретного поля."""
        locator = self._field(field)
        locator.focus()
        locator.blur()
        wrapper = locator.locator("xpath=..")
        assertion = expect(wrapper, f"Неожиданное состояние валидации поля «{field}»")
        if present:
            assertion.to_have_class(re.compile(r"\berror\b"))
        else:
            assertion.not_to_have_class(re.compile(r"\berror\b"))

    def expect_submit_blocked(self, *, by_phone: bool = False) -> None:
        expect(self._submit_button(by_phone=by_phone), "Кнопка «Войти» должна быть заблокирована").to_be_disabled()

    def expect_credentials_error(self, message: str) -> None:
        for field in ("email", "password"):
            alert = self._field(field).locator("xpath=..").locator("._error-msg")
            expect(alert, f"Под полем «{field}» отсутствует сообщение об отказе").to_have_text(message)
            expect(alert).to_be_visible()

    def expect_guest(self) -> None:
        expect(self.account_control, "В шапке должна остаться кнопка гостевого входа").to_have_attribute(
            "onclick", re.compile(self.GUEST_ACTION)
        )

    @property
    def signed_in_control(self) -> Locator:
        return self.page.locator(f'a{self.AUTH_TRIGGER}[href*="/personal/"]:not([onclick*="authPopup.show"])').filter(visible=True)

    @log_step("Дождаться успешного входа")
    def wait_for_login(self, *, timeout: int = settings.navigation_timeout) -> None:
        expect(self.signed_in_control, "После входа должна появиться ссылка на личный кабинет").to_be_visible(
            timeout=timeout
        )
        expect(self.page.locator(self.OVERLAY)).to_be_hidden()

    @log_step("Войти по почте")
    def sign_in_by_email(self, email: str, password: str) -> None:
        self.open().switch_to_email().fill_email(email).fill_password(password).accept_consent().submit()
        self.wait_for_login()

    @log_step("Выйти из личного кабинета")
    def logout(self) -> None:
        if self.page.is_closed():
            return
        if not self.account_control.is_visible():
            self.open_home()
        if self.signed_in_control.is_visible():
            # Штатный обработчик сайта, зафиксированный при разведке.
            self.page.wait_for_function(
                "() => typeof o2v2 !== 'undefined' && typeof o2v2.authPopup?.logout === 'function'"
            )
            self.page.evaluate("() => o2v2.authPopup.logout()")
            self.expect_guest()

    def wait_for_manual_captcha(self) -> None:
        """Дождаться прохождения капчи человеком в браузере."""
        self._expect_visible(self._panel(by_phone=True).locator('input[name="captcha_word"]'), "поле капчи")
        self.log.warning("Введите ответ на капчу в браузере и нажмите «Войти»")
        expect(self.page.locator(self.CODE_WINDOW).filter(visible=True), "Не открылась форма SMS").to_be_visible(
            timeout=settings.manual_timeout * 1000
        )

    def wait_for_manual_sms(self) -> None:
        """Дождаться входа после автоматической отправки кода сайтом."""
        self.log.warning("Введите SMS-код в браузере. Сайт подтвердит его автоматически")
        self.wait_for_login(timeout=settings.manual_timeout * 1000)
