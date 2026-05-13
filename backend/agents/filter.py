"""过滤Agent - 后台静默执行，筛选合规素材."""

import re
from typing import Any

from backend.agents.base import BaseAgent
from backend.models.schemas import AgentRole, FilteredData, ZhihuAnswer


class FilterAgent(BaseAgent):
    """过滤Agent：剔除劝退型硬核内容、AI水文、广告垃圾内容."""

    def __init__(self):
        super().__init__(AgentRole.FILTER, "过滤Agent")

        # AI水文特征词
        self.ai_watermark_patterns = [
            r"综上所述",
            r"首先.*?其次.*?最后",
            r"值得注意的是",
            r"不可否认的是",
            r"让我们.*?来看",
            r"从.*?角度来看",
            r"一言以蔽之",
            r"总而言之",
            r"本文旨在",
            r"通过本文的分析",
            r"ChatGPT",
            r"AI生成",
            r"大模型",
        ]

        # 广告垃圾特征
        self.ad_patterns = [
            r"点击链接",
            r"扫码.*?领取",
            r"限时优惠",
            r"加微信",
            r"私信我",
            r"购买.*?课程",
            r"公众号",
            r"关注.*?获取",
        ]

        # 劝退型硬核内容特征（过于专业、不友好的表达）
        self.hardcore_patterns = [
            r"证毕",
            r"Q\.?E\.?D\.?",
            r"定理\s*\d+",
            r"引理\s*\d+",
            r"证明：",
            r"根据.*?公式",
            r"推导过程",
        ]

    def _is_ai_watermark(self, text: str) -> tuple[bool, str]:
        """检测AI水文特征."""
        for pattern in self.ai_watermark_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"检测到AI水文特征: {pattern}"
        return False, ""

    def _is_ad_content(self, text: str) -> tuple[bool, str]:
        """检测广告内容."""
        for pattern in self.ad_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True, f"检测到广告特征: {pattern}"
        return False, ""

    def _is_hardcore_unfriendly(self, text: str) -> tuple[bool, str]:
        """检测劝退型硬核内容."""
        hardcore_count = 0
        for pattern in self.hardcore_patterns:
            if re.search(pattern, text):
                hardcore_count += 1
        if hardcore_count >= 2:
            return True, "内容过于硬核，可能劝退普通读者"
        return False, ""

    def _calculate_quality_score(self, answer: ZhihuAnswer) -> float:
        """计算内容质量分数."""
        score = 0.0

        # 点赞数权重
        if answer.voteup_count > 1000:
            score += 30
        elif answer.voteup_count > 500:
            score += 20
        elif answer.voteup_count > 100:
            score += 10

        # 评论互动权重
        if answer.comment_count > 50:
            score += 15
        elif answer.comment_count > 10:
            score += 8

        # 内容长度适中（知乎优质回答通常有一定深度但不过长）
        excerpt_len = len(answer.excerpt)
        if 200 <= excerpt_len <= 2000:
            score += 20
        elif excerpt_len > 2000:
            score += 10

        # 作者可信度（有作者信息的加分）
        if answer.author_name and answer.author_name != "匿名用户":
            score += 10

        return min(score, 100)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行内容过滤."""
        collected_data = context.get("collected_data", {})
        raw_answers = collected_data.get("top_answers", [])

        valid_answers = []
        invalid_answers = []
        filter_reasons = []

        for ans_dict in raw_answers:
            answer = ZhihuAnswer(**ans_dict)
            excerpt = answer.excerpt or ""

            # 依次检测
            is_ai, ai_reason = self._is_ai_watermark(excerpt)
            is_ad, ad_reason = self._is_ad_content(excerpt)
            is_hard, hard_reason = self._is_hardcore_unfriendly(excerpt)

            if is_ai:
                invalid_answers.append(answer)
                filter_reasons.append(f"[{answer.author_name}] {ai_reason}")
                continue
            if is_ad:
                invalid_answers.append(answer)
                filter_reasons.append(f"[{answer.author_name}] {ad_reason}")
                continue
            if is_hard:
                invalid_answers.append(answer)
                filter_reasons.append(f"[{answer.author_name}] {hard_reason}")
                continue

            # 质量评分
            quality_score = self._calculate_quality_score(answer)
            if quality_score < 15:
                invalid_answers.append(answer)
                filter_reasons.append(f"[{answer.author_name}] 质量评分过低 ({quality_score})")
                continue

            valid_answers.append(answer)

        # 内容分析摘要
        content_analysis = {
            "total_count": len(raw_answers),
            "valid_count": len(valid_answers),
            "invalid_count": len(invalid_answers),
            "avg_quality_score": sum(
                self._calculate_quality_score(a) for a in valid_answers
            ) / len(valid_answers) if valid_answers else 0,
        }

        filtered = FilteredData(
            valid_answers=valid_answers,
            invalid_answers=invalid_answers,
            content_analysis=content_analysis,
            filter_reasons=filter_reasons,
        )

        return {
            "filtered_data": filtered.model_dump(),
            "status": "success",
            "message": f"过滤完成：保留 {len(valid_answers)} 条，剔除 {len(invalid_answers)} 条",
        }
