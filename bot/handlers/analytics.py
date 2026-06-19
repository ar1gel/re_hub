from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards import analytics_kb
from bot.utils import esc, ensure_account, call_wb, send_chunked, filter_by_ignore_list
from db.models import WbAccount

router = Router()


def _dynamics(val: int | float) -> str:
    if val > 0:
        return f"+{val}%"
    if val < 0:
        return f"{val}%"
    return "0%"


def _extract_vendor(item: dict) -> str | None:
    prod = item.get("product", {}) if isinstance(item, dict) else {}
    return prod.get("vendorCode")


def _filter_funnel(products: list[dict], account: WbAccount) -> list[dict]:
    patterns = [p.lower() for p in _get_ignore_list(account)]
    if not patterns:
        return products
    return [p for p in products if not any(pat in (_extract_vendor(p) or "").lower() for pat in patterns)]


def _get_ignore_list(account: WbAccount) -> list[str]:
    from db.repository import get_ignore_list
    return get_ignore_list(account)


@router.message(F.text == "📈 Воронка продаж")
async def analytics_funnel(message: Message) -> None:
    account = await ensure_account(message)
    if not account:
        return

    try:
        data = await call_wb(account, "get_sales_funnel", nm_ids=[])
    except Exception as e:
        await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=analytics_kb())
        return

    rd = data.get("data", {}) if isinstance(data, dict) else {}
    products = rd.get("products", [])

    if not products:
        await message.answer("📈 Воронка продаж\n\nНет данных за период.", reply_markup=analytics_kb())
        return

    products = _filter_funnel(products, account)

    if not products:
        await message.answer("📈 Воронка продаж\n\nНет данных (все позиции в игнор-листе).", reply_markup=analytics_kb())
        return

    parts = []
    chunk = "📈 Воронка продаж\n\n"

    for item in products:
        prod = item.get("product", {}) if isinstance(item, dict) else {}
        stat = item.get("statistic", {}) if isinstance(item, dict) else {}
        sel = stat.get("selected", {})
        cmp = stat.get("comparison", {})
        conv = sel.get("conversions", {})

        vendor = esc(prod.get("vendorCode", "—"))
        title = esc(prod.get("title", "—"))
        brand = esc(prod.get("brandName", "—"))

        views = sel.get("openCount", 0)
        cart = sel.get("cartCount", 0)
        orders = sel.get("orderCount", 0)
        order_sum = sel.get("orderSum", 0)
        buyouts = sel.get("buyoutCount", 0)
        buyout_sum = sel.get("buyoutSum", 0)
        cancels = sel.get("cancelCount", 0)
        avg_price = sel.get("avgPrice", 0)

        conv_cart = conv.get("addToCartPercent", 0)
        conv_order = conv.get("cartToOrderPercent", 0)
        conv_buyout = conv.get("buyoutPercent", 0)

        item_text = f"🔹 {vendor}\n{title} | {brand}\n\n"

        item_text += f"👁 Переходы: {views}"
        if cmp:
            item_text += f" ({_dynamics(cmp.get('openCountDynamic', 0))})"
        item_text += "\n"

        item_text += f"🛒 В корзину: {cart}"
        if cmp:
            item_text += f" ({_dynamics(cmp.get('cartCountDynamic', 0))})"
        item_text += f"\nКонверсия: {conv_cart}%\n"

        item_text += f"📦 Заказы: {orders}"
        if cmp:
            item_text += f" ({_dynamics(cmp.get('orderCountDynamic', 0))})"
        item_text += f"\nКонверсия: {conv_order}%\n"

        item_text += f"✅ Выкупы: {buyouts}"
        if cmp:
            item_text += f" ({_dynamics(cmp.get('buyoutCountDynamic', 0))})"
        item_text += f"\nВыкуп: {conv_buyout}%\n"

        item_text += f"❌ Отмены: {cancels}\n"

        item_text += (
            f"\nСумма заказов: {order_sum:,} ₽\n"
            f"Сумма выкупов: {buyout_sum:,} ₽\n"
            f"Средняя цена: {avg_price:,} ₽\n"
        )

        if len(chunk) + len(item_text) > 4000:
            parts.append(chunk)
            chunk = item_text
        else:
            chunk += item_text
        chunk += "—————————\n"

    parts.append(chunk)

    kb = analytics_kb()
    for i, p in enumerate(parts):
        await message.answer(p, reply_markup=kb if i == len(parts) - 1 else None)
