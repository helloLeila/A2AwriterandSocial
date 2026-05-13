"""用户Agent - 代表真实提问用户，发起需求对话."""

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole


USER_AGENT_SYSTEM_PROMPT = """你是用户Agent，代表知乎上真实的提问用户。你的人设必须贴合真实用户，具备以下特征：

【核心人设】
- 你是一个有真实困惑的普通人，不是完美的提问机器
- 你有情绪、有顾虑、会吐槽、会补充要求
- 你的语气自然口语化，像微信聊天一样，不用书面语
- 你会对答主的方向提出质疑，也会表达感谢和认同
- 你有自己的偏好和禁忌，会明确说"我不想看到这个"

【语气风格】
- 用口语化表达，偶尔有错别字或口语词也没关系
- 会带情绪词："感觉..."、"说实话..."、"我有点担心..."、"卧槽"
- 会追问细节："这个能再具体点吗"、"我不太理解你说的..."
- 会拒绝："这个方向不太对"、"我不想写成那样"
- 会补充："对了，我还想说..."、"差点忘了..."

【对话策略】
- 第一轮：表达核心需求，但描述可能比较模糊、口语化
- 第二轮：对答主的方案提出质疑或补充，表达真实顾虑
- 第三轮：进一步细化需求，明确自己的底线和禁忌
- 第四轮及以后：确认共识，补充遗漏的细节

【绝对禁止】
- 禁止像AI一样条理清晰地罗列1、2、3
- 禁止用"首先、其次、最后"等模板化表达
- 禁止一次性把所有需求说完，要像真人一样逐步补充
- 禁止直接生成完整的回答正文

当前对话上下文中的知乎问题信息将帮助你理解真实场景。你的目标是让答主真正理解你的需求，而不是接受一个敷衍的方案。"""


class UserAgent(BaseAgent):
    """用户Agent：代表真实提问用户，主动提需求、表达顾虑、补充要求."""

    def __init__(self):
        super().__init__(AgentRole.USER, "用户Agent")

    def _build_context(self, context: dict[str, Any]) -> str:
        """构建对话上下文."""
        parts = []

        # 知乎问题信息
        question_title = context.get("question_title", "")
        if question_title:
            parts.append(f"你正在关注的知乎问题：「{question_title}」")

        # 过滤后的参考素材
        filtered = context.get("filtered_data", {})
        valid_answers = filtered.get("valid_answers", [])
        if valid_answers:
            parts.append("\n你之前看过一些回答，有以下印象：")
            for i, ans in enumerate(valid_answers[:3], 1):
                author = ans.get("author_name", "匿名")
                excerpt = ans.get("excerpt", "")[:100]
                parts.append(f"  - {author}的回答提到了：{excerpt}...")

        # 对话历史
        chat_history = context.get("chat_history", [])
        if chat_history:
            parts.append("\n之前的对话：")
            for msg in chat_history[-6:]:
                role = "你" if msg.get("agent_role") == "user" else "答主"
                parts.append(f"  {role}：{msg.get('content', '')}")

        # 当前轮次
        round_num = context.get("round_number", 1)
        parts.append(f"\n当前是第 {round_num} 轮对话。")

        if round_num == 1:
            parts.append("这是对话的开始，你要先向答主表达你的核心需求和困惑。")
        elif round_num == 2:
            parts.append("答主刚才给了你一个初步方案，你要表达你的顾虑、质疑或补充需求。")
        elif round_num == 3:
            parts.append("经过两轮对话，你要进一步明确你的底线和禁忌，细化需求。")
        else:
            parts.append("对话接近尾声，你要确认是否达成了共识，补充遗漏细节。")

        return "\n".join(parts)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行用户Agent对话."""
        ctx_text = self._build_context(context)
        round_num = context.get("round_number", 1)

        messages = [
            {"role": "user", "content": f"{ctx_text}\n\n请生成你（用户）在这一轮的发言："}
        ]

        content = await self.call_llm(
            system_prompt=USER_AGENT_SYSTEM_PROMPT,
            messages=messages,
            temperature=0.85,
            max_tokens=800,
        )

        return {
            "content": content.strip(),
            "agent_role": "user",
            "round_number": round_num,
            "status": "success",
        }
