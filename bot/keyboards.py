from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"account_delete:{account_id}"),
    )
    builder.row(InlineKeyboardButton(text="🔙 К списку", callback_data="menu_accounts"))
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
