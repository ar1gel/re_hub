from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import products_kb, main_kb
from bot.utils import filter_by_ignore_list, esc
from bot.menu import set_menu
from bot.cache import get as cache_get, set as cache_set

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
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
            return

    cards = data.get("cards", []) if isinstance(data, dict) else []
    cards = filter_by_ignore_list(cards, account)
    if not cards:
        await message.answer("📭 Товары не найдены.", reply_markup=products_kb())
        return

    header = f"📋 <b>Товары ({len(cards)} шт.)</b>"
    chunk = header + "\n\n"
    chunks = []
    for card in cards:
        vendor = esc(card.get("vendorCode", "—"))
        brand = esc(card.get("brand", "—"))
        name = esc(card.get("title", "—"))
        item = f"• <b>{name}</b>\n"
        item += f"  Артикул: {vendor}\n"
        item += f"  Бренд: {brand}\n\n"
        if len(chunk) + len(item) > 4096:
            chunks.append(chunk)
            chunk = item
        else:
            chunk += item
    chunks.append(chunk)

    for i, part in enumerate(chunks):
        kb = products_kb() if i == len(chunks) - 1 else None
        await message.answer(part, reply_markup=kb)


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

    cache_key = f"stocks:{account.id}"
    stocks = cache_get(cache_key)
    if stocks is None:
        from bot.wb_client import WbClient

        async with WbClient(account.token) as client:
            try:
                stocks = await client.get_product_stocks()
            except Exception as e:
                await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
                return
        cache_set(cache_key, stocks)

    stocks = filter_by_ignore_list(stocks, account)
    if not stocks:
        await message.answer("📭 Остатки не найдены.", reply_markup=products_kb())
        return

    header = f"📦 <b>Остатки ({len(stocks)} позиций)</b>"
    chunk = header + "\n\n"
    chunks = []
    for stock in stocks:
        vendor = esc(stock.get("vendorCode") or stock.get("supplierArticle") or "—")
        warehouses = stock.get("warehouses", [])
        total = sum(w.get("quantity", 0) for w in warehouses)
        item = f"• {vendor}\n"
        item += f"  Всего: {total} шт.\n"
        for w in warehouses:
            item += f"    {esc(w.get('warehouseName', '—'))}: {w.get('quantity', 0)} шт.\n"
        if len(chunk) + len(item) > 4096:
            chunks.append(chunk)
            chunk = item
        else:
            chunk += item
    chunks.append(chunk)

    for i, part in enumerate(chunks):
        kb = products_kb() if i == len(chunks) - 1 else None
        await message.answer(part, reply_markup=kb)


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
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
            return

    prices = filter_by_ignore_list(prices, account)
    if not prices:
        await message.answer("📭 Цены не найдены.", reply_markup=products_kb())
        return

    header = f"💰 <b>Цены ({len(prices)} позиций)</b>"
    chunk = header + "\n\n"
    chunks = []
    for price in prices:
        vendor = esc(price.get("vendorCode", "—"))
        sizes = price.get("sizes", [])
        if sizes:
            current = sizes[0].get("price", 0)
            discounted = sizes[0].get("discountedPrice", current)
        else:
            current = discounted = 0
        item = f"• {vendor}\n"
        item += f"  Цена: {_format_price(current)}\n"
        item += f"  Со скидкой: {_format_price(discounted)}\n\n"
        if len(chunk) + len(item) > 4096:
            chunks.append(chunk)
            chunk = item
        else:
            chunk += item
    chunks.append(chunk)

    for i, part in enumerate(chunks):
        kb = products_kb() if i == len(chunks) - 1 else None
        await message.answer(part, reply_markup=kb)
