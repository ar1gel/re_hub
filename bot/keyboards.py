from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 Товары", callback_data="menu_products"),
        InlineKeyboardButton(text="📋 Заказы", callback_data="menu_orders"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Аналитика", callback_data="menu_analytics"),
        InlineKeyboardButton(text="💰 Финансы", callback_data="menu_finances"),
    )
    builder.row(
        InlineKeyboardButton(text="🔑 Аккаунты WB", callback_data="menu_accounts"),
        InlineKeyboardButton(text="❓ Помощь", callback_data="menu_help"),
    )
    return builder.as_markup()


def accounts_menu(accounts: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for acc in accounts:
        builder.row(
            InlineKeyboardButton(text=f"{acc.name}", callback_data=f"account_select:{acc.id}")
        )
    builder.row(
        InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="account_add"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_main"),
    )
    return builder.as_markup()


def account_actions(account_id: int, account_name: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="ℹ️ Информация", callback_data=f"account_info:{account_id}"),
        InlineKeyboardButton(text="🚫 Игнор-лист", callback_data=f"account_ignore:{account_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"account_delete:{account_id}"),
    )
    builder.row(InlineKeyboardButton(text="🔙 К списку", callback_data="menu_accounts"))
    return builder.as_markup()


def ignore_list_menu(account_id: int, items: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for vc in items[:10]:
        builder.row(InlineKeyboardButton(text=f"❌ {vc}", callback_data=f"ignore_del:{account_id}:{vc}"))
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data=f"ignore_add:{account_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"account_select:{account_id}"),
    )
    return builder.as_markup()


def products_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список товаров", callback_data="products_list"),
        InlineKeyboardButton(text="📦 Остатки", callback_data="products_stocks"),
    )
    builder.row(
        InlineKeyboardButton(text="💰 Цены", callback_data="products_prices"),
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_main"),
    )
    return builder.as_markup()


def orders_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📥 Новые заказы", callback_data="orders_new"),
        InlineKeyboardButton(text="📤 Продажи", callback_data="orders_sales"),
    )
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_main"))
    return builder.as_markup()


def analytics_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Воронка продаж", callback_data="analytics_funnel"),
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_main"),
    )
    return builder.as_markup()


def finances_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 Отчёт по реализации", callback_data="finances_report"),
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_main"),
    )
    return builder.as_markup()


def back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_main"))
    return builder.as_markup()


def cancel_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def add_account_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔑 Добавить аккаунт", callback_data="account_add"))
    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_main"))
    return builder.as_markup()


def main_reply_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📦 Товары"),
        KeyboardButton(text="📋 Заказы"),
    )
    builder.row(
        KeyboardButton(text="📊 Аналитика"),
        KeyboardButton(text="💰 Финансы"),
    )
    builder.row(
        KeyboardButton(text="🔑 Аккаунты"),
        KeyboardButton(text="❓ Помощь"),
    )
    return builder.as_markup(resize_keyboard=True)
