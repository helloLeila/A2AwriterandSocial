"""答主Agent - 代表知乎创作者，专业耐心地沟通需求."""

from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole


ANSWERER_AGENT_SYSTEM_PROMPT = """你是答主Agent，代表知乎上的专业创作者。你的人设必须贴合真实答主，具备以下特征：

【核心人设】
- 你是某个领域的资深答主，有多年知乎创作经验
- 你专业但不傲慢，耐心但不啰嗦
- 你善于通过提问来确认用户需求，而不是直接给方案
- 你会根据用户的反馈灵活调整创作方向
- 你重视用户体验，会主动说"这样写你觉得怎么样"

【语气风格】
- 知乎深度理性的风格，但不枯燥
- 会主动确认："我理解你的意思是...对吗？"
- 会给出选择："我有两个思路，一是...二是...你倾向哪个？"
- 会表达专业判断："从创作角度，我建议...因为..."
- 会坦诚表达困难："这个方向有挑战，因为..."

【对话策略】
- 第一轮：认真倾听用户需求，复述确认核心诉求，提出初步思路
- 第二轮：根据用户反馈调整方向，细化创作方案，询问禁忌和底线
- 第三轮：整合前两轮信息，给出更精准的创作框架，确认细节
- 第四轮及以后：达成创作共识，总结对齐结果

【创作原则】
- 只输出写作框架、切入角度、结构规划，绝对不生成完整回答正文
- 强调「AI辅助、人为主导」，你的角色是帮用户理清思路
- 每个建议都要说明"为什么"，让用户理解创作逻辑

【绝对禁止】
- 禁止直接输出完整的回答正文
- 禁止像客服一样机械回复
- 禁止忽略用户的顾虑和禁忌
- 禁止一意孤行，必须根据用户反馈调整"""


class AnswererAgent(BaseAgent):
    """答主Agent：专业知乎创作者，主动确认需求、调整创作方案."""

    def __init__(self):
        super().__init__(AgentRole.ANSWERER, "答主Agent")

    def _build_context(self, context: dict[str, Any]) -> str:
        """构建对话上下文."""
        parts = []

        # 知乎问题信息
        question_title = context.get("question_title", "")
        if question_title:
            parts.append(f"你准备回答的知乎问题：「{question_title}」")

        # 过滤后的参考素材
        filtered = context.get("filtered_data", {})
        valid_answers = filtered.get("valid_answers", [])
        if valid_answers:
            parts.append("\n你调研了同类高赞回答，了解到：")
            for i, ans in enumerate(valid_answers[:3], 1):
                author = ans.get("author_name", "匿名")
                excerpt = ans.get("excerpt", "")[:120]
                vote = ans.get("voteup_count", 0)
                parts.append(f"  {i}. {author}（{vote}赞）：{excerpt}...")

        # 内容分析
        analysis = filtered.get("content_analysis", {})
        if analysis:
            parts.append(f"\n内容分析：有效回答 {analysis.get('valid_count', 0)} 条，"
                        f"平均质量分 {analysis.get('avg_quality_score', 0):.1f}")

        # 对话历史
        chat_history = context.get("chat_history", [])
        if chat_history:
            parts.append("\n对话历史：")
            for msg in chat_history[-6:]:
                role = "用户" if msg.get("agent_role") == "user" else "你"
                parts.append(f"  {role}：{msg.get('content', '')}")

        # 当前轮次
        round_num = context.get("round_number", 1)
        parts.append(f"\n当前是第 {round_num} 轮对话。")

        if round_num == 1:
            parts.append("用户刚刚表达了需求，你要认真倾听并复述确认，给出初步创作思路。")
        elif round_num == 2:
            parts.append("用户对初步方案有反馈（有顾虑或补充），你要据此调整方向。")
        elif round_num == 3:
            parts.append("进入深度对齐阶段，你要给出更精准的创作框架，明确结构和切入点。")
        else:
            parts.append("对话收尾阶段，确认共识并总结创作方向。")

        return "\n".join(parts)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行答主Agent对话."""
        ctx_text = self._build_context(context)
        round_num = context.get("round_number", 1)

        messages = [
            {"role": "user", "content": f"{ctx_text}\n\n请生成你（答主）在这一轮的专业回应："}
        ]

        content = await self.call_llm(
            system_prompt=ANSWERER_AGENT_SYSTEM_PROMPT,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )

        return {
            "content": content.strip(),
            "agent_role": "answerer",
            "round_number": round_num,
            "status": "success",
        }
