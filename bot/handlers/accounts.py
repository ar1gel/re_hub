from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from db.engine import get_session
from db.repository import get_or_create_user, get_accounts, get_account_by_id, add_account, delete_account
from bot.keyboards import accounts_menu, account_actions, cancel_button, main_menu, back_button
from bot.wb_client import WbClient

router = Router()


class AccountAdd(StatesGroup):
    name = State()
    token = State()


@router.callback_query(F.data == "menu_accounts")
async def menu_accounts(callback: CallbackQuery) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, callback.from_user.id)

    if not accounts:
        await callback.message.edit_text(
            "🔑 <b>Аккаунты WB</b>\n\n"
            "У тебя пока нет добавленных аккаунтов.\n"
            "Нажми «Добавить аккаунт», чтобы добавить токен WB API.",
            reply_markup=accounts_menu([]),
        )
    else:
        text = "🔑 <b>Твои аккаунты WB:</b>\n\n"
        for i, acc in enumerate(accounts, 1):
            text += f"{i}. <b>{acc.name}</b> (id: {acc.id})\n"
        await callback.message.edit_text(text, reply_markup=accounts_menu(accounts))
    await callback.answer()


@router.callback_query(F.data == "account_add")
async def account_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(
        "✏️ <b>Добавление аккаунта WB</b>\n\n"
        "Введи название для аккаунта (например, «Мой магазин»):",
        reply_markup=cancel_button(),
    )
    await state.set_state(AccountAdd.name)
    await callback.answer()


@router.message(StateFilter(AccountAdd.name))
async def account_add_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if len(name) > 128:
        await message.answer("❌ Название слишком длинное (максимум 128 символов). Попробуй снова:")
        return
    await state.update_data(name=name)
    await state.set_state(AccountAdd.token)
    await message.answer(
        "🔑 Теперь отправь токен WB API.\n\n"
        "Токен можно получить в личном кабинете WB:\n"
        "Настройки → Доступ к API",
        reply_markup=cancel_button(),
    )


@router.message(StateFilter(AccountAdd.token))
async def account_add_token(message: Message, state: FSMContext) -> None:
    token = message.text.strip()
    data = await state.get_data()
    name = data["name"]

    async with WbClient(token) as client:
        ok = await client.ping()

    if not ok:
        await message.answer(
            "❌ Не удалось подключиться к WB API с этим токеном.\n"
            "Проверь правильность токена и попробуй снова.",
            reply_markup=cancel_button(),
        )
        return

    async with get_session() as session:
        await get_or_create_user(session, tg_id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name)
        account = await add_account(session, message.from_user.id, name, token)

    await state.clear()
    await message.answer(
        f"✅ <b>Аккаунт «{account.name}» успешно добавлен!</b>",
        reply_markup=main_menu(),
    )


@router.callback_query(F.data.startswith("account_select:"))
async def account_select(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        account = await get_account_by_id(session, account_id, callback.from_user.id)

    if account is None:
        await callback.message.edit_text(
            "❌ Аккаунт не найден.",
            reply_markup=back_button(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🔑 <b>Аккаунт: {account.name}</b>\n\n"
        f"ID: {account.id}\n"
        f"Токен: {account.token[:8]}...{account.token[-4:]}",
        reply_markup=account_actions(account.id, account.name),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("account_info:"))
async def account_info(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        account = await get_account_by_id(session, account_id, callback.from_user.id)

    if account is None:
        await callback.message.edit_text(
            "❌ Аккаунт не найден.",
            reply_markup=back_button(),
        )
        await callback.answer()
        return

    async with WbClient(account.token) as client:
        try:
            info = await client.get_seller_info()
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка при получении информации: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    text = (
        f"ℹ️ <b>Информация об аккаунте</b>\n\n"
        f"Название: {account.name}\n"
        f"Продавец: {info.get('name', '—')}\n"
        f"Торговая марка: {info.get('tradeMark', '—')}\n"
        f"ИНН: {info.get('tin', '—')}\n"
        f"SID: {info.get('sid', '—')}"
    )
    await callback.message.edit_text(text, reply_markup=account_actions(account.id, account.name))
    await callback.answer()


@router.callback_query(F.data.startswith("account_delete:"))
async def account_delete_confirm(callback: CallbackQuery) -> None:
    account_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        deleted = await delete_account(session, account_id, callback.from_user.id)

    if deleted:
        await callback.message.edit_text(
            "✅ Аккаунт удалён.",
            reply_markup=back_button(),
        )
    else:
        await callback.message.edit_text(
            "❌ Аккаунт не найден.",
            reply_markup=back_button(),
        )

    await callback.answer()
