"""Demo编排器 - 协调知乎回答页A2A Demo全流程."""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from backend.agents.base import BaseAgent
from backend.agents.post_feedback_agent import PostFeedbackAgent
from backend.models.schemas import (
    AnswererProfile,
    AskerProfile,
    AskerType,
    CommentTurn,
    DebateRound,
    DemoPhase,
    DemoSession,
    PublishFeedback,
    ResearchResult,
    WritingStrategy,
    ZhihuFeedItem,
)
from backend.services.zhihu_client import ZhihuClient


FAST_ANALYSIS_PROMPT = """你是知乎A2A创作参谋系统。基于以下信息，一次性输出答主画像、提问者画像、全网语境分析、三方互搏和写作策略。

【输出要求】
必须严格按以下JSON格式输出，不要任何其他文字：

{
  "answerer_profile": {
    "content_interests": ["12-18字标签，说明具体关注领域和使用场景", "例如：大学学习方法与长期自驱管理"],
    "audience_expectation": "60-90字，说明读者为什么愿意看这个答主，不要只写期待真实有温度",
    "expression_style": "50-80字，说明适合用什么表达方式、为什么这种方式适合该问题",
    "experience_boundary": ["12-22字标签，说明不能伪造的经验边界", "例如：不要假装有心理咨询资质"],
    "suitable_angle": "120-180字的详细切入建议，必须包含具体开头场景、核心矛盾、展开路径、预期读者收获，不要写'从个人真实观察切入'这种空话",
    "angle_reference_links": ["标题：知乎/全网文章标题｜来源：知乎回答/知乎问题/全网搜索｜链接：https://...｜摘要：这篇材料说清了什么｜可借鉴：适合支撑切入建议的哪一段｜风险：不能照搬或要避开的点"]
  },
  "asker_profile": {
    "real_confusion": "120-180字，必须描述一个具体人群的具体卡点：已经尝试过什么、看了哪些回答仍然不懂、担心什么后果、希望得到什么判断标准。禁止输出'关于某题的真实困惑'这类套话",
    "hot_answer_angles": ["12-24字标签，要说明高赞回答的具体套路", "例如：先拆误区再给可执行训练法"],
    "hated_expressions": ["12-24字标签，要具体说明讨厌的表达", "例如：把自律说成纯靠意志力"],
    "hoped_details": ["12-24字标签，要具体说明想补充的细节", "例如：每天十分钟能练什么任务"],
    "reference_links": ["标题：知乎回答标题｜来源：知乎回答｜链接：https://www.zhihu.com/question/xxx/answer/yyy｜摘要：一句话摘要｜可借鉴：适合借鉴到回答的哪一部分｜风险：照搬时的风险", "标题：...｜来源：...｜链接：...｜摘要：...｜可借鉴：...｜风险：..."]
  },
  "research": {
    "common_views": ["12-24字标签，说明常见观点及适用边界"],
    "overused_angles": ["12-24字标签，说明这个角度为什么烂俗"],
    "controversy_points": ["12-24字标签，说明争议双方各自担心什么"],
    "reference_materials": ["可参考材料1：一句话说明为什么可参考", "可参考材料2：来源和参考价值"],
    "risky_expressions": ["风险表达1", "风险表达2", "风险表达3", "风险表达4"]
  },
  "debate_rounds": [
    {"round_number": 1, "agent_name": "答主视角", "stance": "200-300字，详细阐述创作立场。包含：具体观点、支撑论据、预期读者反应、创作信心来源。像一位有经验的答主在认真阐述自己的写作思路，有细节、有层次、不空洞。", "risk_or_blindspot": "150-250字，深入剖析这个立场的问题：哪里可能站不住脚、什么读者会不买账、已有回答中类似的思路效果怎样、信息盲区在哪、如果妥协会在哪里妥协、底线是什么、最终选择这个方向的核心原因。"},
    {"round_number": 1, "agent_name": "提问者视角", "stance": "200-300字，表达真实用户的困惑和期待。包含：看了哪些回答觉得不满意、具体哪一点没解决、自己的实际场景是什么、最希望回答能带给自己什么改变。", "risk_or_blindspot": "150-250字，听完各方观点后的深入反思：哪些需求可以调整、哪些必须坚持、有没有过度理想化、忽略了哪些现实约束、答主的顾虑有没有道理、对答主的新期待、如果最终回答还是不满意自己会怎么做。"},
    {"round_number": 1, "agent_name": "全网视角", "stance": "200-300字，综合现有高赞回答和评论区反馈。包含：目前回答的共性特征、读者点赞和踩的真实原因、被忽视的细分需求、这个话题在不同时期的热度变化。", "risk_or_blindspot": "150-250字，总结三方博弈的共识与分歧：什么群体被代表了、什么场景被忽略了、跟风写作的风险、信息茧房效应、最有可能被读者认可的路径、最大风险点在哪里、如果自己是读者会怎么评价最终答案。"}
  ],
  "strategy": {
    "is_suitable": true,
    "recommended_angles": ["推荐角度1", "推荐角度2"],
    "avoid_angles": ["避免角度1"],
    "structure_suggestion": "写作结构建议",
    "materials_to_cite": ["需引用材料1"],
    "effective_expression": "最有效的表达方式",
    "likely_followup": "发布后最可能被追问的问题"
  }
}

注意：
- 每个字段都必须有内容，不能空
- 所有 tag/list 项必须比普通关键词更具体，最短 8 个汉字，优先 12-24 个汉字；不要输出“主流观点”“具体步骤”“真实案例”这种信息密度很低的词
- 真实困惑必须结合「知乎搜索结果」和「全网搜索结果」里的材料，由大模型归纳读者仍然没被解决的卡点；不能用问题标题改写
- 互搏要真实有冲突感，stance 和 risk_or_blindspot 都要写得具体、有细节，不要空洞概括
- reference_materials 每条都要注明来源和一句话参考价值
- reference_links 和 angle_reference_links 必须优先从上方「知乎搜索结果」「全网搜索结果」中挑选，输出真实链接，并说明为什么这个材料支撑当前切入建议。如果搜索结果不足，再补充静态演示素材，并在来源里标注“静态演示素材”
- 策略要具体可操作
- 总输出控制在3000字以内"""


