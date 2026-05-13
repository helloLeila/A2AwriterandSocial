"""写后互动Agent - 模拟发布后提问者反馈和评论区互动."""

from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, PublishFeedback, CommentTurn


# 按提问者类型分类的系统prompt，生成更像真实知乎评论区用户的反馈

ANXIOUS_FEEDBACK_PROMPT = """你是一位在知乎上看到回答的普通用户。你的性格是：有真实困惑、想要具体建议、讨厌空泛鸡汤。

你现在要在这个回答下面写一条评论。注意：
- 要像真实用户刷知乎时的随手评论，不是写文章
- 可以带口语词："卧槽"、"确实"、"不过"、"想请教"、"收藏了"
- 可以带情绪：惊喜、焦虑、困惑、认同
- 可能追问具体细节，也可能说"这正是我需要的"
- 绝对禁止："感谢分享"、"写得很好"、"很有启发"这种模板评论
- 绝对禁止像AI助手那样总结回答要点
- 长度30-80字
- 直接输出评论文字，不要任何前缀"""

SKEPTICAL_FEEDBACK_PROMPT = """你是一位在知乎上看到回答的普通用户。你的性格是：理性质疑、会追问证据、不喜欢以偏概全。

你现在要在这个回答下面写一条评论。注意：
- 要像真实用户刷知乎时的随手评论，不是写文章
- 可能追问："有数据支撑吗？"、"这个说法有反例吗？"
- 可能补充："我查了一下，实际情况可能不同"
- 可能温和反驳："同意大部分，但有个边界条件..."
- 绝对禁止："感谢分享"、"写得很好"这种模板评论
- 绝对禁止像AI助手那样总结回答要点
- 长度30-80字
- 直接输出评论文字，不要任何前缀"""

EXPERIENCED_FEEDBACK_PROMPT = """你是一位在知乎上看到回答的普通用户。你自己有相关经历，想补充细节。

你现在要在这个回答下面写一条评论。注意：
- 要像真实用户刷知乎时的随手评论，不是写文章
- 可能说："作为过来人补充一句..."、"我补充一个踩坑经验"
- 可能认同并扩展："确实是这样，我再补充一个角度"
- 语气像朋友聊天，不要太正式
- 绝对禁止："感谢分享"、"写得很好"这种模板评论
- 绝对禁止像AI助手那样总结回答要点
- 长度30-80字
- 直接输出评论文字，不要任何前缀"""

SUGGESTION_PROMPT = """你是一位知乎创作参谋。基于提问者的评论，给答主一条具体的回应建议。

要求：
- 建议要具体可操作，不是泛泛而谈
- 长度30-60字
- 语气像同行建议，不要居高临下

直接输出建议文字。"""

COMMENT_REPLY_PROMPT = """你是一位在知乎评论区互动的普通用户。基于之前的对话上下文和答主的最新回复，写一条评论回复。

注意：
- 像真实用户随手评论，口语化
- 可能追问、认同、补充或质疑
- 带情绪，不要太冷静
- 长度30-80字
- 直接输出评论文字"""


