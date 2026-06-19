from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards import orders_kb
from bot.utils import filter_by_ignore_list, esc, send_rich, ensure_account, call_wb, chunk_message

router = Router()


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
    account = await ensure_account(message)
    if not account:
        return

    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    try:
        orders = await call_wb(account, "get_orders", date_from=date_from)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=orders_kb())
        return

    orders = filter_by_ignore_list(orders, account, code_keys=["vendorCode", "supplierArticle"])
    if not orders:
        await message.answer("📥 **Новые заказы**: нет данных.", reply_markup=orders_kb())
        return

    header = f"# 📥 Новые заказы ({len(orders)} шт.)\n| Артикул | Кол-во | Сумма | Статус |\n|:--------|:------:|------:|:-------|\n"
    rows = _build_rows(orders)
    parts = chunk_message(header, rows)
    for i, p in enumerate(parts):
        await send_rich(message, p, orders_kb() if i == len(parts) - 1 else None)


def _build_sales_rows(items: list[dict]) -> list[str]:
    rows = []
    for o in items:
        art = esc(o.get("supplierArticle", "—"))
        total = o.get("finishedPrice") or o.get("priceWithDisc") or o.get("totalPrice") or 0
        for_pay = o.get("forPay") or 0
        rows.append(f"| `{art}` | `{total:,.0f} ₽` | `{for_pay:,.0f} ₽` |\n")
    return rows


@router.message(F.text == "📤 Продажи")
async def orders_sales(message: Message) -> None:
    account = await ensure_account(message)
    if not account:
        return

    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    try:
        sales = await call_wb(account, "get_sales", date_from=date_from)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=orders_kb())
        return

    sales = filter_by_ignore_list(sales, account, code_keys=["vendorCode", "supplierArticle"])
    if not sales:
        await message.answer("📤 **Продажи**: нет данных.", reply_markup=orders_kb())
        return

    fbo = [s for s in sales if s.get("warehouseType") == "Склад WB"]
    fbs = [s for s in sales if s.get("warehouseType") == "Склад продавца"]

    fbo_total = sum(s.get("finishedPrice") or s.get("priceWithDisc") or s.get("totalPrice") or 0 for s in fbo)
    fbo_for_pay = sum(s.get("forPay") or 0 for s in fbo)
    fbs_total = sum(s.get("finishedPrice") or s.get("priceWithDisc") or s.get("totalPrice") or 0 for s in fbs)
    fbs_for_pay = sum(s.get("forPay") or 0 for s in fbs)

    parts = []

    if fbo:
        header = f"# 📦 Продажи FBO — Склад WB ({len(fbo)} шт.)\n\n| Сумма | К перечислению |\n|------:|---------------:|\n| `{fbo_total:,.0f} ₽` | `{fbo_for_pay:,.0f} ₽` |\n\n| Артикул | Цена | К перечислению |\n|:--------|-----:|---------------:|\n"
        rows = _build_sales_rows(fbo)
        parts.extend(chunk_message(header, rows))

    if fbs:
        header = f"# 📋 Продажи FBS — Склад продавца ({len(fbs)} шт.)\n\n| Сумма | К перечислению |\n|------:|---------------:|\n| `{fbs_total:,.0f} ₽` | `{fbs_for_pay:,.0f} ₽` |\n\n| Артикул | Цена | К перечислению |\n|:--------|-----:|---------------:|\n"
        rows = _build_sales_rows(fbs)
        parts.extend(chunk_message(header, rows))

    if not parts:
        await message.answer("📤 **Продажи**: нет данных.", reply_markup=orders_kb())
        return

    for i, p in enumerate(parts):
        await send_rich(message, p, orders_kb() if i == len(parts) - 1 else None)
