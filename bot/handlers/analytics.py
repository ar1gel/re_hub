from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import analytics_kb, main_kb
from bot.utils import esc
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
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=analytics_kb())
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
        items = []
        for product in products:
            card = product.get("product", {}) if isinstance(product, dict) else {}
            name = esc(card.get("title", "—"))
            items.append(f"• {name}\n")
        header = text + f"<b>По товарам ({len(products)} шт.):</b>"
        chunk = header + "\n\n"
        chunks = []
        for item in items:
            if len(chunk) + len(item) > 4096:
                chunks.append(chunk)
                chunk = item
            else:
                chunk += item
        chunks.append(chunk)
    else:
        text += "Нет данных о товарах в отчёте.\n"
        chunks = [text]

    for i, part in enumerate(chunks):
        kb = analytics_kb() if i == len(chunks) - 1 else None
        await message.answer(part, reply_markup=kb)
