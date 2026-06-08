from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import finances_menu, back_button, add_account_button

router = Router()


def _fmt_currency(kopecks: int) -> str:
    return f"{kopecks / 100:,.2f} ₽"


@router.callback_query(F.data == "menu_finances")
async def menu_finances(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "💰 <b>Финансы</b>\n\nВыбери действие:",
        reply_markup=finances_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "finances_report")
async def finances_report(callback: CallbackQuery) -> None:
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
    today = datetime.now()
    date_to = today.strftime("%Y-%m-%d")
    date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            report = await client.get_finance_report(date_from=date_from, date_to=date_to)
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    if not report:
        await callback.message.edit_text(
            "📭 Нет данных за последние 30 дней.",
            reply_markup=back_button(),
        )
        await callback.answer()
        return

    total_orders = 0
    total_sales = 0.0
    total_commission = 0.0
    total_logistics = 0.0
    total_paid = 0.0

    try:
        for item in report:
            total_orders += int(item.get("quantity", 0) or 0)
            total_sales += float(item.get("retailAmount", 0) or 0)
            total_commission += float(item.get("ppvzSalesCommission", 0) or 0)
            total_logistics += float(item.get("deliveryService", 0) or 0)
            total_paid += float(item.get("forPay", 0) or 0)
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при обработке отчёта: {e}",
            reply_markup=back_button(),
        )
        await callback.answer()
        return

    text = (
        f"💰 <b>Отчёт по реализации</b>\n"
        f"📅 {date_from} — {date_to}\n\n"
        f"📦 Заказов: {total_orders}\n"
        f"💵 Продажи: {_fmt_currency(total_sales)}\n"
        f"📉 Комиссия WB: {_fmt_currency(abs(total_commission))}\n"
        f"🚚 Логистика: {_fmt_currency(abs(total_logistics))}\n"
        f"✅ Итого к выплате: {_fmt_currency(total_paid)}\n\n"
        f"<i>Показаны агрегированные данные за период</i>"
    )

    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
