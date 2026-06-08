from aiogram import Router, F
from aiogram.types import CallbackQuery

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import analytics_menu, back_button, add_account_button

router = Router()


@router.callback_query(F.data == "menu_analytics")
async def menu_analytics(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📊 <b>Аналитика</b>\n\nВыбери действие:",
        reply_markup=analytics_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "analytics_funnel")
async def analytics_funnel(callback: CallbackQuery) -> None:
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

    from bot.wb_client import WbClient

    async with WbClient(account.token) as client:
        try:
            data = await client.get_sales_funnel(nm_ids=[])
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
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
        for product in products[:5]:
            card = product.get("product", {}) if isinstance(product, dict) else {}
            name = card.get("title", "—")
            text += f"• {name}\n"
    else:
        text += "Нет данных о товарах в отчёте.\n"

    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
