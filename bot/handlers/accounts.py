from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from db.engine import get_session
from db.repository import get_or_create_user, get_accounts, get_account_by_id, add_account, delete_account, get_ignore_list, add_to_ignore, remove_from_ignore
from bot.keyboards import accounts_list_kb, account_actions_kb, ignore_list_kb, main_kb, back_kb, remove_kb
from bot.menu import set_menu, get_menu, set_account, get_account
from bot.wb_client import WbClient

router = Router()


class AccountAdd(StatesGroup):
    name = State()
    token = State()


class IgnoreAdd(StatesGroup):
    vendor_code = State()


async def show_accounts_list(tg_id: int, target: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, tg_id)

    if not accounts:
        await target.answer(
            "🔑 <b>Аккаунты WB</b>\n\n"
            "У тебя пока нет добавленных аккаунтов.\n"
            "Нажми «Добавить аккаунт», чтобы добавить токен WB API.",
            reply_markup=accounts_list_kb([]),
        )
    else:
        text = "🔑 <b>Твои аккаунты WB:</b>\n\n"
        for i, acc in enumerate(accounts, 1):
            text += f"{i}. <b>{acc.name}</b>\n"
        await target.answer(text, reply_markup=accounts_list_kb(accounts))
    set_menu(tg_id, "accounts")


def _account_from_text(text: str, accounts: list) -> tuple[int, object] | None:
    for acc in accounts:
        if text == f"🔑 {acc.name}":
            return acc.id, acc
    return None


@router.message(F.text.startswith("🔑 "))
async def account_select_by_name(message: Message) -> None:
    if get_menu(message.from_user.id) != "accounts":
        return

    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)

    result = _account_from_text(message.text, accounts)
    if result is None:
        return

    account_id, account = result
    set_account(message.from_user.id, account_id)
    await message.answer(
        f"🔑 <b>Аккаунт: {account.name}</b>\n\n"
        f"ID: {account.id}\n"
        f"Токен: {account.token[:8]}...{account.token[-4:]}",
        reply_markup=account_actions_kb(),
    )
    set_menu(message.from_user.id, "account_actions")


@router.message(F.text == "🔙 К списку")
async def back_to_accounts_list(message: Message) -> None:
    await show_accounts_list(message.from_user.id, message)


@router.message(F.text == "ℹ️ Информация")
async def account_info(message: Message) -> None:
    account_id = get_account(message.from_user.id)
    if account_id is None:
        await message.answer("❌ Сначала выбери аккаунт.", reply_markup=main_kb())
        set_menu(message.from_user.id, "main")
        return

    async with get_session() as session:
        account = await get_account_by_id(session, account_id, message.from_user.id)

    if account is None:
        await message.answer("❌ Аккаунт не найден.", reply_markup=main_kb())
        set_menu(message.from_user.id, "main")
        return

    async with WbClient(account.token) as client:
        try:
            info = await client.get_seller_info()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=account_actions_kb())
            return

    text = (
        f"ℹ️ <b>Информация об аккаунте</b>\n\n"
        f"Название: {account.name}\n"
        f"Продавец: {info.get('name', '—')}\n"
        f"Торговая марка: {info.get('tradeMark', '—')}\n"
        f"ИНН: {info.get('tin', '—')}\n"
        f"SID: {info.get('sid', '—')}"
    )
    await message.answer(text, reply_markup=account_actions_kb())


@router.message(F.text == "❌ Удалить аккаунт")
async def account_delete_confirm(message: Message) -> None:
    account_id = get_account(message.from_user.id)
    if account_id is None:
        await message.answer("❌ Сначала выбери аккаунт.", reply_markup=main_kb())
        set_menu(message.from_user.id, "main")
        return

    async with get_session() as session:
        deleted = await delete_account(session, account_id, message.from_user.id)

    if deleted:
        await message.answer("✅ Аккаунт удалён.", reply_markup=back_kb())
    else:
        await message.answer("❌ Аккаунт не найден.", reply_markup=back_kb())


