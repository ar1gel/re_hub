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

    async def get_product_stocks(self, nm_ids: list[int] | None = None) -> list[dict]:
        params = {}
        if nm_ids:
            params["nmIDs"] = nm_ids
        data = await self._request("get", f"{STATISTICS_API}/api/v3/stocks", params=params)
        return data if isinstance(data, list) else data.get("stocks", [])

    async def get_orders(self, date_from: str | None = None, limit: int = 30) -> list[dict]:
        params = {"limit": limit}
        if date_from:
            params["dateFrom"] = date_from
        data = await self._request("get", f"{MARKETPLACE_API}/api/v3/orders", params=params)
        return data if isinstance(data, list) else []

    async def get_sales(self, date_from: str | None = None, limit: int = 30) -> list[dict]:
        params = {"limit": limit, "flag": 1}
        if date_from:
            params["dateFrom"] = date_from
        data = await self._request("get", f"{STATISTICS_API}/api/v3/sales", params=params)
        return data if isinstance(data, list) else []

    async def get_sales_funnel(self, nm_ids: list[int]) -> dict:
        payload = {"nmIDs": nm_ids}
        return await self._request("post", f"{ANALYTICS_API}/api/analytics/v3/sales-funnel/products", json=payload)

    async def get_finance_report(self, date_from: str, date_to: str) -> list[dict]:
        params = {"dateFrom": date_from, "dateTo": date_to}
        data = await self._request("get", f"{STATISTICS_API}/api/v5/supplier/reportDetailByPeriod", params=params)
        return data if isinstance(data, list) else []

    async def get_prices(self, nm_ids: list[int] | None = None) -> list[dict]:
        params = {}
        if nm_ids:
            params["nmIDs"] = nm_ids
        data = await self._request("get", f"{DISCOUNTS_PRICES_API}/api/v3/prices", params=params)
        return data if isinstance(data, list) else []
