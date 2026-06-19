from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from db.models import WbAccount


def main_kb(account_name: str | None = None) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📦 Товары"), KeyboardButton(text="📋 Заказы"))
    b.row(KeyboardButton(text="📊 Аналитика"), KeyboardButton(text="💰 Финансы"))
    b.row(KeyboardButton(text="🔑 Аккаунты"), KeyboardButton(text=f"🔄 {account_name}" if account_name else "🔄 Сменить аккаунт"))
    return b.as_markup(resize_keyboard=True)


def back_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def products_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📋 Список товаров"), KeyboardButton(text="📦 Остатки"))
    b.row(KeyboardButton(text="💰 Цены"), KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def orders_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📥 Новые заказы"), KeyboardButton(text="📤 Продажи"))
    b.row(KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def analytics_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📈 Воронка продаж"), KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def finances_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="📄 Отчёт по реализации"), KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def accounts_list_kb(accounts: list[WbAccount]) -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    for acc in accounts:
        label = acc.name[:32]
        b.row(KeyboardButton(text=f"🔑 {label}"))
    b.row(KeyboardButton(text="➕ Добавить аккаунт"))
    b.row(KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def account_actions_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="ℹ️ Информация"), KeyboardButton(text="🚫 Игнор-лист"))
    b.row(KeyboardButton(text="❌ Удалить аккаунт"), KeyboardButton(text="🔙 К списку"))
    return b.as_markup(resize_keyboard=True)


def ignore_list_kb() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text="➕ Добавить в игнор"))
    b.row(KeyboardButton(text="🔙 Назад"))
    return b.as_markup(resize_keyboard=True)


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
