from html import escape as h

from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import analytics_kb, main_kb
from bot.menu import set_menu

router = Router()


@router.message(F.text == "📈 Воронка продаж")
async def analytics_funnel(message: Message) -> None:
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

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            data = await client.get_sales_funnel(nm_ids=[])
        except Exception as e:
            await message.answer(f"❌ Ошибка: {h(str(e))}", reply_markup=analytics_kb())
            return

    response_data = data.get("data", {}) if isinstance(data, dict) else {}
    products = response_data.get("products", [])
    statistics = response_data.get("statistics", {})

    text = "<b>📈 Воронка продаж</b>\n\n"

    if statistics:
        text += (
            f"👁 Просмотры: {statistics.get('views', '—')}\n"
            f"🛒 В корзину: {statistics.get('addToCart', '—')}\n"
            f"📦 Заказы: {statistics.get('orders', '—')}\n"
            f"✅ Выкупы: {statistics.get('buyouts', '—')}\n\n"
        )

    if products:
        text += f"<b>По товарам ({len(products)} шт.):</b>\n\n"
        for product in products:
            card = product.get("product", {}) if isinstance(product, dict) else {}
            name = h(card.get("title", "—"))
            text += f"• {name}\n"
    else:
        text += "Нет данных о товарах в отчёте.\n"

    await message.answer(text, reply_markup=analytics_kb())
