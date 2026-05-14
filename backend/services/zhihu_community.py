"""知乎社区开放 API AK/SK 签名客户端."""

import base64
import hashlib
import hmac
import os
import time
from typing import Any

import httpx


class ZhihuCommunityClient:
    """处理知乎社区 API 的 HMAC-SHA256 请求签名."""

    def __init__(
        self,
        api_base: str | None = None,
        app_key: str | None = None,
        app_secret: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.api_base = (api_base or os.getenv("ZHIHU_COMMUNITY_BASE", "https://openapi.zhihu.com")).rstrip("/")
        self.app_key = app_key if app_key is not None else os.getenv("ZHIHU_COMMUNITY_APP_KEY", "")
        self.app_secret = app_secret if app_secret is not None else os.getenv("ZHIHU_COMMUNITY_APP_SECRET", "")
        self.http = http_client or httpx.AsyncClient(timeout=15.0)

    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    def signed_headers(
        self,
        extra_info: str = "",
        timestamp: str | None = None,
        log_id: str | None = None,
    ) -> dict[str, str]:
        ts = timestamp or str(int(time.time()))
        lid = log_id or f"request_{ts}"
        sign_str = f"app_key:{self.app_key}|ts:{ts}|logid:{lid}|extra_info:{extra_info}"
        digest = hmac.new(
            self.app_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sign = base64.b64encode(digest).decode("utf-8")
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-App-Key": self.app_key,
            "X-Timestamp": ts,
            "X-Log-Id": lid,
            "X-Sign": sign,
            "X-Extra-Info": extra_info,
        }

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        extra_info: str = "",
    ) -> dict[str, Any]:
        resp = await self.http.get(
            f"{self.api_base}{path}",
            params=params,
            headers=self.signed_headers(extra_info=extra_info),
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("知乎社区 API 响应不是 JSON 对象")
        return data

    async def post(
        self,
        path: str,
        payload: dict[str, Any],
        extra_info: str = "",
    ) -> dict[str, Any]:
        resp = await self.http.post(
            f"{self.api_base}{path}",
            json=payload,
            headers=self.signed_headers(extra_info=extra_info),
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("知乎社区 API 响应不是 JSON 对象")
        return data
