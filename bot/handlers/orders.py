from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import orders_kb, main_kb
from bot.utils import filter_by_ignore_list, esc
from bot.menu import set_menu

router = Router()


def _build_items(orders: list) -> tuple[str, list[str]]:
    if not orders:
        return "", []
    items = []
    for order in orders:
        art = esc(order.get("vendorCode") or order.get("supplierArticle", "—"))
        qty = order.get("quantity", 0)
        total = order.get("totalPrice") or 0
        status = esc(order.get("wbStatus", "—"))
        items.append(
            f"<b>Артикул:</b> <code>{art}</code>\n"
            f"Кол-во: <code>{qty}</code>, Сумма: <code>{total:,.2f} ₽</code>\n"
            f"Статус: {status}\n\n"
        )
    return items


@router.message(F.text == "📥 Новые заказы")
async def orders_new(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)

    if not accounts:
        await message.answer(
            "❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.",
            reply_markup=main_kb(),
        )
        set_menu(message.from_user.id, "main")
        return

    account = accounts[0]
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            orders = await client.get_orders(date_from=date_from)
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=orders_kb())
            return

    orders = filter_by_ignore_list(orders, account, code_keys=["vendorCode", "supplierArticle"])
    items = _build_items(orders)
    if not items:
        await message.answer("📥 <b>Новые заказы</b>: нет данных.", reply_markup=orders_kb())
        return
    header = f"📥 <b>Новые заказы</b> ({len(orders)} шт.)"
    chunk = header + "\n\n"
    chunks = []
    for item in items:
        if len(chunk) + len(item) > 4096:
            chunks.append(chunk)
            chunk = item
        else:
            chunk += item
    chunks.append(chunk)
    for i, part in enumerate(chunks):
        kb = orders_kb() if i == len(chunks) - 1 else None
        await message.answer(part, reply_markup=kb)


@router.message(F.text == "📤 Продажи")
async def orders_sales(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)

    if not accounts:
        await message.answer(
            "❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.",
            reply_markup=main_kb(),
        )
        set_menu(message.from_user.id, "main")
        return

    account = accounts[0]
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            sales = await client.get_sales(date_from=date_from)
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=orders_kb())
            return

    sales = filter_by_ignore_list(sales, account, code_keys=["vendorCode", "supplierArticle"])
    items = _build_items(sales)
    if not items:
        await message.answer("📤 <b>Продажи</b>: нет данных.", reply_markup=orders_kb())
        return
    header = f"📤 <b>Продажи</b> ({len(sales)} шт.)"
    chunk = header + "\n\n"
    chunks = []
    for item in items:
        if len(chunk) + len(item) > 4096:
            chunks.append(chunk)
            chunk = item
        else:
            chunk += item
    chunks.append(chunk)
    for i, part in enumerate(chunks):
        kb = orders_kb() if i == len(chunks) - 1 else None
        await message.answer(part, reply_markup=kb)
