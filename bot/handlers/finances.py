from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import finances_kb, main_kb
from bot.utils import esc
from bot.menu import set_menu

router = Router()


def _fmt_currency(kopecks: int) -> str:
    return f"{kopecks / 100:,.2f} ₽"


@router.message(F.text == "📄 Отчёт по реализации")
async def finances_report(message: Message) -> None:
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
    today = datetime.now()
    date_to = today.strftime("%Y-%m-%d")
    date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            report = await client.get_finance_report(date_from=date_from, date_to=date_to)
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=finances_kb())
            return

    if not report:
        await message.answer(
            "📭 Нет данных за последние 30 дней.",
            reply_markup=finances_kb(),
        )
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
        await message.answer(
            f"❌ Ошибка при обработке отчёта: {esc(e)}",
            reply_markup=finances_kb(),
        )
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

    await message.answer(text, reply_markup=finances_kb())
