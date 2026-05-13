"""Pydantic数据模型定义 - 知乎回答页A2A Demo."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent角色枚举."""
    COLLECTOR = "collector"
    FILTER = "filter"
    USER = "user"
    ANSWERER = "answerer"


class AskerType(str, Enum):
    """提问者画像类型."""
    ANXIOUS = "anxious"        # 焦虑求助型
    SKEPTICAL = "skeptical"    # 理性质疑型
    EXPERIENCED = "experienced" # 经验补充型


class DemoPhase(str, Enum):
    """Demo阶段."""
    INIT = "init"
    FETCHING = "fetching"           # 拉取答主数据
    PROFILING = "profiling"         # 画像分析中
    DEBATING = "debating"           # 互搏中
    STRATEGY_READY = "strategy_ready" # 策略已生成
    DRAFTING = "drafting"           # 草稿编辑中
    PUBLISHED = "published"         # 已模拟发布
    FEEDBACK_READY = "feedback_ready" # 反馈已生成
    COMMENTING = "commenting"       # 评论互动中
    ERROR = "error"


class ZhihuFeedItem(BaseModel):
    """知乎关注流单条内容."""
    id: str
    title: str
    author: str
    type: str = "answer"
    voteup_count: int = 0
    excerpt: str = ""


class ZhihuQuestion(BaseModel):
    """兼容旧采集Agent的知乎问题模型."""
    id: str
    title: str
    url: str
    excerpt: Optional[str] = None
    answer_count: int = 0
    follower_count: int = 0
    hot_score: Optional[float] = None


class ZhihuAnswer(BaseModel):
    """兼容旧采集Agent的知乎回答模型."""
    id: str
    author_name: str
    author_url: Optional[str] = None
    excerpt: str
    voteup_count: int = 0
    comment_count: int = 0
    created_time: Optional[datetime] = None
    content: Optional[str] = None


class CollectedData(BaseModel):
    """兼容旧采集Agent的输出数据."""
    question: ZhihuQuestion
    top_answers: list[ZhihuAnswer] = []
    related_questions: list[ZhihuQuestion] = []
    hot_list_context: Optional[list[dict]] = None


class FilteredData(BaseModel):
    """兼容旧过滤Agent的输出数据."""
    valid_answers: list[ZhihuAnswer] = []
    invalid_answers: list[ZhihuAnswer] = []
    content_analysis: dict[str, Any] = {}
    filter_reasons: list[str] = []


class AnswererProfile(BaseModel):
    """答主画像."""
    content_interests: list[str] = []      # 关注领域
    audience_expectation: str = ""         # 受众期待
    expression_style: str = ""             # 适合表达方式
    experience_boundary: list[str] = []    # 不应伪造的经验边界
    suitable_angle: str = ""              # 适合切入角度
    angle_reference_links: list[str] = []   # 支撑切入建议的真实参考文章
    fetch_status: str = "pending"          # pending/success/failed


class AskerProfile(BaseModel):
    """提问者画像."""
    asker_type: AskerType = AskerType.ANXIOUS
    real_confusion: str = ""              # 用户真实困惑描述（100-150字）
    hot_answer_angles: list[str] = []      # 高赞回答思路列表
    hated_expressions: list[str] = []      # 讨厌的回答方式
    hoped_details: list[str] = []          # 希望补充的细节
    reference_links: list[str] = []        # 推荐阅读链接（推文/文章）
    first_feedback_preview: str = ""       # 发布后第一条反馈预览


class ResearchResult(BaseModel):
    """全网/知乎语境研究结果."""
    common_views: list[str] = []           # 常见观点
    overused_angles: list[str] = []        # 已过度使用的角度
    controversy_points: list[str] = []     # 争议点
    reference_materials: list[str] = []    # 可引用材料
    risky_expressions: list[str] = []      # 风险表达
    status: str = "pending"


class DebateRound(BaseModel):
    """互搏单轮."""
    round_number: int
    agent_name: str
    stance: str
    risk_or_blindspot: str = ""           # 指出另一视角的风险/盲点


class WritingStrategy(BaseModel):
    """写作策略."""
    is_suitable: bool = True               # 是否适合回答
    recommended_angles: list[str] = []     # 推荐切入角度
    avoid_angles: list[str] = []           # 不推荐切入角度
    structure_suggestion: str = ""         # 写作结构建议
    materials_to_cite: list[str] = []      # 需引用或避开的材料
    effective_expression: str = ""         # 对提问者最有效的表达方式
    likely_followup: str = ""              # 发布后最可能被追问的问题
    status: str = "pending"


class PublishFeedback(BaseModel):
    """发布后反馈."""
    asker_comment: str = ""                # 提问者第一条评论
    answerer_suggestion: str = ""          # 答主回应建议
    status: str = "pending"


class CommentTurn(BaseModel):
    """评论互动单轮."""
    turn_number: int
    answerer_reply: str = ""               # 答主回复
    asker_feedback: str = ""               # 提问者反馈
    generated_at: datetime = Field(default_factory=datetime.now)


class DemoSession(BaseModel):
    """Demo会话状态."""
    session_id: str
    phase: DemoPhase = DemoPhase.INIT
    question_title: str = ""
    question_desc: str = ""

    # 答主数据
    answerer_feed: list[ZhihuFeedItem] = []
    answerer_following: list[str] = []
    answerer_followers: int = 0

    # Agent输出
    answerer_profile: Optional[AnswererProfile] = None
    asker_profile: Optional[AskerProfile] = None
    research: Optional[ResearchResult] = None
    debate_rounds: list[DebateRound] = []
    strategy: Optional[WritingStrategy] = None

    # 发布与互动
    draft_content: str = ""
    publish_feedback: Optional[PublishFeedback] = None
    comment_turns: list[CommentTurn] = []

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class StartDemoRequest(BaseModel):
    """启动Demo请求."""
    question_title: str = Field(..., description="问题标题")
    question_desc: str = Field(default="", description="问题描述")
    asker_type: AskerType = Field(default=AskerType.ANXIOUS, description="提问者类型")


class StartDemoResponse(BaseModel):
    """启动Demo响应."""
    session_id: str
    phase: DemoPhase
    message: str


class PublishRequest(BaseModel):
    """模拟发布请求."""
    draft_content: str = Field(..., description="回答草稿")


class CommentRequest(BaseModel):
    """评论互动请求."""
    answerer_reply: str = Field(..., description="答主回复内容")


class StreamMessage(BaseModel):
    """SSE消息协议."""
    type: str
    payload: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
