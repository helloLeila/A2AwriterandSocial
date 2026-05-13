"""Agent基类定义."""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
from anthropic import AsyncAnthropic
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.models.schemas import AgentRole


class AgentConfig(BaseSettings):
    """Agent配置."""
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    anthropic_api_key: str = ""
    anthropic_base_url: str = ""
    model_name: str = "claude-sonnet-4-6"


class BaseAgent(ABC):
    """Agent基类."""

    def __init__(self, role: AgentRole, name: str):
        self.role = role
        self.name = name
        self.config = AgentConfig()
        self._client: Optional[AsyncAnthropic] = None

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(
                api_key=self.config.anthropic_api_key,
                base_url=self.config.anthropic_base_url or None,
            )
        return self._client

    async def call_llm(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """调用Claude大模型."""
        response = await self.client.messages.create(
            model=self.config.model_name,
            system=system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行Agent任务."""
        pass

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role.value, "name": self.name}
