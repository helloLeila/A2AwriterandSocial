"""提问者画像Agent - 基于预设模板扩写提问者画像."""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, AskerProfile, AskerType


ASKER_TEMPLATES = {
    AskerType.ANXIOUS: {
        "name": "焦虑求助型",
        "traits": "想要具体可执行的建议，讨厌空泛鸡汤和正确的废话",
        "pain_points": "已经看过很多泛泛而谈的回答，需要真正能落地的方案",
        "taboos": ["别跟我说'你要努力'", "别给我百度百科式的定义", "别只说大道理不给步骤"],
    },
    AskerType.SKEPTICAL: {
        "name": "理性质疑型",
        "traits": "会追问证据、数据来源、边界条件和反例",
        "pain_points": "讨厌没有数据支撑的观点，讨厌以偏概全",
        "taboos": ["别说'大家都这样'", "别回避边界条件", "别用个例当规律"],
    },
    AskerType.EXPERIENCED: {
        "name": "经验补充型",
        "traits": "自己有相关经历，希望答主回应具体细节",
        "pain_points": "很多回答太浅，没有触及实际操作中的难点",
        "taboos": ["别讲我都知道的", "别忽略执行层面的细节", "别说得太绝对"],
    },
}


SYSTEM_PROMPT = """你是提问者画像分析师。基于提问者类型模板，为当前问题生成详细的提问者画像。

请输出JSON格式：
{
  "hot_answer_angles": ["高赞回答常用思路1", "高赞回答常用思路2", "高赞回答常用思路3", "高赞回答常用思路4"],
  "hated_expressions": ["讨厌1", "讨厌2", "讨厌3", "讨厌4"],
  "hoped_details": ["希望补充1", "希望补充2", "希望补充3", "希望补充4"],
  "first_feedback_preview": "发布后可能的第一条评论预览（口语化，像真人评论）"
}

要求：
- hot_answer_angles：这类问题的高赞回答通常从哪些角度切入，至少4个
- hated_expressions：提问者最讨厌的回答方式，至少4个
- hoped_details：提问者最希望看到的内容，至少4个
- 所有标签要具体，不要泛泛而谈
- first_feedback_preview 要像真实知乎评论区发言，带情绪"""


class AskerProfileAgent(BaseAgent):
    """提问者画像Agent."""

    def __init__(self):
        super().__init__(AgentRole.USER, "提问者画像Agent")

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        asker_type = context.get("asker_type", AskerType.ANXIOUS)
        question_title = context.get("question_title", "")
        question_desc = context.get("question_desc", "")

        template = ASKER_TEMPLATES.get(asker_type, ASKER_TEMPLATES[AskerType.ANXIOUS])

        user_content = f"""知乎问题：「{question_title}」

问题描述：{question_desc or '暂无详细描述'}

提问者类型：{template['name']}
类型特征：{template['traits']}
核心痛点：{template['pain_points']}
明确禁忌：{', '.join(template['taboos'])}

请生成该提问者的详细画像。高赞回答思路至少4个，标签至少4个。"""

        try:
            result_text = await self.call_llm(
                system_prompt=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.6,
                max_tokens=400,
            )
            result_text = self._extract_json(result_text)
            data = json.loads(result_text)
            profile = AskerProfile(
                asker_type=asker_type,
                real_confusion=", ".join(data.get("hot_answer_angles", [])[:2]),
                hated_expressions=data.get("hated_expressions", [])[:6],
                hoped_details=data.get("hoped_details", [])[:6],
                first_feedback_preview=data.get("first_feedback_preview", ""),
            )
        except Exception:
            profile = AskerProfile(
                asker_type=asker_type,
                real_confusion="从具体场景切入、用数据支撑、提供可执行步骤",
                hated_expressions=template["taboos"] + ["空泛鸡汤", "正确的废话"],
                hoped_details=["具体操作步骤", "真实案例", "避坑经验", "数据支撑"],
                first_feedback_preview="感谢分享！不过我想补充问一下...",
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
