import unittest

import httpx

from backend.agents.collector import CollectorAgent, ZhihuAPIConfig


class CollectorAgentTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_request_sends_zhihu_credentials(self):
        seen_headers = {}

        async def handler(request: httpx.Request) -> httpx.Response:
            seen_headers.update(request.headers)
            return httpx.Response(200, json={"data": []})

        collector = CollectorAgent(
            config=ZhihuAPIConfig(
                zhihu_api_base="https://example.test/api",
                zhihu_app_id="app-id",
                zhihu_app_key="app-key",
                zhihu_access_token="access-token",
            ),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        await collector._fetch_search_results("AI")

        self.assertEqual(seen_headers["authorization"], "Bearer access-token")
        self.assertEqual(seen_headers["x-zhihu-app-id"], "app-id")
        self.assertEqual(seen_headers["x-zhihu-app-key"], "app-key")

    async def test_search_results_are_cached_for_identical_queries(self):
        request_count = 0

        async def handler(request: httpx.Request) -> httpx.Response:
            nonlocal request_count
            request_count += 1
            return httpx.Response(200, json={"data": [{"id": "1"}]})

        collector = CollectorAgent(
            config=ZhihuAPIConfig(
                zhihu_api_base="https://example.test/api",
                zhihu_cache_ttl_seconds=60,
            ),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        first = await collector._fetch_search_results("AI")
        second = await collector._fetch_search_results("AI")

        self.assertEqual(first, [{"id": "1"}])
        self.assertEqual(second, [{"id": "1"}])
        self.assertEqual(request_count, 1)

    async def test_nested_data_items_are_extracted(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": {"items": [{"id": "1"}]}})

        collector = CollectorAgent(
            config=ZhihuAPIConfig(zhihu_api_base="https://example.test/api"),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        results = await collector._fetch_search_results("AI")

        self.assertEqual(results, [{"id": "1"}])

    async def test_non_json_response_is_reported_in_diagnostics(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html><title>404 - 知乎</title></html>")

        collector = CollectorAgent(
            config=ZhihuAPIConfig(zhihu_api_base="https://example.test/api"),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        results = await collector._fetch_search_results("AI")

        self.assertEqual(results, [])
        self.assertIn("非JSON响应", collector.diagnostics[0])

    async def test_execute_message_reports_missing_credentials_and_api_diagnostics(self):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html><title>404 - 知乎</title></html>")

        collector = CollectorAgent(
            config=ZhihuAPIConfig(
                zhihu_api_base="https://example.test/api",
                zhihu_app_id="your_app_id",
                zhihu_app_key="your_app_key",
                zhihu_access_token="your_access_token",
            ),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )

        result = await collector.execute({
            "question_url": "https://www.zhihu.com/question/123",
            "question_title": "AI",
        })

        self.assertIn("知乎密钥未配置", result["message"])
        self.assertIn("非JSON响应", result["message"])


if __name__ == "__main__":
    unittest.main()
