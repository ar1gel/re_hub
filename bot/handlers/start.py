from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from db.engine import get_session
from db.repository import get_or_create_user
from bot.keyboards import main_reply_kb, products_menu, orders_menu, analytics_menu, finances_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with get_session() as session:
        await get_or_create_user(
            session,
            tg_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

    await message.answer(
        f"👋 <b>Привет, {message.from_user.full_name or 'пользователь'}!</b>\n\n"
        "Я — бот для работы с API Wildberries.\n"
        "Здесь ты можешь управлять товарами, заказами, "
        "смотреть аналитику и финансы.\n\n"
        "Чтобы начать, добавь токен WB в разделе «Аккаунты WB».",
        reply_markup=main_reply_kb(),
    )


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел",
    )
    await callback.answer()


@router.callback_query(F.data == "menu_help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "❓ <b>Помощь</b>\n\n"
        "Этот бот позволяет работать с Wildberries API.\n\n"
        "<b>Доступные разделы:</b>\n"
        "📦 <b>Товары</b> — просмотр товаров, остатков, цен\n"
        "📋 <b>Заказы</b> — просмотр заказов и продаж\n"
        "📊 <b>Аналитика</b> — воронка продаж\n"
        "💰 <b>Финансы</b> — отчёты по реализации\n"
        "🔑 <b>Аккаунты WB</b> — управление токенами\n\n"
        "Для начала добавь токен WB API в разделе аккаунтов.\n"
        "Токен можно получить в личном кабинете WB: "
        "Настройки → Доступ к API",
    )
    await callback.answer()


@router.message(F.text == "📦 Товары")
async def reply_products(message: Message) -> None:
    await message.answer("📦 <b>Товары</b>\n\nВыбери действие:", reply_markup=products_menu())


@router.message(F.text == "📋 Заказы")
async def reply_orders(message: Message) -> None:
    await message.answer("📋 <b>Заказы</b>\n\nВыбери действие:", reply_markup=orders_menu())


@router.message(F.text == "📊 Аналитика")
async def reply_analytics(message: Message) -> None:
    await message.answer("📊 <b>Аналитика</b>\n\nВыбери действие:", reply_markup=analytics_menu())


@router.message(F.text == "💰 Финансы")
async def reply_finances(message: Message) -> None:
    await message.answer("💰 <b>Финансы</b>\n\nВыбери действие:", reply_markup=finances_menu())


@router.message(F.text == "🔑 Аккаунты")
async def reply_accounts(message: Message) -> None:
    from bot.handlers.accounts import _show_accounts
    await _show_accounts(message.from_user.id, message)


@router.message(F.text == "❓ Помощь")
async def reply_help(message: Message) -> None:
    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "Этот бот позволяет работать с Wildberries API.\n\n"
        "<b>Доступные разделы:</b>\n"
        "📦 <b>Товары</b> — просмотр товаров, остатков, цен\n"
        "📋 <b>Заказы</b> — просмотр заказов и продаж\n"
        "📊 <b>Аналитика</b> — воронка продаж\n"
        "💰 <b>Финансы</b> — отчёты по реализации\n"
        "🔑 <b>Аккаунты WB</b> — управление токенами\n\n"
        "Для начала добавь токен WB API в разделе аккаунтов.\n"
        "Токен можно получить в личном кабинете WB: "
        "Настройки → Доступ к API",
        reply_markup=main_menu(),
    )
