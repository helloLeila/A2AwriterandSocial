"""知乎开放接口客户端."""

import os
from typing import Any, Optional

import httpx


class ZhihuClient:
    """知乎API客户端."""

    def __init__(
        self,
        api_base: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.api_base = (api_base or os.getenv("ZHIHU_API_BASE", "https://www.zhihu.com/ring/moltbook/api")).rstrip("/")
        self.app_id = os.getenv("ZHIHU_APP_ID", "")
        self.app_key = os.getenv("ZHIHU_APP_KEY", "")
        self.access_token = os.getenv("ZHIHU_ACCESS_TOKEN", "")
        self.http = http_client or httpx.AsyncClient(timeout=15.0)

    def _headers(self) -> dict[str, str]:
        """请求头."""
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
            h["X-Zhihu-Access-Token"] = self.access_token
        if self.app_id:
            h["X-App-Id"] = self.app_id
            h["X-Zhihu-App-Id"] = self.app_id
        if self.app_key:
            h["X-App-Key"] = self.app_key
            h["X-Zhihu-App-Key"] = self.app_key
        return h

    def _extract_items(self, payload: Any) -> list[dict[str, Any]]:
        """从常见开放接口响应结构中提取列表数据."""
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []

        for key in ("data", "items", "list", "results", "contents"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = self._extract_items(value)
                if nested:
                    return nested

        return []

    async def get_hot_list(self, hours: int = 24) -> list[dict[str, Any]]:
        """拉取知乎热榜."""
        try:
            resp = await self.http.get(
                f"{self.api_base}/v1/content/hot_list",
                params={"hours": hours},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return self._extract_items(resp.json())[:20]
        except Exception:
            pass
        return []

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """知乎搜索."""
        try:
            resp = await self.http.get(
                f"{self.api_base}/v1/content/zhihu_search",
                params={"q": query, "limit": limit},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return self._extract_items(resp.json())
        except Exception:
            pass
        return []

    async def global_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """知乎全网搜索."""
        try:
            resp = await self.http.get(
                f"{self.api_base}/v1/content/global_search",
                params={"q": query, "limit": limit},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return self._extract_items(resp.json())
        except Exception:
            pass
        return []

    async def get_following_feed(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取关注流."""
        try:
            resp = await self.http.get(
                f"{self.api_base}/openapi/feed/following",
                params={"limit": limit},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return self._extract_items(resp.json())
        except Exception:
            pass
        return []

    async def get_following_list(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取关注列表."""
        try:
            resp = await self.http.get(
                f"{self.api_base}/openapi/user/following",
                params={"limit": limit},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return self._extract_items(resp.json())
        except Exception:
            pass
        return []

    async def get_followers_list(self, limit: int = 50) -> list[dict[str, Any]]:
        """获取粉丝列表."""
        try:
            resp = await self.http.get(
                f"{self.api_base}/openapi/user/followers",
                params={"limit": limit},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                return self._extract_items(resp.json())
        except Exception:
            pass
        return []
