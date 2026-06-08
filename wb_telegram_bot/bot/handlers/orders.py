from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import orders_menu, back_button, add_account_button

router = Router()


def _fmt_orders(orders: list, title: str) -> str:
    if not orders:
        return f"📭 {title}: нет данных."

    text = f"{title} ({len(orders)} шт.)\n\n"
    for order in orders[:10]:
        nm_id = order.get("nmId", "—")
        art = order.get("vendorCode", "—")
        qty = order.get("quantity", 0)
        total = order.get("totalPrice", 0)
        status = order.get("wbStatus", "—")
        text += (
            f"• <b>Артикул:</b> {art} (nmID: {nm_id})\n"
            f"  Кол-во: {qty}, Сумма: {total / 100:,.2f} ₽\n"
            f"  Статус: {status}\n\n"
        )
    if len(orders) > 10:
        text += f"…и ещё {len(orders) - 10}.\n"
    return text


@router.callback_query(F.data == "menu_orders")
async def menu_orders(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📋 <b>Заказы</b>\n\nВыбери действие:",
        reply_markup=orders_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "orders_new")
async def orders_new(callback: CallbackQuery) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, callback.from_user.id)

    if not accounts:
        await callback.message.edit_text(
            "❌ Сначала добавь аккаунт WB.",
            reply_markup=add_account_button(),
        )
        await callback.answer()
        return

    account = accounts[0]
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            orders = await client.get_orders(date_from=date_from)
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    text = _fmt_orders(orders, "📥 <b>Новые заказы</b>")
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "orders_sales")
async def orders_sales(callback: CallbackQuery) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, callback.from_user.id)

    if not accounts:
        await callback.message.edit_text(
            "❌ Сначала добавь аккаунт WB.",
            reply_markup=add_account_button(),
        )
        await callback.answer()
        return

    account = accounts[0]
    date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            sales = await client.get_sales(date_from=date_from)
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    text = _fmt_orders(sales, "📤 <b>Продажи</b>")
    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