@router.message(F.text == "🚫 Игнор-лист")
async def account_ignore_list(message: Message) -> None:
    account_id = get_account(message.from_user.id)
    if account_id is None:
        await message.answer("❌ Сначала выбери аккаунт.", reply_markup=main_kb())
        set_menu(message.from_user.id, "main")
        return

    async with get_session() as session:
        account = await get_account_by_id(session, account_id, message.from_user.id)

    if account is None:
        await message.answer("❌ Аккаунт не найден.", reply_markup=main_kb())
        set_menu(message.from_user.id, "main")
        return

    items = get_ignore_list(account)
    if items:
        text = (
            f"🚫 <b>Игнор-лист: {account.name}</b>\n\n"
            "Эти артикулы не показываются:\n"
        )
        for vc in items[:15]:
            text += f"• {vc}\n"
        if len(items) > 15:
            text += f"…и ещё {len(items) - 15}\n"
        text += "\nЧтобы удалить артикул, отправь ❌ vendorCode"
    else:
        text = f"🚫 <b>Игнор-лист: {account.name}</b>\n\nИгнор-лист пуст."

    await message.answer(text, reply_markup=ignore_list_kb())
    set_menu(message.from_user.id, "ignore_list")


@router.message(F.text == "➕ Добавить в игнор")
async def ignore_add_start(message: Message, state: FSMContext) -> None:
    await message.answer(
        "✏️ Введи vendorCode (артикул продавца), который нужно скрыть:",
        reply_markup=remove_kb(),
    )
    await state.set_state(IgnoreAdd.vendor_code)


@router.message(StateFilter(IgnoreAdd.vendor_code))
async def ignore_add_vendor(message: Message, state: FSMContext) -> None:
    vc = message.text.strip()
    if not vc:
        await message.answer("❌ Артикул не может быть пустым. Попробуй снова:")
        return

    account_id = get_account(message.from_user.id)
    if account_id is None:
        await state.clear()
        await message.answer("❌ Аккаунт не выбран.", reply_markup=main_kb())
        set_menu(message.from_user.id, "main")
        return

    async with get_session() as session:
        account = await get_account_by_id(session, account_id, message.from_user.id)
        if account:
            await add_to_ignore(session, account, vc)

    await state.clear()
    await message.answer(
        f"✅ Артикул <b>{vc}</b> добавлен в игнор-лист.",
        reply_markup=ignore_list_kb(),
    )
    set_menu(message.from_user.id, "ignore_list")


@router.message(F.text.startswith("❌ "))
async def ignore_del_vendor(message: Message) -> None:
    if get_menu(message.from_user.id) != "ignore_list":
        return

    vc = message.text[2:].strip()
    if not vc:
        return

    account_id = get_account(message.from_user.id)
    if account_id is None:
        return

    async with get_session() as session:
        account = await get_account_by_id(session, account_id, message.from_user.id)
        if account:
            await remove_from_ignore(session, account, vc)

    await message.answer(f"✅ Артикул <b>{vc}</b> удалён из игнор-листа.", reply_markup=ignore_list_kb())


@router.message(F.text == "➕ Добавить аккаунт")
async def account_add_start(message: Message, state: FSMContext) -> None:
    await message.answer(
        "✏️ <b>Добавление аккаунта WB</b>\n\n"
        "Введи название для аккаунта (например, «Мой магазин»):",
        reply_markup=remove_kb(),
    )
    await state.set_state(AccountAdd.name)


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
        reply_markup=remove_kb(),
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
            reply_markup=remove_kb(),
        )
        return

    async with get_session() as session:
        await get_or_create_user(session, tg_id=message.from_user.id, username=message.from_user.username, full_name=message.from_user.full_name)
        account = await add_account(session, message.from_user.id, name, token)

    await state.clear()
    await show_accounts_list(message.from_user.id, message)
