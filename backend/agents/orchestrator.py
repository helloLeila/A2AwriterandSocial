"""会话编排器 - 协调4个Agent的执行流程."""

import uuid
from datetime import datetime
from typing import Any, Optional

from backend.agents.collector import CollectorAgent
from backend.agents.filter import FilterAgent
from backend.agents.user_agent import UserAgent
from backend.agents.answerer_agent import AnswererAgent
from backend.models.schemas import (
    ChatMessage,
    ConsensusBoard,
    DialogueRound,
    SessionState,
    SessionStatus,
    WriterFramework,
)


class SessionOrchestrator:
    """会话编排器：严格按4步流程执行A2A交互."""

    def __init__(self):
        self.sessions: dict[str, SessionState] = {}
        self.collector = CollectorAgent()
        self.filter_agent = FilterAgent()
        self.user_agent = UserAgent()
        self.answerer_agent = AnswererAgent()

    def create_session(self, question_url: str, question_title: str = "") -> str:
        """创建新会话."""
        session_id = str(uuid.uuid4())[:8]
        session = SessionState(
            session_id=session_id,
            question_url=question_url,
            status=SessionStatus.CREATED,
        )
        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self.sessions.get(session_id)

    async def step1_collect_and_filter(
        self, session_id: str, question_title: str = ""
    ) -> dict[str, Any]:
        """步骤1：采集Agent和过滤Agent后台静默执行."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.status = SessionStatus.COLLECTING

        # 采集Agent执行
        collect_result = await self.collector.execute({
            "question_url": session.question_url,
            "question_title": question_title,
        })

        if collect_result.get("status") == "success":
            from backend.models.schemas import CollectedData
            session.collected_data = CollectedData(**collect_result["collected_data"])

        session.status = SessionStatus.FILTERING

        # 过滤Agent执行
        filter_result = await self.filter_agent.execute({
            "collected_data": collect_result.get("collected_data", {}),
        })

        if filter_result.get("status") == "success":
            from backend.models.schemas import FilteredData
            session.filtered_data = FilteredData(**filter_result["filtered_data"])

        session.status = SessionStatus.DIALOGUE
        session.updated_at = datetime.now()

        return {
            "collect_status": collect_result.get("status"),
            "collect_message": collect_result.get("message"),
            "filter_status": filter_result.get("status"),
            "filter_message": filter_result.get("message"),
            "session": session,
        }

    async def step2_run_dialogue_round(
        self, session_id: str, round_number: int
    ) -> dict[str, Any]:
        """步骤2：执行一轮A2A社交对话."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        question_title = ""
        if session.collected_data and session.collected_data.question:
            question_title = session.collected_data.question.title

        # 准备上下文
        chat_history = [
            {"agent_role": m.agent_role, "content": m.content}
            for m in session.chat_messages
        ]

        context = {
            "question_title": question_title,
            "filtered_data": session.filtered_data.model_dump() if session.filtered_data else {},
            "chat_history": chat_history,
            "round_number": round_number,
        }

        # 用户Agent先发言
        user_result = await self.user_agent.execute(context)
        user_msg = ChatMessage(
            id=str(uuid.uuid4())[:8],
            session_id=session_id,
            agent_role="user",
            content=user_result["content"],
            round_number=round_number,
        )
        session.chat_messages.append(user_msg)

        # 更新上下文给答主Agent
        context["chat_history"].append({
            "agent_role": "user",
            "content": user_result["content"],
        })

        # 答主Agent回应
        answerer_result = await self.answerer_agent.execute(context)
        answerer_msg = ChatMessage(
            id=str(uuid.uuid4())[:8],
            session_id=session_id,
            agent_role="answerer",
            content=answerer_result["content"],
            round_number=round_number,
        )
        session.chat_messages.append(answerer_msg)

        # 记录对话轮次
        dialogue_round = DialogueRound(
            round_number=round_number,
            user_agent_message=user_msg,
            answerer_agent_message=answerer_msg,
        )
        session.dialogue_rounds.append(dialogue_round)
        session.updated_at = datetime.now()

        return {
            "user_message": user_msg,
            "answerer_message": answerer_msg,
            "round_number": round_number,
        }

    async def step3_generate_consensus(self, session_id: str) -> ConsensusBoard:
        """步骤3：生成需求对齐看板."""
        session = self.sessions.get(session_id)
        if not session:
            return ConsensusBoard()

        session.status = SessionStatus.ALIGNING

        # 使用LLM从对话中提取共识
        dialogue_text = "\n\n".join([
            f"用户：{r.user_agent_message.content}\n答主：{r.answerer_agent_message.content}"
            for r in session.dialogue_rounds
        ])

        system_prompt = """你是一个对话分析专家。请从以下用户Agent和答主Agent的多轮对话中，提取关键共识信息。

请按以下JSON格式输出（只输出JSON，不要有其他文字）：
{
  "user_core_needs": ["用户核心需求1", "需求2", ...],
  "user_taboos": ["用户禁忌1", "禁忌2", ...],
  "answerer_direction": ["答主创作方向1", "方向2", ...],
  "key_insights": ["关键洞察1", "洞察2", ...],
  "agreed_structure": "双方同意的回答结构概述"
}"""

        messages = [{"role": "user", "content": f"对话内容：\n\n{dialogue_text}"}]

        import json
        try:
            result_text = await self.user_agent.call_llm(
                system_prompt=system_prompt,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
            )
            # 提取JSON
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            data = json.loads(result_text)
            board = ConsensusBoard(**data)
        except Exception:
            # Fallback: 手动提取
            board = ConsensusBoard(
                user_core_needs=["通过多轮对话对齐创作需求"],
                user_taboos=["避免AI生成感", "不跑题"],
                answerer_direction=["基于真实数据创作", "贴合用户真实痛点"],
                key_insights=["双向沟通比单向输出更有效"],
            )

        session.consensus_board = board
        session.updated_at = datetime.now()
        return board

    async def step4_generate_framework(self, session_id: str) -> WriterFramework:
        """步骤4：生成创作者写作框架（禁止生成完整正文）."""
        session = self.sessions.get(session_id)
        if not session:
            return WriterFramework()

        consensus = session.consensus_board
        question_title = ""
        if session.collected_data and session.collected_data.question:
            question_title = session.collected_data.question.title

        system_prompt = """你是知乎创作辅导专家。请基于以下已达成共识的需求对齐结果，为创作者输出写作框架。

【绝对禁止】
- 禁止生成完整的回答正文
- 禁止写出可以直接发布的成段内容
- 只能输出框架、方向、结构、建议

【输出要求】
请按以下JSON格式输出（只输出JSON）：
{
  "title_suggestions": ["标题建议1", "标题建议2", ...],
  "angle_recommendations": ["切入角度1", "角度2", ...],
  "structure_outline": [
    {"section": "第一部分标题", "points": ["要点1", "要点2"]},
    ...
  ],
  "pitfall_checklist": ["避雷点1", "避雷点2", ...],
  "reference_materials": ["可参考素材1", "素材2", ...],
  "tone_guidance": "语气风格指导"
}"""

        content = f"""知乎问题：{question_title}

需求对齐结果：
- 用户核心需求：{', '.join(consensus.user_core_needs) if consensus else 'N/A'}
- 用户禁忌：{', '.join(consensus.user_taboos) if consensus else 'N/A'}
- 创作方向：{', '.join(consensus.answerer_direction) if consensus else 'N/A'}
- 关键洞察：{', '.join(consensus.key_insights) if consensus else 'N/A'}
- 同意结构：{consensus.agreed_structure if consensus else 'N/A'}
"""

        messages = [{"role": "user", "content": content}]

        import json
        try:
            result_text = await self.user_agent.call_llm(
                system_prompt=system_prompt,
                messages=messages,
                temperature=0.4,
                max_tokens=2000,
            )
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            data = json.loads(result_text)
            framework = WriterFramework(**data)
        except Exception:
            framework = WriterFramework(
                title_suggestions=[f"关于「{question_title}」的深度解析"],
                angle_recommendations=["从用户真实痛点切入"],
                structure_outline=[
                    {"section": "引言", "points": ["点明问题背景", "引发读者共鸣"]},
                    {"section": "主体", "points": ["分点论述", "提供数据支撑"]},
                    {"section": "总结", "points": ["回归核心问题", "给出 actionable 建议"]},
                ],
                pitfall_checklist=["避免空泛说教", "避免跑题", "避免AI生成感"],
                reference_materials=["知乎同类高赞回答"],
                tone_guidance="专业但有温度，理性但不冰冷，像朋友分享经验",
            )

        session.writer_framework = framework
        session.status = SessionStatus.COMPLETED
        session.updated_at = datetime.now()
        return framework
