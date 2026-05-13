"""个人画像Agent - 基于知乎关注流/关注列表/粉丝列表分析答主."""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, AnswererProfile


SYSTEM_PROMPT = """你是个人内容画像分析师。基于知乎用户的关注流、关注列表和粉丝数据，分析这个用户的内容特征。

请输出JSON格式：
{
  "content_interests": ["领域1", "领域2", "领域3", "领域4"],
  "audience_expectation": "受众期待的一句话描述",
  "expression_style": "适合表达方式的一句话描述",
  "experience_boundary": ["不应伪造的经验1", "不应伪造的经验2", "不应伪造的经验3"],
  "suitable_angle": "针对当前问题，适合从什么角度切入"
}

要求：
- content_interests 至少4个标签
- experience_boundary 至少3个标签
- 每个标签要具体，不要泛泛而谈
- 如果数据不足，基于已有信息合理推断
- 严禁胡编乱造用户个人信息
"""


class AnswererProfileAgent(BaseAgent):
    """个人画像Agent."""

    def __init__(self):
        super().__init__(AgentRole.USER, "个人画像Agent")

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """生成个人画像."""
        feed = context.get("feed", [])
        following = context.get("following", [])
        followers_count = context.get("followers_count", 0)
        question_title = context.get("question_title", "")

        feed_summary = "\n".join([
            f"- {item.get('title', '')}（{item.get('author', '')}）"
            for item in feed[:10]
        ]) if feed else "关注流数据暂不可用"

        following_summary = ", ".join(following[:20]) if following else "关注列表暂不可用"

        user_content = f"""当前知乎问题：「{question_title}」

用户关注流（最近浏览/互动内容）：
{feed_summary}

用户关注列表：{following_summary}

用户粉丝数：{followers_count}

请分析该用户的内容画像。标签至少4个，每个要具体。"""

        try:
            result_text = await self.call_llm(
                system_prompt=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.3,
                max_tokens=400,
            )
            result_text = self._extract_json(result_text)
            data = json.loads(result_text)
            profile = AnswererProfile(
                content_interests=data.get("content_interests", [])[:6],
                audience_expectation=data.get("audience_expectation", ""),
                expression_style=data.get("expression_style", ""),
                experience_boundary=data.get("experience_boundary", [])[:5],
                suitable_angle=data.get("suitable_angle", ""),
                fetch_status="success",
            )
        except Exception:
            profile = AnswererProfile(
                content_interests=["知识分享", "生活经验", "职场成长", "深度思考"],
                audience_expectation="期待真实、有温度、有信息密度的回答",
                expression_style="亲切自然，像朋友聊天但干货满满",
                experience_boundary=["不伪造专业资质", "不编造亲身经历", "不传播未经证实的数据"],
                suitable_angle="从个人真实观察切入，再提炼通用方法",
                fetch_status="failed",
            )

        return {"profile": profile.model_dump(), "status": "success"}

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
