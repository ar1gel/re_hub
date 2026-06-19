from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards import finances_kb
from bot.utils import esc, send_rich, ensure_account, call_wb

router = Router()


@router.message(F.text == "📄 Отчёт по реализации")
async def finances_report(message: Message) -> None:
    account = await ensure_account(message)
    if not account:
        return

    today = datetime.now()
    date_to = today.strftime("%Y-%m-%d")
    date_from = (today - timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        report = await call_wb(account, "get_finance_report", date_from=date_from, date_to=date_to)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=finances_kb())
        return

    if not report:
        await message.answer("📭 Нет данных за последние 30 дней.", reply_markup=finances_kb())
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
        await message.answer(f"❌ Ошибка при обработке отчёта: {esc(e)}", reply_markup=finances_kb())
        return

    md = (
        f"# 💰 Отчёт по реализации\n"
        f"📅 {date_from} — {date_to}\n\n"
        f"| Показатель | Сумма |\n"
        f"|:-----------|------:|\n"
        f"| 📦 Заказов | `{total_orders}` |\n"
        f"| 💵 Продажи | `{total_sales:.2f} ₽` |\n"
        f"| 📉 Комиссия WB | `{abs(total_commission):.2f} ₽` |\n"
        f"| 🚚 Логистика | `{abs(total_logistics):.2f} ₽` |\n"
        f"| ✅ Итого к выплате | `{total_paid:.2f} ₽` |\n\n"
        f"---\n"
        f"<i>Показаны агрегированные данные за период</i>"
    )

    await send_rich(message, md, finances_kb())
