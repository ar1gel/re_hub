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
            cards = await client.get_products_list()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
            return

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
    from bot.wb_client import WbClient
    async with WbClient(account.token) as client:
        try:
            products = await client.get_products_list()
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
            return

        cache_key = f"stocks:{account.id}"
        stocks = cache_get(cache_key)
        if stocks is None:
            try:
                stocks = await client.get_product_stocks()
            except Exception as e:
                await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=products_kb())
                return
            cache_set(cache_key, stocks)

    stocks_by_vendor = {}
    for s in stocks:
        vendor = s.get("vendorCode") or s.get("supplierArticle")
        if vendor:
            stocks_by_vendor[vendor] = s

    all_items = []
    for p in products:
        vendor = p.get("vendorCode")
        if not vendor:
            continue
        if vendor in stocks_by_vendor:
            s = stocks_by_vendor[vendor]
            wh = s.get("warehouses", [])
            wh = [w for w in wh if not any(kw in (w.get("warehouseName") or "").lower() for kw in ("всего", "в пути"))]
            total = sum(w.get("quantity", 0) for w in wh)
        else:
            wh = []
            total = 0
        all_items.append({"vendorCode": vendor, "title": p.get("title", ""), "warehouses": wh, "total": total})

    all_items = filter_by_ignore_list(all_items, account)
    if not all_items:
        await message.answer("📭 Товары не найдены.", reply_markup=products_kb())
        return

    all_items.sort(key=lambda x: x.get("title", "").lower())

    parts = []
    chunk = f"📦 Остатки ({len(all_items)} позиций)\n\n"

    for item in all_items:
        v = esc(item["vendorCode"])
        wh = item["warehouses"]
        total = item["total"]

        by_region: dict[str, list[dict]] = defaultdict(list)
        for w in wh:
            wh_name = w.get("warehouseName", "—")
            region = WAREHOUSE_TO_REGION.get(wh_name, "Другие")
            by_region[region].append(w)

        item_text = f"🔹 {v} — {total} шт.\n"

        if total == 0:
            item_text += "Нет остатков\n"
        else:
            for region in sorted(by_region):
                w_list = by_region[region]
                w_list.sort(key=lambda w: w.get("warehouseName", ""))
                region_total = sum(w.get("quantity", 0) for w in w_list)
                item_text += f"  {region}: {region_total}\n"
                for w in w_list:
                    wh_name = w.get("warehouseName", "—")
                    qty = w.get("quantity", 0)
                    item_text += f"      {wh_name}: {qty}\n"

        if len(chunk) + len(item_text) > LIMIT:
            parts.append(chunk)
            chunk = item_text
        else:
            chunk += item_text
        chunk += "—————————\n"

    parts.append(chunk)

    kb = products_kb()
    for i, p in enumerate(parts):
        await message.answer(p, reply_markup=kb if i == len(parts) - 1 else None)


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
