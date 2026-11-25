# Page Objects и локаторы zvet.ru

Тесты вызывают методы страниц, а локаторы хранятся в `ui/pages/`. Проверяемые элементы выбираются по роли, тексту, имени поля или атрибуту `data-cy`. CSS используется, когда нужно ограничить поиск областью страницы или отличить одну цену от другой.

| Страница | Элемент | Локатор и назначение |
| --- | --- | --- |
| [Окно входа](../ui/pages/login_page.py) | Кнопка кабинета | Видимая `.header__middle-nav-btn--auth`. После входа проверяется ссылка на `/personal/`. |
| | Активная форма | `._overlay.open` → `._window-login`. Внутри выбирается панель `.auth-popup__login-content._email` или `.auth-popup__login-content._phone`. |
| | Вкладки входа | `get_by_role("button", name="По почте", exact=True)` и аналогично для «По номеру телефона». |
| | Почта, пароль и отправка | `[data-cy="email"]`, `[data-cy="password"]`, `[data-cy="loginBtnByEmail"]` внутри почтовой панели. |
| | Телефон и код с картинки | `input[name="phone"]` и `input[name="captcha_word"]` внутри телефонной панели. Появление `._window-code` подтверждает переход к SMS. |
| | Ошибка поля | Относительный XPath `..` находит обёртку поля. По её классу `error` проверяется клиентская валидация, а по `._error-msg` читается ответ сервера. |
| [Поиск](../ui/pages/search_page.py) | Поле поиска | Видимое `input[name="q"]`. Сайт меняет текст подсказки, поэтому используется имя поля. |
| | Результат поиска | `.product-card` с видимой `.product-card__btn--add`. Тест читает заголовок из `a.product-card__title`, цену из `.product-card__costs span`. |
| [Карточка товара](../ui/pages/product_page.py) | Название, цена, артикул | `get_by_role("heading", level=1)`, `.detail-price__item.current`, пункт списка характеристик с подписью «Артикул». |
| | Покупка | `.detail-buy__button.add_basket` и `.detail-buy__button.remove_basket` подтверждают состояния до и после добавления. |
| [Корзина](../ui/pages/cart_page.py) | Позиция и удаление | `.basket-item` с нужным артикулом в `.basket-item__code`. `.basket-item__delete` ищется внутри этой позиции, чтобы удалить именно тестовый товар. |
| | Цена и количество | `.basket-item__price:not(.basket-item__price--old)` и `.vue-counter__value` внутри строки. Итог берётся из `.cart-summary__sums-row` с подписью «Итоговая сумма к оплате». |
| [Оформление](../ui/pages/checkout_page.py) | Город, адрес и почта | Видимые `input[name="city"]` и `input[name="adress"]`, для почты `get_by_role("textbox", name="Электронная почта", exact=True)`. Точное имя исключает поле подписки внизу страницы. |
| | Согласие | Видимая метка `.cart-summary__checkboxes label.g-checkbox` с текстом «персональных данных» и диалог с ролью `dialog` «Персональные данные». |
| | Готовность заказа | `get_by_role("button", name="Оформить заказ", exact=True)`. Тест проверяет видимость и доступность кнопки. |

Например, в `LoginPage` поле почты однозначно находится внутри активного окна и выбранной панели. Метод `fill_email()` использует этот локатор, а тест вызывает сам метод.

```python
window = page.locator("._overlay.open").locator("._window-login")
panel = window.locator(".auth-popup__login-content._email")
email = panel.locator('[data-cy="email"]')
```
