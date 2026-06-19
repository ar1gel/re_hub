import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiohttp import ClientSession

from wb_api.async_api import AsyncAPI
from wb_api.const import BaseURL

logger = logging.getLogger(__name__)

API_BASE = "https://common-api.wildberries.ru"
DISCOUNTS_PRICES_API = "https://discounts-prices-api.wildberries.ru"
CONTENT_API = "https://content-api.wildberries.ru"
MARKETPLACE_API = "https://marketplace-api.wildberries.ru"
ANALYTICS_API = "https://seller-analytics-api.wildberries.ru"
FINANCE_API = "https://finance-api.wildberries.ru"
STATISTICS_API = "https://statistics-api.wildberries.ru"

MSK_TZ = timezone(timedelta(hours=3))

MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0


class WbAuthError(Exception):
    pass


class WbRateLimitError(Exception):
    pass


class WbClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._api: AsyncAPI | None = None
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "WbClient":
        self._api = await AsyncAPI.build(token=self._token, base_url=BaseURL)
        self._session = ClientSession(
            headers={"Authorization": self._token}
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
        if self._api:
            await self._api.close()

    async def _request(self, method: str, url: str, **kwargs) -> dict | list:
        for attempt in range(MAX_RETRIES):
            async with self._session.request(method, url, **kwargs) as resp:
                if resp.status == 401:
                    raise WbAuthError("Невалидный токен WB API. Обновите токен в настройках аккаунта.")
                if resp.status == 402:
                    raise WbAuthError("Недостаточно прав для доступа к API. Проверьте права токена.")
                if resp.status == 429:
                    retry_after = float(resp.headers.get("Retry-After", BASE_RETRY_DELAY * (2 ** attempt)))
                    logger.warning(f"Rate limit hit, retrying in {retry_after}s (attempt {attempt + 1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise WbRateLimitError("Превышен лимит запросов WB API. Попробуйте позже.")
                if resp.status >= 400:
                    text = await resp.text()
                    raise RuntimeError(f"WB API error {resp.status}: {text[:1000]}")
                return await resp.json()

    async def ping(self) -> bool:
        try:
            await self._api.common.ping()
            return True
        except Exception:
            return False

    async def get_seller_info(self) -> dict:
        return await self._request("get", f"{API_BASE}/api/v1/seller-info")

    async def get_products_list(self) -> list[dict]:
        all_cards = []
        cursor = {"limit": 100}
        while True:
            payload = {"settings": {"cursor": cursor, "filter": {"withPhoto": -1}}}
            data = await self._request("post", f"{CONTENT_API}/content/v2/get/cards/list", json=payload)
            cards = data.get("cards", []) if isinstance(data, dict) else []
            all_cards.extend(cards)
            cursor_data = data.get("cursor", {}) if isinstance(data, dict) else {}
            next_cursor = cursor_data.get("updated")
            if not cards or not next_cursor or len(cards) < 100:
                break
            cursor = {"limit": 100, "updated": next_cursor}
        return all_cards

    async def get_product_stocks(self) -> list[dict]:
        task_data = await self._request(
            "get", f"{ANALYTICS_API}/api/v1/warehouse_remains",
            params={"groupByNm": "true", "groupBySa": "true"},
        )
        task_id = task_data.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError("Не удалось создать задачу отчёта об остатках")

        for i in range(21):
            if i > 0:
                await asyncio.sleep(6)
            status_data = await self._request(
                "get", f"{ANALYTICS_API}/api/v1/warehouse_remains/tasks/{task_id}/status",
            )
            if status_data.get("data", {}).get("status") == "done":
                break
        else:
            raise RuntimeError("Отчёт об остатках не сформировался за 2 мин")

        data = await self._request(
            "get", f"{ANALYTICS_API}/api/v1/warehouse_remains/tasks/{task_id}/download",
        )
        return data if isinstance(data, list) else []

    async def get_orders(self, date_from: str | None = None, limit: int = 100) -> list[dict]:
        all_orders = []
        params = {"limit": limit, "next": 0}
        if date_from:
            if date_from.replace("-", "").isdigit():
                dt = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=MSK_TZ)
                params["dateFrom"] = int(dt.timestamp())
            else:
                params["dateFrom"] = date_from
        while True:
            data = await self._request("get", f"{MARKETPLACE_API}/api/v3/orders", params=params)
            orders = data if isinstance(data, list) else data.get("orders", [])
            all_orders.extend(orders)
            next_cursor = data.get("next", 0) if isinstance(data, dict) else 0
            if not orders or next_cursor == 0 or len(orders) < limit:
                break
            params["next"] = next_cursor
        return all_orders

    async def get_sales(self, date_from: str | None = None) -> list[dict]:
        if date_from is None:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {"dateFrom": date_from, "flag": 1}
        data = await self._request("get", f"{STATISTICS_API}/api/v1/supplier/sales", params=params)
        return data if isinstance(data, list) else []

    async def get_sales_funnel(self, nm_ids: list[int] | None = None) -> dict:
        today = datetime.now()
        end = today.strftime("%Y-%m-%d")
        start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        prev_end = (today - timedelta(days=31)).strftime("%Y-%m-%d")
        prev_start = (today - timedelta(days=61)).strftime("%Y-%m-%d")
        payload = {
            "selectedPeriod": {"start": start, "end": end},
            "pastPeriod": {"start": prev_start, "end": prev_end},
        }
        if nm_ids:
            payload["nmIDs"] = nm_ids
        return await self._request("post", f"{ANALYTICS_API}/api/analytics/v3/sales-funnel/products", json=payload)

    async def get_finance_report(self, date_from: str, date_to: str) -> list[dict]:
        payload = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "period": "daily",
        }
        data = await self._request("post", f"{FINANCE_API}/api/finance/v1/sales-reports/detailed", json=payload)
        return data if isinstance(data, list) else []

    async def get_prices(self, nm_ids: list[int] | None = None) -> list[dict]:
        if nm_ids:
            payload = {"nmList": nm_ids}
            data = await self._request("post", f"{DISCOUNTS_PRICES_API}/api/v2/list/goods/filter", json=payload)
            if isinstance(data, dict):
                return data.get("data", {}).get("listGoods", [])
            return []
        all_goods = []
        offset = 0
        limit = 100
        while True:
            data = await self._request("get", f"{DISCOUNTS_PRICES_API}/api/v2/list/goods/filter", params={"limit": limit, "offset": offset})
            if isinstance(data, dict):
                goods = data.get("data", {}).get("listGoods", [])
            else:
                goods = []
            all_goods.extend(goods)
            if len(goods) < limit:
                break
            offset += limit
        return all_goods
