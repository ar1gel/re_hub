from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import analytics_kb, main_kb
from bot.utils import esc, send_rich
from bot.menu import set_menu

router = Router()


@router.message(F.text == "📈 Воронка продаж")
async def analytics_funnel(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)
    if not accounts:
        await message.answer("❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.", reply_markup=main_kb())
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

    rd = data.get("data", {}) if isinstance(data, dict) else {}
    products = rd.get("products", [])
    stats = rd.get("statistics", {})

    md = "# 📈 Воронка продаж\n\n"
    if stats:
        md += "| Метрика | Значение |\n|:--------|--------:|\n"
        md += f"| 👁 Просмотры | {stats.get('views', '—')} |\n"
        md += f"| 🛒 В корзину | {stats.get('addToCart', '—')} |\n"
        md += f"| 📦 Заказы | {stats.get('orders', '—')} |\n"
        md += f"| ✅ Выкупы | {stats.get('buyouts', '—')} |\n"

    if products:
        md += "\n## По товарам\n| № | Название |\n|:-:|:---------|\n"
        for i, p in enumerate(products, 1):
            card = p.get("product", {}) if isinstance(p, dict) else {}
            name = esc(card.get("title", "—"))
            md += f"| {i} | {name} |\n"
    else:
        md += "\nНет данных о товарах в отчёте.\n"

    await send_rich(message, md, analytics_kb())
