import asyncio
from datetime import datetime, timedelta, timezone

from aiohttp import ClientSession

from wb_api.async_api import AsyncAPI
from wb_api.const import BaseURL


API_BASE = "https://common-api.wildberries.ru"
DISCOUNTS_PRICES_API = "https://discounts-prices-api.wildberries.ru"
CONTENT_API = "https://content-api.wildberries.ru"
MARKETPLACE_API = "https://marketplace-api.wildberries.ru"
ANALYTICS_API = "https://seller-analytics-api.wildberries.ru"
FINANCE_API = "https://finance-api.wildberries.ru"
STATISTICS_API = "https://statistics-api.wildberries.ru"

MSK_TZ = timezone(timedelta(hours=3))


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
        async with self._session.request(method, url, **kwargs) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"WB API error {resp.status}: {text[:200]}")
            return await resp.json()

    async def ping(self) -> bool:
        try:
            await self._api.common.ping()
            return True
        except Exception:
            return False

    async def get_seller_info(self) -> dict:
        return await self._request("get", f"{API_BASE}/api/v1/seller-info")

    async def get_products_list(self) -> dict:
        payload = {"settings": {"cursor": {"limit": 30}, "filter": {"withPhoto": -1}}}
        return await self._request("post", f"{CONTENT_API}/content/v2/get/cards/list", json=payload)

    async def get_product_stocks(self) -> list[dict]:
        task_data = await self._request(
            "get", f"{ANALYTICS_API}/api/v1/warehouse_remains",
            params={"groupByNm": True},
        )
        task_id = task_data.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError("Не удалось создать задачу отчёта об остатках")

        for _ in range(30):
            await asyncio.sleep(1)
            status_data = await self._request(
                "get", f"{ANALYTICS_API}/api/v1/warehouse_remains/tasks/{task_id}/status",
            )
            if status_data.get("data", {}).get("status") == "done":
                break
        else:
            raise RuntimeError("Отчёт об остатках не сформировался за 30 сек")

        data = await self._request(
            "get", f"{ANALYTICS_API}/api/v1/warehouse_remains/tasks/{task_id}/download",
        )
        return data if isinstance(data, list) else []

    async def get_orders(self, date_from: str | None = None, limit: int = 30) -> list[dict]:
        params = {"limit": limit, "next": 0}
        if date_from:
            if date_from.replace("-", "").isdigit():
                dt = datetime.strptime(date_from, "%Y-%m-%d").replace(tzinfo=MSK_TZ)
                params["dateFrom"] = int(dt.timestamp())
            else:
                params["dateFrom"] = date_from
        data = await self._request("get", f"{MARKETPLACE_API}/api/v3/orders", params=params)
        return data if isinstance(data, list) else data.get("orders", [])

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
        prev_end = start
        prev_start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
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
        else:
            data = await self._request("get", f"{DISCOUNTS_PRICES_API}/api/v2/list/goods/filter", params={"limit": 100, "offset": 0})
        if isinstance(data, dict):
            return data.get("data", {}).get("listGoods", [])
        return []
