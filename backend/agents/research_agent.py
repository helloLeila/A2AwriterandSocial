"""全网研究Agent - 分析知乎搜索结果和已有回答."""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, ResearchResult


SYSTEM_PROMPT = """你是全网研究专家。基于知乎搜索结果和已有回答摘要，分析当前问题的语境。

请输出JSON格式：
{
  "common_views": ["常见观点1", "常见观点2", "常见观点3"],
  "overused_angles": ["已说烂的角度1", "已说烂的角度2", "已说烂的角度3", "已说烂的角度4"],
  "controversy_points": ["争议点1", "争议点2", "争议点3"],
  "reference_materials": ["可参考材料1", "可参考材料2", "可参考材料3"],
  "risky_expressions": ["风险表达1", "风险表达2", "风险表达3", "风险表达4"]
}

要求：
- 每个字段至少3个标签，最多5个
- overused_angles 和 risky_expressions 至少4个
- 给出具体、有洞察的分析，不要泛泛而谈
- 如果搜索结果为空，基于问题本身合理推断
- 风险表达要指出哪些说法容易翻车"""


class ResearchAgent(BaseAgent):
    """全网研究Agent."""

    def __init__(self):
        super().__init__(AgentRole.COLLECTOR, "全网研究Agent")

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        question_title = context.get("question_title", "")
        search_results = context.get("search_results", [])

        results_summary = "\n".join([
            f"- {item.get('title', '')}（{item.get('author', '匿名')}，{item.get('voteup_count', 0)}赞）：{item.get('excerpt', '')[:80]}..."
            for item in search_results[:5]
        ]) if search_results else "知乎搜索结果暂不可用"

        user_content = f"""知乎问题：「{question_title}」

知乎站内搜索结果：
{results_summary}

请分析这个问题的知乎语境：哪些观点已经被说烂了？哪些角度还有空间？有什么争议和风险？每个字段至少3个标签。"""

        try:
            result_text = await self.call_llm(
                system_prompt=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.3,
                max_tokens=400,
            )
            result_text = self._extract_json(result_text)
            data = json.loads(result_text)
            research = ResearchResult(
                common_views=data.get("common_views", [])[:5],
                overused_angles=data.get("overused_angles", [])[:5],
                controversy_points=data.get("controversy_points", [])[:5],
                reference_materials=data.get("reference_materials", [])[:5],
                risky_expressions=data.get("risky_expressions", [])[:5],
                status="success",
            )
        except Exception:
            research = ResearchResult(
                common_views=["大多数人认同的主流观点", "经验分享型回答占多数"],
                overused_angles=["泛泛而谈的经验分享", "正确的废话", "鸡汤式鼓励", "没有数据支撑的结论"],
                controversy_points=["不同群体的利益冲突", "定义和边界的分歧", "短期vs长期的视角差异"],
                reference_materials=["知乎高赞回答中的数据点", "行业报告关键结论", "权威机构发布的研究"],
                risky_expressions=["绝对化表述容易翻车", "未经证实的数据引用", "涉及敏感群体的刻板印象"],
                status="failed",
            )

        return {"research": research.model_dump(), "status": "success"}

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
