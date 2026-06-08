from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import products_menu, back_button, add_account_button

router = Router()


def _format_price(price: int | None) -> str:
    if price is None:
        return "—"
    return f"{price / 100:,.2f} ₽"


@router.callback_query(F.data == "menu_products")
async def menu_products(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📦 <b>Товары</b>\n\nВыбери действие:",
        reply_markup=products_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "products_list")
async def products_list(callback: CallbackQuery) -> None:
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
            data = await client.get_products_list()
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка при получении товаров: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    cards = data.get("cards", []) if isinstance(data, dict) else []
    if not cards:
        await callback.message.edit_text("📭 Товары не найдены.", reply_markup=back_button())
        await callback.answer()
        return

    text = f"📋 <b>Товары ({len(cards)} шт.)</b>\n\n"
    for card in cards[:10]:
        nm_id = card.get("nmID", "—")
        vendor = card.get("vendorCode", "—")
        brand = card.get("brand", "—")
        name = card.get("title", "—")
        text += f"• <b>{name}</b>\n"
        text += f"  Артикул: {vendor} (nmID: {nm_id})\n"
        text += f"  Бренд: {brand}\n\n"

    if len(cards) > 10:
        text += f"…и ещё {len(cards) - 10} товаров.\n"

    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "products_stocks")
async def products_stocks(callback: CallbackQuery) -> None:
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
            stocks = await client.get_product_stocks()
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    if not stocks:
        await callback.message.edit_text("📭 Остатки не найдены.", reply_markup=back_button())
        await callback.answer()
        return

    text = f"📦 <b>Остатки ({len(stocks)} позиций)</b>\n\n"
    for stock in stocks[:10]:
        nm_id = stock.get("nmId", "—")
        qty = stock.get("quantity", 0)
        warehouse = stock.get("warehouseName", "—")
        text += f"• nmID: {nm_id}\n"
        text += f"  Склад: {warehouse}, Остаток: {qty} шт.\n\n"

    if len(stocks) > 10:
        text += f"…и ещё {len(stocks) - 10}.\n"

    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()


@router.callback_query(F.data == "products_prices")
async def products_prices(callback: CallbackQuery) -> None:
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
            prices = await client.get_prices()
        except Exception as e:
            await callback.message.edit_text(
                f"❌ Ошибка: {e}",
                reply_markup=back_button(),
            )
            await callback.answer()
            return

    if not prices:
        await callback.message.edit_text("📭 Цены не найдены.", reply_markup=back_button())
        await callback.answer()
        return

    text = f"💰 <b>Цены ({len(prices)} позиций)</b>\n\n"
    for price in prices[:10]:
        nm_id = price.get("nmID", "—")
        sizes = price.get("sizes", [])
        if sizes:
            current = sizes[0].get("price", 0)
            discounted = sizes[0].get("discountedPrice", current)
        else:
            current = discounted = 0
        text += f"• nmID: {nm_id}\n"
        text += f"  Цена: {_format_price(current)}\n"
        text += f"  Со скидкой: {_format_price(discounted)}\n\n"

    if len(prices) > 10:
        text += f"…и ещё {len(prices) - 10}.\n"

    await callback.message.edit_text(text, reply_markup=back_button())
    await callback.answer()
