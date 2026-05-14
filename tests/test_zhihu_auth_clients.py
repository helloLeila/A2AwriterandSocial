import base64
import hashlib
import hmac
import unittest
from unittest.mock import patch

import httpx

from backend.services.zhihu_community import ZhihuCommunityClient
from backend.services.zhihu_oauth import ZhihuOAuthClient


class ZhihuOAuthClientTest(unittest.IsolatedAsyncioTestCase):
    def test_authorize_url_uses_zhihu_oauth_parameters(self):
        client = ZhihuOAuthClient(
            oauth_base="https://openapi.zhihu.com",
            app_id="app-id",
            app_key="app-key",
        )

        url = client.build_authorize_url(
            redirect_uri="https://demo.example.com/api/auth/zhihu/callback",
            state="state-1",
        )

        self.assertTrue(url.startswith("https://openapi.zhihu.com/authorize?"))
        self.assertIn("app_id=app-id", url)
        self.assertIn("response_type=code", url)
        self.assertIn("state=state-1", url)

    async def test_exchange_code_posts_json_to_access_token_endpoint(self):
        seen = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            seen["path"] = request.url.path
            seen["body"] = request.content.decode()
            return httpx.Response(
                200,
                json={"access_token": "token-1", "expires_in": 3600, "uid": 123},
            )

        client = ZhihuOAuthClient(
            oauth_base="https://openapi.zhihu.com",
            app_id="app-id",
            app_key="app-key",
            token_path="/access_token",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        token = await client.exchange_code(
            code="code-1",
            redirect_uri="https://demo.example.com/api/auth/zhihu/callback",
        )

        self.assertEqual(seen["path"], "/access_token")
        self.assertIn('"code":"code-1"', seen["body"].replace(" ", ""))
        self.assertEqual(token["access_token"], "token-1")


class ZhihuCommunityClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_signed_get_sends_required_hmac_headers(self):
        seen_headers = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            seen_headers.update(request.headers)
            return httpx.Response(200, json={"code": 0, "data": {"id": "ring-1"}})

        client = ZhihuCommunityClient(
            api_base="https://openapi.zhihu.com",
            app_key="people-token",
            app_secret="secret-key",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        with patch("backend.services.zhihu_community.time.time", return_value=1000):
            payload = await client.get("/openapi/ring/detail", {"ring_id": "ring-1"})

        expected = base64.b64encode(
            hmac.new(
                b"secret-key",
                b"app_key:people-token|ts:1000|logid:request_1000|extra_info:",
                hashlib.sha256,
            ).digest()
        ).decode()

        self.assertEqual(payload["data"]["id"], "ring-1")
        self.assertEqual(seen_headers["x-app-key"], "people-token")
        self.assertEqual(seen_headers["x-timestamp"], "1000")
        self.assertEqual(seen_headers["x-log-id"], "request_1000")
        self.assertEqual(seen_headers["x-extra-info"], "")
        self.assertEqual(seen_headers["x-sign"], expected)


if __name__ == "__main__":
    unittest.main()