class FastAnalysisAgent(BaseAgent):
    """快速分析Agent - 一次LLM调用生成所有分析结果."""

    def __init__(self):
        from backend.models.schemas import AgentRole
        from backend.agents.base import AgentConfig
        self.role = AgentRole.USER
        self.name = "快速分析Agent"
        self.config = AgentConfig()

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        return await self.analyze(context)

    async def analyze(self, context: dict[str, Any]) -> dict[str, Any]:
        """一次性生成所有分析结果."""
        question_title = context.get("question_title", "")
        question_desc = context.get("question_desc", "")
        asker_type = context.get("asker_type", "anxious")
        feed = context.get("feed", [])
        following = context.get("following", [])
        search_results = context.get("search_results", [])
        global_results = context.get("global_results", [])

        feed_summary = "\n".join([
            f"- {item.get('title', '')}（{item.get('author', '')}）"
            for item in feed[:5]
        ]) if feed else "关注流数据暂不可用"

        following_summary = ", ".join(following[:10]) if following else "关注列表暂不可用"

        search_items = self._format_result_items(search_results[:5])
        search_summary = "\n".join(search_items) if search_items else "搜索结果暂不可用"

        global_items = self._format_result_items(global_results[:5])
        global_summary = "\n".join(global_items) if global_items else "全网搜索结果暂不可用"

        asker_type_name = {
            "anxious": "焦虑求助型",
            "skeptical": "理性质疑型",
            "experienced": "经验补充型",
        }.get(asker_type, "焦虑求助型")

        user_content = f"""知乎问题：「{question_title}」
问题描述：{question_desc or '暂无'}

提问者类型：{asker_type_name}

答主关注流：
{feed_summary}

答主关注列表：{following_summary}

知乎搜索结果：
{search_summary}

全网搜索结果：
{global_summary}

请一次性输出完整的分析结果。"""

        result_text = await self.call_llm(
            system_prompt=FAST_ANALYSIS_PROMPT,
            messages=[{"role": "user", "content": user_content}],
            temperature=0.5,
            max_tokens=6000,
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
        return data

    def _format_result_items(self, results: list[dict[str, Any]]) -> list[str]:
        items = []
        for item in results:
            title = item.get("title") or item.get("question_title") or item.get("name") or "未命名内容"
            author = item.get("author") or item.get("author_name") or item.get("user_name") or "匿名"
            votes = item.get("voteup_count", item.get("vote_count", 0))
            qid = item.get("question_id", "")
            aid = item.get("answer_id", item.get("id", ""))
            url = item.get("url", "")
            if qid and aid and not url:
                url = f"https://www.zhihu.com/question/{qid}/answer/{aid}"
            excerpt = (
                item.get("excerpt")
                or item.get("summary")
                or item.get("description")
                or item.get("content")
                or "暂无摘要"
            )[:80]
            items.append(
                f"- 标题：{title}\n  作者：{author} | {votes}赞\n  链接：{url or '未提供'}\n  摘要：{excerpt}..."
            )
        return items


class DemoOrchestrator:
    """Demo编排器：写前画像→互搏策略→写后反馈→评论互动."""

    def __init__(self):
        self.sessions: dict[str, DemoSession] = {}
        self.zhihu = ZhihuClient()
        self.fast_agent = FastAnalysisAgent()
        self.post_feedback_agent = PostFeedbackAgent()

    def create_session(
        self,
        question_title: str,
        question_desc: str = "",
        asker_type: AskerType = AskerType.ANXIOUS,
    ) -> str:
        """创建Demo会话."""
        session_id = str(uuid.uuid4())[:8]
        session = DemoSession(
            session_id=session_id,
            phase=DemoPhase.INIT,
            question_title=question_title,
            question_desc=question_desc,
        )
        self.sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[DemoSession]:
        return self.sessions.get(session_id)

    async def run_pre_writing_analysis(
        self, session_id: str, progress_callback: Any = None
    ) -> None:
        """执行写前分析 - 合并为单次LLM调用，目标<5秒."""
        session = self.sessions.get(session_id)
        if not session:
            return

        session.phase = DemoPhase.FETCHING
        if progress_callback:
            await progress_callback("profile_fetching", {"message": "正在拉取知乎数据..."})

        # === 并行拉取知乎数据 ===
        feed_task = self.zhihu.get_following_feed(limit=10)
        following_task = self.zhihu.get_following_list(limit=20)
        followers_task = self.zhihu.get_followers_list(limit=1)
        search_task = self.zhihu.search(session.question_title, limit=3)
        global_search_task = self.zhihu.global_search(session.question_title, limit=3)

        feed_raw, following_raw, followers_raw, search_raw, global_raw = await asyncio.gather(
            feed_task, following_task, followers_task, search_task, global_search_task,
            return_exceptions=True,
        )
        search_items = search_raw if not isinstance(search_raw, Exception) else []
        global_items = global_raw if not isinstance(global_raw, Exception) else []
        reference_fallbacks = self._build_reference_links(
            [*search_items, *global_items],
            fallback_question=session.question_title,
        )

        # 处理关注流
        if not isinstance(feed_raw, Exception):
            session.answerer_feed = [
                ZhihuFeedItem(
                    id=str(item.get("id", i)),
                    title=item.get("title", ""),
                    author=item.get("author", ""),
                    type=item.get("type", "answer"),
                    voteup_count=item.get("voteup_count", 0),
                    excerpt=item.get("excerpt", ""),
                )
                for i, item in enumerate(feed_raw)
            ]

        if not isinstance(following_raw, Exception):
            session.answerer_following = [
                item.get("name", item.get("nickname", ""))
                for item in following_raw
                if item.get("name") or item.get("nickname")
            ]

        if not isinstance(followers_raw, Exception):
            session.answerer_followers = len(followers_raw)

        # === 单次LLM调用生成所有分析 ===
        session.phase = DemoPhase.PROFILING
        if progress_callback:
            await progress_callback("profiling", {"message": "AI分析中..."})

        try:
            result = await self.fast_agent.analyze({
                "question_title": session.question_title,
                "question_desc": session.question_desc,
                "asker_type": session.asker_profile.asker_type if session.asker_profile else "anxious",
                "feed": [f.model_dump() for f in session.answerer_feed],
                "following": session.answerer_following,
                "search_results": search_items,
                "global_results": global_items,
            })

            # 解析结果
            ap = result.get("answerer_profile", {})
            session.answerer_profile = AnswererProfile(
                content_interests=ap.get("content_interests") or [
                    "围绕问题拆解具体行动路径",
                    "把抽象能力转成日常训练任务",
                ],
                audience_expectation=ap.get("audience_expectation")
                or "读者期待你先承认他们卡在执行和判断标准上，而不是继续讲正确但不可操作的大道理。",
                expression_style=ap.get("expression_style")
                or "适合用一个常见误区开场，再把概念拆成可练习的动作，语气克制但给出明确取舍。",
                experience_boundary=ap.get("experience_boundary") or [
                    "不要伪装成认知科学专家",
                    "不要承诺短期训练立刻见效",
                ],
                suitable_angle=ap.get("suitable_angle") or self._fallback_suitable_angle(session.question_title),
                angle_reference_links=(ap.get("angle_reference_links") or reference_fallbacks)[:4],
                fetch_status="success",
            )

            ak = result.get("asker_profile", {})
            session.asker_profile = AskerProfile(
                asker_type=AskerType.ANXIOUS,
                real_confusion=ak.get("real_confusion") or self._fallback_real_confusion(session.question_title),
                hot_answer_angles=(ak.get("hot_answer_angles") or [
                    "先拆常见误区再给训练动作",
                    "用真实场景解释判断标准",
                    "把抽象能力分成可复盘步骤",
                ])[:6],
                hated_expressions=(ak.get("hated_expressions") or [
                    "只喊长期主义不讲执行成本",
                    "把复杂问题归因成不够自律",
                    "没有边界条件的万能建议",
                ])[:6],
                hoped_details=(ak.get("hoped_details") or [
                    "给出第一周可以执行的小任务",
                    "说明什么迹象代表方向错了",
                    "补充不同基础人群的取舍",
                ])[:6],
                reference_links=(ak.get("reference_links") or reference_fallbacks)[:4],
            )

            rs = result.get("research", {})
            session.research = ResearchResult(
                common_views=rs.get("common_views") or [
                    "多数回答强调习惯养成但弱化场景差异",
                    "高赞内容偏方法论但缺少失败判断",
                ],
                overused_angles=rs.get("overused_angles") or [
                    "把复杂能力包装成三步公式",
                    "只讲读书笔记不讲迁移场景",
                ],
                controversy_points=rs.get("controversy_points") or [
                    "读者想要速成但答主担心过度承诺",
                    "经验派强调实操而理论派要求严谨",
                ],
                reference_materials=rs.get("reference_materials") or [
                    item.replace("标题：", "可参考材料：", 1)
                    for item in reference_fallbacks[:3]
                ] or ["可参考材料：静态演示素材｜来源：本地兜底｜参考价值：接口暂不可用时保留展示结构"],
                risky_expressions=rs.get("risky_expressions") or [
                    "保证几天内明显提升",
                    "所有人都适用同一套训练法",
                    "把不成功归因于读者不够自律",
                    "直接复述高赞回答的完整论证",
                ],
                status="success",
            )

            session.debate_rounds = [
                DebateRound(**r) for r in result.get("debate_rounds", [])
            ]

            st = result.get("strategy", {})
            session.strategy = WritingStrategy(
                is_suitable=st.get("is_suitable", True),
                recommended_angles=st.get("recommended_angles") or [
                    "从读者已经努力但判断不出效果的场景切入",
                    "用知乎搜索材料对照高赞回答的未覆盖卡点",
                ],
                avoid_angles=st.get("avoid_angles") or [
                    "不要把问题写成万能成功学清单",
                    "不要替读者生成可直接发布的完整回答",
                ],
                structure_suggestion=st.get("structure_suggestion")
                or "误区开场→读者卡点→已有回答没解决什么→三段写作框架→边界和反例。",
                materials_to_cite=st.get("materials_to_cite") or reference_fallbacks[:3],
                effective_expression=st.get("effective_expression")
                or "先承认读者困惑，再用短段落拆行动和判断标准，保持辅助写作而非代写口吻。",
                likely_followup=st.get("likely_followup")
                or "读者最可能追问：如果自己基础弱、时间少，第一周到底该怎么判断训练有没有跑偏？",
                status="success",
            )

        except Exception:
            # fallback
            session.answerer_profile = AnswererProfile(
                content_interests=[
                    "围绕问题拆解具体行动路径",
                    "把抽象能力转成日常训练任务",
                ],
                audience_expectation="读者期待你先承认他们卡在执行和判断标准上，而不是继续讲正确但不可操作的大道理。",
                expression_style="适合用一个常见误区开场，再把概念拆成可练习的动作，语气克制但给出明确取舍。",
                experience_boundary=[
                    "不要伪装成认知科学专家",
                    "不要承诺短期训练立刻见效",
                ],
                suitable_angle=self._fallback_suitable_angle(session.question_title),
                angle_reference_links=reference_fallbacks[:4],
                fetch_status="failed",
            )
            session.asker_profile = AskerProfile(
                asker_type=AskerType.ANXIOUS,
                real_confusion=self._fallback_real_confusion(session.question_title),
                hot_answer_angles=[
                    "先拆常见误区再给训练动作",
                    "用真实场景解释判断标准",
                    "把抽象能力分成可复盘步骤",
                ],
                hated_expressions=[
                    "只喊长期主义不讲执行成本",
                    "把复杂问题归因成不够自律",
                    "没有边界条件的万能建议",
                ],
                hoped_details=[
                    "给出第一周可以执行的小任务",
                    "说明什么迹象代表方向错了",
                    "补充不同基础人群的取舍",
                ],
                reference_links=reference_fallbacks[:4],
            )
            session.research = ResearchResult(
                common_views=[
                    "多数回答强调习惯养成但弱化场景差异",
                    "高赞内容偏方法论但缺少失败判断",
                ],
                overused_angles=[
                    "把复杂能力包装成三步公式",
                    "只讲读书笔记不讲迁移场景",
                ],
                controversy_points=[
                    "读者想要速成但答主担心过度承诺",
                    "经验派强调实操而理论派要求严谨",
                ],
                reference_materials=[
                    item.replace("标题：", "可参考材料：", 1)
                    for item in reference_fallbacks[:3]
                ] or ["可参考材料：静态演示素材｜来源：本地兜底｜参考价值：接口暂不可用时保留展示结构"],
                risky_expressions=[
                    "保证几天内明显提升",
                    "所有人都适用同一套训练法",
                    "把不成功归因于读者不够自律",
                    "直接复述高赞回答的完整论证",
                ],
                status="failed",
            )
            session.debate_rounds = [
                DebateRound(round_number=1, agent_name="答主视角", stance="作为创作者，我觉得从自己的真实经历和观察出发是最自然的切入方式。读者更愿意看一个'活'的人分享，而不是教科书式的罗列。我打算先讲一个自己或身边人的故事，引出问题的核心，再逐步展开方法论。这种方式的优势在于开场就能抓住注意力，让读者产生'这说的就是我'的共鸣。", risk_or_blindspot="但这个方式也有明显风险：个人样本太小，可能过于片面，不同背景的读者会觉得'你的情况跟我不一样'。而且如果故事讲不好，很容易变成流水账。我已经观察到，知乎上同类型的高赞回答中，纯经验分享类虽然开头吸引人，但评论区经常有读者质疑'个案不代表普遍情况'。我需要想办法让个人经验更具代表性，或者穿插一些公认的数据来平衡。"),
                DebateRound(round_number=1, agent_name="提问者视角", stance="说实话，我看了很多回答，大多数都在讲理论框架，看完之后我还是不知道具体该做什么。我需要的是能直接跟着做的步骤，最好每一步都有明确的判断标准和预期效果。比如'每天花15分钟做X，坚持一个月后你会看到Y变化'这种。我不反对讲故事，但故事之后必须要有干货，否则我会觉得被骗了时间。", risk_or_blindspot="不过冷静下来想，我的要求可能也有点过于理想化了。每个人的情况不同，一套固定的步骤不可能适合所有人。而且有些问题本身就不是线性的，强行拆成步骤反而会误导。也许我应该更开放地看待回答形式，只要核心信息密度够高、让我看完之后知道'下一步该往哪个方向探索'，就已经很有价值了。"),
                DebateRound(round_number=1, agent_name="全网视角", stance="从目前的知乎生态来看，这个话题下的高赞回答大致分为两类：一类是系统性的知识梳理，结构清晰但容易枯燥；另一类是个人逆袭故事，开头抓人但后劲不足。点赞高的往往是两者的结合体——用故事开场建立信任，再用结构化内容提供价值。评论区的高频反馈是'收藏了'和'求更新'，说明读者确实认可这种混合模式。", risk_or_blindspot="但这种共识也有盲区：现有高赞回答大多来自头部创作者，他们的表达能力和知识储备不是普通创作者能直接复制的。而且'故事+干货'的套路用得太多，读者已经开始审美疲劳。更重要的是，这个话题下有很多细分场景被忽视了——比如不同职业、不同年龄段的人面临的其实是不同层面的问题，但现有回答往往用一个统一的框架去套。如果创作者能找到这些被忽视的细分切入点，反而更容易突围。"),
            ]
            session.strategy = WritingStrategy(
                is_suitable=True,
                recommended_angles=[
                    "从读者已经努力但判断不出效果的场景切入",
                    "用知乎搜索材料对照高赞回答的未覆盖卡点",
                ],
                avoid_angles=[
                    "不要把问题写成万能成功学清单",
                    "不要替读者生成可直接发布的完整回答",
                ],
                structure_suggestion="误区开场→读者卡点→已有回答没解决什么→三段写作框架→边界和反例。",
                materials_to_cite=reference_fallbacks[:3],
                effective_expression="先承认读者困惑，再用短段落拆行动和判断标准，保持辅助写作而非代写口吻。",
                likely_followup="读者最可能追问：如果自己基础弱、时间少，第一周到底该怎么判断训练有没有跑偏？",
                status="failed",
            )

        # 发送进度
        if progress_callback:
            await progress_callback("answerer_profile_ready", {
                "profile": session.answerer_profile.model_dump(),
            })
            await progress_callback("asker_profile_ready", {
                "profile": session.asker_profile.model_dump(),
            })
            await progress_callback("research_ready", {
                "research": session.research.model_dump(),
            })
            for i, r in enumerate(session.debate_rounds):
                await progress_callback("debate_round", {"round": r.model_dump(), "index": i})
            await progress_callback("strategy_ready", {
                "strategy": session.strategy.model_dump(),
            })

        session.phase = DemoPhase.STRATEGY_READY
        session.updated_at = datetime.now()

    def _fallback_suitable_angle(self, question_title: str) -> str:
        return (
            f"从“很多人知道「{question_title}」重要，却把它误解成多想一会儿或多看几篇回答”这个场景开场，"
            "先写清读者低效努力的核心矛盾，再拆成提问质量、证据检查、复盘输出三步，让读者知道每天能练什么、"
            "练完如何判断有没有进步。"
        )

    def _fallback_real_confusion(self, question_title: str) -> str:
        return (
            f"读者并不是不知道「{question_title}」重要，而是看完高赞回答后仍卡在第一步：不知道该先改输入、"
            "改提问方式，还是先做复盘记录；他们担心照搬别人的学习节奏会失败，也希望有人给出能自检的判断标准。"
        )

    def _build_reference_links(
        self,
        results: list[dict[str, Any]],
        fallback_question: str,
    ) -> list[str]:
        references: list[str] = []
        for item in results[:8]:
            title = item.get("title") or item.get("question_title") or item.get("name") or fallback_question
            url = item.get("url") or ""
            qid = item.get("question_id", "")
            aid = item.get("answer_id", item.get("id", ""))
            if qid and aid and not url:
                url = f"https://www.zhihu.com/question/{qid}/answer/{aid}"
            if not url:
                continue
            source = (
                item.get("source")
                or item.get("type")
                or ("知乎回答" if "zhihu.com" in url else "全网搜索")
            )
            excerpt = (
                item.get("excerpt")
                or item.get("summary")
                or item.get("description")
                or item.get("content")
                or "围绕当前问题提供了可参考的论证角度"
            )
            references.append(
                f"标题：{str(title)[:42]}｜来源：{source}｜链接：{url}｜"
                f"摘要：{str(excerpt)[:72]}｜可借鉴：支撑切入建议中的开头场景、材料铺垫或反例提醒｜"
                "风险：只借鉴结构和材料，不照搬原文判断"
            )

        if references:
            return references

        return [
            f"标题：搜索「{fallback_question}」的知乎相关讨论｜来源：静态演示素材｜"
            f"链接：https://www.zhihu.com/search?type=content&q={fallback_question}｜"
            "摘要：接口暂不可用时保留展示位，实际部署应替换为知乎搜索或全网搜索返回的真实文章｜"
            "可借鉴：用于说明哪些高赞角度已经被反复讨论｜风险：演示素材不能当作正式引用",
            f"标题：搜索「{fallback_question}」的全网材料｜来源：静态演示素材｜"
            f"链接：https://www.zhihu.com/search?type=content&q={fallback_question}｜"
            "摘要：用于展示全网搜索结果进入切入建议的链路｜可借鉴：对照知乎回答以发现读者未被满足的卡点｜"
            "风险：需等真实接口返回后再提交正式材料",
        ]

    async def publish_and_feedback(
        self, session_id: str, draft_content: str, progress_callback: Any = None
    ) -> None:
        """模拟发布并生成提问者反馈."""
        session = self.sessions.get(session_id)
        if not session:
            return

        session.draft_content = draft_content
        session.phase = DemoPhase.PUBLISHED

        if progress_callback:
            await progress_callback("publishing", {"message": "正在生成提问者反馈..."})

        try:
            result = await self.post_feedback_agent.generate_feedback({
                "draft_content": draft_content,
                "asker_profile": session.asker_profile.model_dump() if session.asker_profile else {},
                "strategy": session.strategy.model_dump() if session.strategy else {},
            })
            session.publish_feedback = PublishFeedback(**result.get("feedback", {}))
        except Exception:
            session.publish_feedback = PublishFeedback(status="failed")

        session.phase = DemoPhase.FEEDBACK_READY
        session.updated_at = datetime.now()

        if progress_callback:
            await progress_callback("publish_feedback_ready", {
                "feedback": session.publish_feedback.model_dump() if session.publish_feedback else {},
            })

    async def comment_interaction(
        self, session_id: str, answerer_reply: str, progress_callback: Any = None
    ) -> dict[str, Any]:
        """评论区互动."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.phase = DemoPhase.COMMENTING
        turn_number = len(session.comment_turns) + 1

        try:
            result = await self.post_feedback_agent.generate_comment_reply({
                "asker_profile": session.asker_profile.model_dump() if session.asker_profile else {},
                "answerer_reply": answerer_reply,
                "previous_turns": [t.model_dump() for t in session.comment_turns],
                "turn_number": turn_number,
            })

            turn = CommentTurn(**result.get("turn", {}))
            session.comment_turns.append(turn)

            if progress_callback:
                await progress_callback("comment_turn_ready", {
                    "turn": turn.model_dump(),
                    "answerer_suggestion": result.get("answerer_suggestion", ""),
                })

            return {
                "turn": turn.model_dump(),
                "answerer_suggestion": result.get("answerer_suggestion", ""),
                "status": "success",
            }
        except Exception as e:
            return {"error": str(e), "status": "failed"}
