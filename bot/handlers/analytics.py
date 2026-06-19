from aiogram import Router, F
from aiogram.types import Message

from db.engine import get_session
from db.repository import get_accounts
from bot.keyboards import analytics_kb, main_kb
from bot.utils import esc, filter_by_ignore_list, get_selected_account, get_account_name
from bot.menu import set_menu

router = Router()

LIMIT = 4000


def _is_ignored(item: dict, account) -> bool:
    prod = item.get("product", {}) if isinstance(item, dict) else {}
    vendor = prod.get("vendorCode")
    if not vendor:
        return False
    from db.repository import get_ignore_list
    patterns = get_ignore_list(account)
    for p in patterns:
        if p.lower() in vendor.lower():
            return True
    return False


def _dynamics(val: int | float) -> str:
    if val > 0:
        return f"+{val}%"
    if val < 0:
        return f"{val}%"
    return "0%"


@router.message(F.text == "📈 Воронка продаж")
async def analytics_funnel(message: Message) -> None:
    account = await get_selected_account(message.from_user.id)
    if not account:
        acc_name = await get_account_name(message.from_user.id)
        await message.answer("❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.", reply_markup=main_kb(acc_name))
        set_menu(message.from_user.id, "main")
        return

    from bot.wb_client import WbClient
    async with WbClient(account.token) as client:
        try:
            data = await client.get_sales_funnel(nm_ids=[])
        except Exception as e:
            await message.answer(f"❌ Ошибка: {esc(e)}", reply_markup=analytics_kb())
            return

    rd = data.get("data", {}) if isinstance(data, dict) else {}
    products = rd.get("products", [])

    if not products:
        await message.answer("📈 Воронка продаж\n\nНет данных за период.", reply_markup=analytics_kb())
        return

    products = [p for p in products if not _is_ignored(p, account)]

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

        if len(chunk) + len(item_text) > LIMIT:
            parts.append(chunk)
            chunk = item_text
        else:
            chunk += item_text
        chunk += "—————————\n"

    parts.append(chunk)

    kb = analytics_kb()
    for i, p in enumerate(parts):
        await message.answer(p, reply_markup=kb if i == len(parts) - 1 else None)
