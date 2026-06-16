from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import orders_kb, main_kb
from bot.utils import filter_by_ignore_list, esc, send_rich
from bot.menu import set_menu

router = Router()

LIMIT = 32000


def _build_rows(items: list[dict]) -> list[str]:
    rows = []
    for o in items:
        art = esc(o.get("vendorCode") or o.get("supplierArticle", "—"))
        qty = o.get("quantity", 0)
        total = o.get("totalPrice") or 0
        status = esc(o.get("wbStatus", "—"))
        rows.append(f"| `{art}` | {qty} | `{total:,.2f} ₽` | {status} |\n")
    return rows


@router.message(F.text == "📥 Новые заказы")
async def orders_new(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)
    if not accounts:
        await message.answer("❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.", reply_markup=main_kb())
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
    if not orders:
        await message.answer("📥 **Новые заказы**: нет данных.", reply_markup=orders_kb())
        return

    header = f"# 📥 Новые заказы ({len(orders)} шт.)\n| Артикул | Кол-во | Сумма | Статус |\n|:--------|:------:|------:|:-------|\n"
    rows = _build_rows(orders)
    chunk = header
    parts = []
    for r in rows:
        if len(chunk) + len(r) > LIMIT:
            parts.append(chunk)
            chunk = r
        else:
            chunk += r
    parts.append(chunk)
    for i, p in enumerate(parts):
        await send_rich(message, p, orders_kb() if i == len(parts) - 1 else None)


@router.message(F.text == "📤 Продажи")
async def orders_sales(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)
    if not accounts:
        await message.answer("❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.", reply_markup=main_kb())
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
    if not sales:
        await message.answer("📤 **Продажи**: нет данных.", reply_markup=orders_kb())
        return

    header = f"# 📤 Продажи ({len(sales)} шт.)\n| Артикул | Кол-во | Сумма | Статус |\n|:--------|:------:|------:|:-------|\n"
    rows = _build_rows(sales)
    chunk = header
    parts = []
    for r in rows:
        if len(chunk) + len(r) > LIMIT:
            parts.append(chunk)
            chunk = r
        else:
            chunk += r
    parts.append(chunk)
    for i, p in enumerate(parts):
        await send_rich(message, p, orders_kb() if i == len(parts) - 1 else None)