class PostFeedbackAgent(BaseAgent):
    """写后互动Agent."""

    def __init__(self):
        super().__init__(AgentRole.ANSWERER, "写后互动Agent")

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """默认执行 - 生成发布后反馈."""
        return await self.generate_feedback(context)

    def _get_prompt_by_type(self, asker_type: str) -> str:
        """根据提问者类型返回对应的prompt."""
        prompts = {
            "skeptical": SKEPTICAL_FEEDBACK_PROMPT,
            "experienced": EXPERIENCED_FEEDBACK_PROMPT,
        }
        return prompts.get(asker_type, ANXIOUS_FEEDBACK_PROMPT)

    async def generate_feedback(self, context: dict[str, Any]) -> dict[str, Any]:
        """生成发布后提问者第一条反馈."""
        draft = context.get("draft_content", "")
        asker = context.get("asker_profile", {})
        strategy = context.get("strategy", {})
        asker_type = asker.get("asker_type", "anxious")

        system_prompt = self._get_prompt_by_type(asker_type)

        # 构建更贴近真实场景的user content
        user_content = f"""你正在刷知乎，看到了一个关于「{asker.get('real_confusion', '某个问题')}」的回答。

回答内容（节选）：
{draft[:600]}

你的困惑是：{asker.get('real_confusion', '')}
你特别讨厌的回答方式是：{', '.join(asker.get('hated_expressions', [])[:2])}

现在你在评论区打字："""

        try:
            asker_comment = await self.call_llm(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.7,
                max_tokens=100,
            )
            asker_comment = asker_comment.strip()
            # 去除可能的引号
            asker_comment = asker_comment.strip('"').strip("'")

            # 生成回应建议
            suggestion_user = f"""提问者评论：「{asker_comment}」

答主原回答：{draft[:400]}

请给答主一条回应建议。"""

            answerer_suggestion = await self.call_llm(
                system_prompt=SUGGESTION_PROMPT,
                messages=[{"role": "user", "content": suggestion_user}],
                temperature=0.5,
                max_tokens=120,
            )
            answerer_suggestion = answerer_suggestion.strip()

            feedback = PublishFeedback(
                asker_comment=asker_comment,
                answerer_suggestion=answerer_suggestion,
                status="success",
            )
        except Exception:
            # fallback 也要像真人
            fallbacks = {
                "skeptical": (
                    "这个数据有来源吗？我在实际中观察到的现象似乎不太一样。",
                    "可以引用具体的数据来源或案例来支撑观点。"
                ),
                "experienced": (
                    "说得挺对的，我再补充一个实际操作中容易忽略的点。",
                    "感谢补充，可以把你的经验整理成具体步骤，更有参考价值。"
                ),
            }
            c, s = fallbacks.get(asker_type, (
                "卧槽这正是我需要的！不过想追问一下具体怎么操作？",
                "可以补充一个具体的操作步骤或截图说明。"
            ))
            feedback = PublishFeedback(
                asker_comment=c,
                answerer_suggestion=s,
                status="failed",
            )

        return {"feedback": feedback.model_dump(), "status": "success"}

    async def generate_comment_reply(self, context: dict[str, Any]) -> dict[str, Any]:
        """生成评论区下一轮反馈."""
        asker = context.get("asker_profile", {})
        answerer_reply = context.get("answerer_reply", "")
        previous_turns = context.get("previous_turns", [])
        turn_number = context.get("turn_number", 1)
        asker_type = asker.get("asker_type", "anxious")

        history = "\n".join([
            f"答主：{t.get('answerer_reply', '')}\n你：{t.get('asker_feedback', '')}"
            for t in previous_turns[-2:]
        ])

        user_content = f"""你是一位知乎用户，正在评论区和答主互动。

{history}

答主最新回复：{answerer_reply}

你在评论区打字："""

        try:
            asker_feedback = await self.call_llm(
                system_prompt=COMMENT_REPLY_PROMPT,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.7,
                max_tokens=100,
            )
            asker_feedback = asker_feedback.strip().strip('"').strip("'")

            # 生成回应建议
            suggestion_prompt = f"""提问者最新评论：「{asker_feedback}」

请给答主一条回应建议。"""

            answerer_suggestion = await self.call_llm(
                system_prompt=SUGGESTION_PROMPT,
                messages=[{"role": "user", "content": suggestion_prompt}],
                temperature=0.5,
                max_tokens=120,
            )
            answerer_suggestion = answerer_suggestion.strip()

            turn = CommentTurn(
                turn_number=turn_number,
                answerer_reply=answerer_reply,
                asker_feedback=asker_feedback,
            )
        except Exception:
            turn = CommentTurn(
                turn_number=turn_number,
                answerer_reply=answerer_reply,
                asker_feedback="懂了，确实是这样。谢谢答主！",
            )
            answerer_suggestion = "可以礼貌收尾，邀请后续交流。"

        return {
            "turn": turn.model_dump(),
            "answerer_suggestion": answerer_suggestion,
            "status": "success",
        }
