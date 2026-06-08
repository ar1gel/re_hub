from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import products_kb, main_kb
from bot.utils import filter_by_ignore_list
from bot.menu import set_menu

router = Router()


def _format_price(price: int | float | None) -> str:
    if price is None:
        return "—"
    return f"{price:,.2f} ₽"


@router.message(F.text == "📋 Список товаров")
async def products_list(message: Message) -> None:
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
            data = await client.get_products_list()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=products_kb())
            return

    cards = data.get("cards", []) if isinstance(data, dict) else []
    cards = filter_by_ignore_list(cards, account)
    if not cards:
        await message.answer("📭 Товары не найдены.", reply_markup=products_kb())
        return

    text = f"📋 <b>Товары ({len(cards)} шт.)</b>\n\n"
    for card in cards:
        vendor = card.get("vendorCode", "—")
        brand = card.get("brand", "—")
        name = card.get("title", "—")
        text += f"• <b>{name}</b>\n"
        text += f"  Артикул: {vendor}\n"
        text += f"  Бренд: {brand}\n\n"

    await message.answer(text, reply_markup=products_kb())


@router.message(F.text == "📦 Остатки")
async def products_stocks(message: Message) -> None:
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
            stocks = await client.get_product_stocks()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=products_kb())
            return

    stocks = filter_by_ignore_list(stocks, account)
    if not stocks:
        await message.answer("📭 Остатки не найдены.", reply_markup=products_kb())
        return

    text = f"📦 <b>Остатки ({len(stocks)} позиций)</b>\n\n"
    for stock in stocks:
        vendor = stock.get("vendorCode", "—")
        warehouses = stock.get("warehouses", [])
        total = sum(w.get("quantity", 0) for w in warehouses)
        text += f"• {vendor}\n"
        text += f"  Всего: {total} шт.\n"
        for w in warehouses:
            text += f"    {w.get('warehouseName', '—')}: {w.get('quantity', 0)} шт.\n"

    await message.answer(text, reply_markup=products_kb())


@router.message(F.text == "💰 Цены")
async def products_prices(message: Message) -> None:
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
            prices = await client.get_prices()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}", reply_markup=products_kb())
            return

    prices = filter_by_ignore_list(prices, account)
    if not prices:
        await message.answer("📭 Цены не найдены.", reply_markup=products_kb())
        return

    text = f"💰 <b>Цены ({len(prices)} позиций)</b>\n\n"
    for price in prices:
        vendor = price.get("vendorCode", "—")
        sizes = price.get("sizes", [])
        if sizes:
            current = sizes[0].get("price", 0)
            discounted = sizes[0].get("discountedPrice", current)
        else:
            current = discounted = 0
        text += f"• {vendor}\n"
        text += f"  Цена: {_format_price(current)}\n"
        text += f"  Со скидкой: {_format_price(discounted)}\n\n"

    await message.answer(text, reply_markup=products_kb())
