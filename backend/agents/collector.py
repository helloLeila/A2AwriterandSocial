"""采集Agent - 后台静默执行，抓取知乎数据."""

import re
import time
from typing import Any

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, CollectedData, ZhihuAnswer, ZhihuQuestion


class ZhihuAPIConfig(BaseSettings):
    """知乎开放接口配置."""
    model_config = SettingsConfigDict(env_file="backend/.env", extra="ignore")

    zhihu_api_base: str = "https://www.zhihu.com/ring/moltbook/api"
    zhihu_app_id: str = ""
    zhihu_app_key: str = ""
    zhihu_access_token: str = ""
    zhihu_cache_ttl_seconds: int = 3600
    zhihu_hot_list_path: str = "/v1/content/hot_list"
    zhihu_search_path: str = "/v1/content/zhihu_search"


class CollectorAgent(BaseAgent):
    """采集Agent：调用知乎接口抓取目标问题、高赞回答、评论数据."""

    def __init__(
        self,
        api_base: str | None = None,
        config: ZhihuAPIConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        super().__init__(AgentRole.COLLECTOR, "采集Agent")
        self.zhihu_config = config or ZhihuAPIConfig()
        self.api_base = (api_base or self.zhihu_config.zhihu_api_base).rstrip("/")
        self.http = http_client or httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[float, Any]] = {}
        self.diagnostics: list[str] = []

    def _is_configured_secret(self, value: str) -> bool:
        """排除空值和示例占位符，避免把无效凭证发给接口."""
        normalized = value.strip()
        return bool(normalized) and not normalized.startswith("your_")

    def _auth_headers(self) -> dict[str, str]:
        """构造知乎开放接口请求头."""
        headers: dict[str, str] = {}

        if self._is_configured_secret(self.zhihu_config.zhihu_access_token):
            headers["Authorization"] = f"Bearer {self.zhihu_config.zhihu_access_token}"
            headers["X-Zhihu-Access-Token"] = self.zhihu_config.zhihu_access_token
        if self._is_configured_secret(self.zhihu_config.zhihu_app_id):
            headers["X-Zhihu-App-Id"] = self.zhihu_config.zhihu_app_id
        if self._is_configured_secret(self.zhihu_config.zhihu_app_key):
            headers["X-Zhihu-App-Key"] = self.zhihu_config.zhihu_app_key

        return headers

    def _cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        param_items = tuple(sorted(params.items()))
        return f"{endpoint}:{param_items}"

    def _extract_items(self, payload: Any) -> list[dict]:
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

    def _record_diagnostic(self, message: str):
        if message not in self.diagnostics:
            self.diagnostics.append(message)

    def _missing_credentials(self) -> list[str]:
        if self._is_configured_secret(self.zhihu_config.zhihu_access_token):
            return []
        return ["ZHIHU_ACCESS_TOKEN"]

    async def _get_data(self, endpoint: str, params: dict[str, Any]) -> list[dict]:
        """GET知乎接口并缓存成功结果，避免重复消耗开放接口额度."""
        cache_key = self._cache_key(endpoint, params)
        now = time.monotonic()
        cached = self._cache.get(cache_key)

        if cached and now - cached[0] < self.zhihu_config.zhihu_cache_ttl_seconds:
            return cached[1]

        try:
            resp = await self.http.get(
                f"{self.api_base}{endpoint}",
                params=params,
                headers=self._auth_headers(),
            )
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                if "json" not in content_type.lower():
                    self._record_diagnostic(
                        f"{endpoint} 非JSON响应，疑似路径或鉴权错误: {resp.text[:80]}"
                    )
                    return []

                data = self._extract_items(resp.json())
                self._cache[cache_key] = (now, data)
                return data

            self._record_diagnostic(
                f"{endpoint} HTTP {resp.status_code}: {resp.text[:120]}"
            )
        except Exception as exc:
            self._record_diagnostic(f"{endpoint} 请求异常: {type(exc).__name__}: {str(exc)[:120]}")

        return []

    def _extract_question_id(self, url: str) -> str:
        """从知乎URL中提取问题ID."""
        patterns = [
            r"question/(\d+)",
            r"zhuanlan\.zhihu\.com/p/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        # 返回一个基于URL的hash作为fallback
        return str(hash(url) % 100000000)

    async def _fetch_hot_list(self, hours: int = 24) -> list[dict]:
        """拉取知乎热榜."""
        return (await self._get_data(self.zhihu_config.zhihu_hot_list_path, {"hours": hours}))[:50]

    async def _fetch_search_results(self, query: str) -> list[dict]:
        """搜索知乎内容."""
        return await self._get_data(self.zhihu_config.zhihu_search_path, {"q": query, "limit": 10})

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行数据采集."""
        self.diagnostics = []
        question_url = context["question_url"]
        question_id = self._extract_question_id(question_url)

        missing_credentials = self._missing_credentials()
        if missing_credentials:
            self._record_diagnostic(f"知乎密钥未配置: {', '.join(missing_credentials)}")

        # 构造问题信息（实际应调用知乎API）
        question = ZhihuQuestion(
            id=question_id,
            title=context.get("question_title", "待获取问题标题"),
            url=question_url,
        )

        # 拉取热榜获取上下文
        hot_list = await self._fetch_hot_list()

        # 搜索相关问题和高赞回答
        search_query = context.get("question_title", "")
        search_results = []
        if search_query:
            search_results = await self._fetch_search_results(search_query)

        # 从搜索结果构建回答列表
        top_answers = []
        for item in search_results[:5]:
            if item.get("type") == "answer":
                top_answers.append(
                    ZhihuAnswer(
                        id=str(item.get("id", "")),
                        author_name=item.get("author", "匿名用户"),
                        excerpt=item.get("excerpt", "")[:500],
                        voteup_count=item.get("voteup_count", 0),
                        comment_count=item.get("comment_count", 0),
                    )
                )

        # 构建相关问题
        related_questions = []
        for item in search_results:
            if item.get("type") == "question":
                related_questions.append(
                    ZhihuQuestion(
                        id=str(item.get("id", "")),
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        hot_score=item.get("score"),
                    )
                )

        collected = CollectedData(
            question=question,
            top_answers=top_answers,
            related_questions=related_questions[:5],
            hot_list_context=hot_list[:10] if hot_list else None,
        )

        message = f"已采集 {len(top_answers)} 条高赞回答，{len(related_questions)} 个相关问题"
        if self.diagnostics:
            message = f"{message}；诊断：{'；'.join(self.diagnostics[:3])}"

        return {
            "collected_data": collected.model_dump(),
            "status": "success",
            "message": message,
            "diagnostics": self.diagnostics,
        }
