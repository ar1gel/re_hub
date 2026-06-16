from collections import defaultdict

from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import products_kb, main_kb
from bot.utils import filter_by_ignore_list, esc, send_rich
from bot.warehouses import WAREHOUSE_TO_REGION
from bot.menu import set_menu
from bot.cache import get as cache_get, set as cache_set

router = Router()

LIMIT = 32000


def _page(md: str, rows: list[str], reply_markup=None):
    chunk = md
    parts = []
    for r in rows:
        if len(chunk) + len(r) > LIMIT:
            parts.append(chunk)
            chunk = r
        else:
            chunk += r
    parts.append(chunk)
    return parts, reply_markup


@router.message(F.text == "📋 Список товаров")
async def products_list(message: Message) -> None:
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
            data = await client.get_products_list()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
            return

    cards = data.get("cards", []) if isinstance(data, dict) else []
    cards = filter_by_ignore_list(cards, account)
    if not cards:
        await message.answer("📭 Товары не найдены.", reply_markup=products_kb())
        return

    cards.sort(key=lambda c: (c.get("title") or "").lower())

    header = f"# 📋 Товары ({len(cards)} шт.)\n| Название | Артикул | Бренд |\n|:---------|:--------|:------|\n"
    rows = []
    for c in cards:
        rows.append(f"| {esc(c.get('title', '—'))} | `{esc(c.get('vendorCode', '—'))}` | {esc(c.get('brand', '—'))} |\n")
    parts, kb = _page(header, rows, products_kb())
    for i, p in enumerate(parts):
        await send_rich(message, p, kb if i == len(parts) - 1 else None)


@router.message(F.text == "📦 Остатки")
async def products_stocks(message: Message) -> None:
    async with get_session() as session:
        accounts = await get_accounts(session, message.from_user.id)
    if not accounts:
        await message.answer("❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.", reply_markup=main_kb())
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

    stocks.sort(key=lambda s: (s.get("vendorCode") or s.get("supplierArticle") or "").lower())

    rows = []
    for s in stocks:
        v = esc(s.get("vendorCode") or s.get("supplierArticle") or "—")
        wh = s.get("warehouses", [])
        total = sum(w.get("quantity", 0) for w in wh)

        by_region: dict[str, list[dict]] = defaultdict(list)
        for w in wh:
            wh_name = w.get("warehouseName", "—")
            region = WAREHOUSE_TO_REGION.get(wh_name, "Другие")
            by_region[region].append(w)

        rows.append(f"\n## `{v}` — **{total}** шт.\n| Регион | Склад | Шт. |\n|:-------|:------|----:|\n")
        for region in sorted(by_region):
            w_list = by_region[region]
            w_list.sort(key=lambda w: w.get("warehouseName", ""))
            region_total = sum(w.get("quantity", 0) for w in w_list)
            for i, w in enumerate(w_list):
                rlabel = region if i == 0 else ""
                wh_name = w.get("warehouseName", "—")
                rows.append(f"| {rlabel} | {wh_name} | {w.get('quantity', 0)} |\n")
            rows.append(f"| | **Итого** | **{region_total}** |\n")
        rows.append("---\n")

    header = f"# 📦 Остатки ({len(stocks)} позиций)\n"
    parts, kb = _page(header, rows, products_kb())
    for i, p in enumerate(parts):
        await send_rich(message, p, kb if i == len(parts) - 1 else None)


@router.message(F.text == "💰 Цены")
async def products_prices(message: Message) -> None:
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
            prices = await client.get_prices()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
            return

    prices = filter_by_ignore_list(prices, account)
    if not prices:
        await message.answer("📭 Цены не найдены.", reply_markup=products_kb())
        return

    prices.sort(key=lambda p: (p.get("vendorCode") or "").lower())

    header = f"# 💰 Цены ({len(prices)} позиций)\n| Артикул | Цена | Со скидкой |\n|:--------|-----:|-----------:|\n"
    rows = []
    for p in prices:
        v = esc(p.get("vendorCode", "—"))
        sizes = p.get("sizes", [])
        if sizes:
            cur = sizes[0].get("price", 0)
            disc = sizes[0].get("discountedPrice", cur)
        else:
            cur = disc = 0
        rows.append(f"| `{v}` | `{cur:,.2f} ₽` | `{disc:,.2f} ₽` |\n")
    parts, kb = _page(header, rows, products_kb())
    for i, p in enumerate(parts):
        await send_rich(message, p, kb if i == len(parts) - 1 else None)
