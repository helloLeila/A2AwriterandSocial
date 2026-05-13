"""互搏编排Agent - 三方视角两轮短平快互搏，生成写作策略."""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, DebateRound, WritingStrategy


SYSTEM_PROMPT = """你是知乎创作参谋系统。基于答主画像、提问者画像和全网研究三方视角，模拟一场"小圆桌"讨论，最终输出写作策略。

场景设定：
- 答主视角：刚写完回答草稿，想确认方向对不对
- 提问者视角：看了草稿，有话想说
- 全网视角：看过很多同类回答，有经验

第一轮（各自表态）：三方各自用1-2句话表达核心观点，像朋友聊天一样自然口语化。
第二轮（互相挑刺）：每个视角用1句话指出另一个视角的问题或风险。

要求：
- stance（立场）要写2-3句话，带口语感，不要干巴巴的结论
- risk_or_blindspot（挑刺）要写1-2句话，有具体细节
- 互搏要像真实对话，有来有回，不要一团和气
- 总输出控制在800字以内

请输出JSON格式：
{
  "debate_rounds": [
    {"round_number": 1, "agent_name": "答主视角", "stance": "...", "risk_or_blindspot": ""},
    {"round_number": 1, "agent_name": "提问者视角", "stance": "...", "risk_or_blindspot": ""},
    {"round_number": 1, "agent_name": "全网视角", "stance": "...", "risk_or_blindspot": ""},
    {"round_number": 2, "agent_name": "答主视角", "stance": "", "risk_or_blindspot": "..."},
    {"round_number": 2, "agent_name": "提问者视角", "stance": "", "risk_or_blindspot": "..."},
    {"round_number": 2, "agent_name": "全网视角", "stance": "", "risk_or_blindspot": "..."}
  ],
  "strategy": {
    "is_suitable": true,
    "recommended_angles": ["推荐角度1", "推荐角度2"],
    "avoid_angles": ["避免角度1", "避免角度2"],
    "structure_suggestion": "写作结构建议",
    "materials_to_cite": ["需引用或避开的材料1"],
    "effective_expression": "最有效的表达方式",
    "likely_followup": "发布后最可能被追问的问题"
  }
}

注意：
- 互搏要真实、有冲突感，不要一团和气
- 每轮每个视角只给一句话立场 + 一句话风险
- 策略要具体可操作，不是泛泛模板
- 输出严格JSON，不要多余文字
"""


class DebateAgent(BaseAgent):
    """互搏编排Agent."""

    def __init__(self):
        super().__init__(AgentRole.ANSWERER, "互搏编排Agent")

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        question_title = context.get("question_title", "")
        answerer = context.get("answerer_profile", {})
        asker = context.get("asker_profile", {})
        research = context.get("research", {})

        user_content = f"""知乎问题：「{question_title}」

【答主画像】
关注领域：{', '.join(answerer.get('content_interests', []))}
受众期待：{answerer.get('audience_expectation', '')}
适合表达方式：{answerer.get('expression_style', '')}
经验边界：{', '.join(answerer.get('experience_boundary', []))}
适合切入角度：{answerer.get('suitable_angle', '')}

【提问者画像】
类型：{asker.get('asker_type', 'anxious')}
真实困惑：{asker.get('real_confusion', '')}
讨厌的表达：{', '.join(asker.get('hated_expressions', []))}
希望补充的细节：{', '.join(asker.get('hoped_details', []))}

【全网研究】
常见观点：{', '.join(research.get('common_views', []))}
已说烂的角度：{', '.join(research.get('overused_angles', []))}
争议点：{', '.join(research.get('controversy_points', []))}
风险表达：{', '.join(research.get('risky_expressions', []))}

请进行两轮互搏并输出写作策略。"""

        try:
            result_text = await self.call_llm(
                system_prompt=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.4,
                max_tokens=500,
            )
            result_text = self._extract_json(result_text)
            data = json.loads(result_text)

            debate_rounds = [
                DebateRound(**r) for r in data.get("debate_rounds", [])
            ]
            s = data.get("strategy", {})
            strategy = WritingStrategy(
                is_suitable=s.get("is_suitable", True),
                recommended_angles=s.get("recommended_angles", []),
                avoid_angles=s.get("avoid_angles", []),
                structure_suggestion=s.get("structure_suggestion", ""),
                materials_to_cite=s.get("materials_to_cite", []),
                effective_expression=s.get("effective_expression", ""),
                likely_followup=s.get("likely_followup", ""),
                status="success",
            )
        except Exception:
            debate_rounds = [
                DebateRound(round_number=1, agent_name="答主视角", stance="从个人经验切入最自然", risk_or_blindspot=""),
                DebateRound(round_number=1, agent_name="提问者视角", stance="我要的是可落地的步骤，不是感受", risk_or_blindspot=""),
                DebateRound(round_number=1, agent_name="全网视角", stance="这个话题已有大量高赞回答", risk_or_blindspot=""),
                DebateRound(round_number=2, agent_name="答主视角", stance="", risk_or_blindspot="个人经验可能过于局限，缺乏普适性"),
                DebateRound(round_number=2, agent_name="提问者视角", stance="", risk_or_blindspot="过于追求步骤可能忽略深层原因"),
                DebateRound(round_number=2, agent_name="全网视角", stance="", risk_or_blindspot="已有回答的套路可能让读者审美疲劳"),
            ]
            strategy = WritingStrategy(
                is_suitable=True,
                recommended_angles=["从具体场景切入，再提炼通用方法", "用数据+个人观察结合"],
                avoid_angles=["泛泛而谈的经验", "正确的废话"],
                structure_suggestion="场景引入 → 核心方法 → 具体步骤 → 避坑提醒 → 总结",
                materials_to_cite=["知乎高赞回答中的关键数据", "行业公认的研究结论"],
                effective_expression="亲切但有干货，像朋友分享但信息密度高",
                likely_followup="这个方法适合我这种情况吗？",
                status="failed",
            )

        return {
            "debate_rounds": [r.model_dump() for r in debate_rounds],
            "strategy": strategy.model_dump(),
            "status": "success",
        }

    def _extract_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
