from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_or_create_user, get_accounts
from bot.keyboards import main_kb, products_kb, orders_kb, analytics_kb, finances_kb
from bot.menu import set_menu, get_account, set_account
from bot.utils import esc

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
        accounts = await get_accounts(session, message.from_user.id)
    if accounts and get_account(message.from_user.id) is None:
        set_account(message.from_user.id, accounts[0].id)
    await message.answer(
        f"👋 <b>Привет, {message.from_user.full_name or 'пользователь'}!</b>\n\n"
        "Я — бот для работы с API Wildberries.\n"
        "Здесь ты можешь управлять товарами, заказами, "
        "смотреть аналитику и финансы.\n\n"
        "Чтобы начать, добавь токен WB в разделе «Аккаунты WB».",
        reply_markup=main_kb(),
    )
    set_menu(message.from_user.id, "main")


@router.message(F.text == "🔙 Назад")
async def back_main(message: Message) -> None:
    await message.answer("🏠 <b>Главное меню</b>\n\nВыбери раздел", reply_markup=main_kb())
    set_menu(message.from_user.id, "main")


@router.message(F.text == "📦 Товары")
async def reply_products(message: Message) -> None:
    await message.answer("📦 <b>Товары</b>\n\nВыбери действие:", reply_markup=products_kb())
    set_menu(message.from_user.id, "products")


@router.message(F.text == "📋 Заказы")
async def reply_orders(message: Message) -> None:
    await message.answer("📋 <b>Заказы</b>\n\nВыбери действие:", reply_markup=orders_kb())
    set_menu(message.from_user.id, "orders")


@router.message(F.text == "📊 Аналитика")
async def reply_analytics(message: Message) -> None:
    await message.answer("📊 <b>Аналитика</b>\n\nВыбери действие:", reply_markup=analytics_kb())
    set_menu(message.from_user.id, "analytics")


@router.message(F.text == "💰 Финансы")
async def reply_finances(message: Message) -> None:
    await message.answer("💰 <b>Финансы</b>\n\nВыбери действие:", reply_markup=finances_kb())
    set_menu(message.from_user.id, "finances")


@router.message(F.text == "🔑 Аккаунты")
async def reply_accounts(message: Message) -> None:
    from bot.handlers.accounts import show_accounts_list
    await show_accounts_list(message.from_user.id, message)


@router.message(F.text == "🔄 Сменить аккаунт")
async def reply_switch_account(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)
    if not accounts:
        await message.answer("❌ У тебя нет добавленных аккаунтов.\n\nНажми «Аккаунты», чтобы добавить.", reply_markup=main_kb())
        return
    if len(accounts) == 1:
        await message.answer(f"ℹ️ У тебя только один аккаунт: {esc(accounts[0].name)}", reply_markup=main_kb())
        return

    current_id = get_account(message.from_user.id)
    current_idx = 0
    for i, acc in enumerate(accounts):
        if acc.id == current_id:
            current_idx = i
            break
    next_idx = (current_idx + 1) % len(accounts)
    next_acc = accounts[next_idx]
    set_account(message.from_user.id, next_acc.id)
    await message.answer(f"✅ Аккаунт: <b>{esc(next_acc.name)}</b>", reply_markup=main_kb())
