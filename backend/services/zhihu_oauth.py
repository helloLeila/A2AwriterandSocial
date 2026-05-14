"""知乎 OAuth 授权码模式客户端."""

import os
from typing import Any
from urllib.parse import urlencode

import httpx


class ZhihuOAuthClient:
    """处理知乎 OAuth 登录、换 token、授权接口调用."""

    def __init__(
        self,
        oauth_base: str | None = None,
        app_id: str | None = None,
        app_key: str | None = None,
        authorize_path: str | None = None,
        token_path: str | None = None,
        userinfo_path: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.oauth_base = (oauth_base or os.getenv("ZHIHU_OAUTH_BASE", "https://openapi.zhihu.com")).rstrip("/")
        self.app_id = app_id if app_id is not None else os.getenv("ZHIHU_OAUTH_APP_ID", "")
        self.app_key = app_key if app_key is not None else os.getenv("ZHIHU_OAUTH_APP_KEY", "")
        self.authorize_path = authorize_path or os.getenv("ZHIHU_OAUTH_AUTHORIZE_PATH", "/authorize")
        self.token_path = token_path or os.getenv("ZHIHU_OAUTH_TOKEN_PATH", "/access_token")
        self.userinfo_path = userinfo_path or os.getenv("ZHIHU_OAUTH_USERINFO_PATH", "/oauth_info")
        self.http = http_client or httpx.AsyncClient(timeout=15.0)

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_key)

    def build_authorize_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "redirect_uri": redirect_uri,
            "app_id": self.app_id,
            "response_type": "code",
            "state": state,
        }
        return f"{self.oauth_base}{self.authorize_path}?{urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        payload = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "client_id": self.app_id,
            "client_secret": self.app_key,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        resp = await self.http.post(
            f"{self.oauth_base}{self.token_path}",
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("知乎 OAuth token 响应不是 JSON 对象")
        if data.get("code") == 401:
            raise ValueError(str(data.get("data") or "知乎 OAuth token 无效"))
        if not data.get("access_token"):
            raise ValueError(f"知乎 OAuth token 响应缺少 access_token: {data}")
        return data

    async def get_userinfo(self, access_token: str) -> dict[str, Any]:
        return await self.get_authorized(self.userinfo_path, access_token)

    async def get_authorized(
        self,
        path: str,
        access_token: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = await self.http.get(
            f"{self.oauth_base}{path}",
            params=params,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise ValueError("知乎 OAuth 授权接口响应不是 JSON 对象")
        if data.get("code") == 401:
            raise ValueError(str(data.get("data") or "知乎 OAuth access_token 无效"))
        return data
