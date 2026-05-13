export type AskerType = 'anxious' | 'skeptical' | 'experienced';

export type DemoPhase =
  | 'init'
  | 'fetching'
  | 'profiling'
  | 'debating'
  | 'strategy_ready'
  | 'drafting'
  | 'published'
  | 'feedback_ready'
  | 'commenting'
  | 'error';

export interface AnswererProfile {
  content_interests: string[];
  audience_expectation: string;
  expression_style: string;
  experience_boundary: string[];
  suitable_angle: string;
  angle_reference_links: string[];
  fetch_status: string;
}

export interface AskerProfile {
  asker_type: AskerType;
  real_confusion: string;
  hot_answer_angles: string[];
  hated_expressions: string[];
  hoped_details: string[];
  reference_links: string[];
  first_feedback_preview: string;
}

export interface ResearchResult {
  common_views: string[];
  overused_angles: string[];
  controversy_points: string[];
  reference_materials: string[];
  risky_expressions: string[];
  status: string;
}

export interface DebateRound {
  round_number: number;
  agent_name: string;
  stance: string;
  risk_or_blindspot: string;
}

export interface WritingStrategy {
  is_suitable: boolean;
  recommended_angles: string[];
  avoid_angles: string[];
  structure_suggestion: string;
  materials_to_cite: string[];
  effective_expression: string;
  likely_followup: string;
  status: string;
}

export interface PublishFeedback {
  asker_comment: string;
  answerer_suggestion: string;
  status: string;
}

export interface CommentTurn {
  turn_number: number;
  answerer_reply: string;
  asker_feedback: string;
}

export interface NotificationItem {
  id: string;
  tag: string;
  title: string;
  excerpt: string;
  time: string;
}

export interface DemoSession {
  session_id: string;
  phase: DemoPhase;
  question_title: string;
  question_desc: string;
  answerer_profile?: AnswererProfile;
  asker_profile?: AskerProfile;
  research?: ResearchResult;
  debate_rounds: DebateRound[];
  strategy?: WritingStrategy;
  draft_content: string;
  publish_feedback?: PublishFeedback;
  comment_turns: CommentTurn[];
}

export type StreamMessageType =
  | 'connected'
  | 'profile_fetching'
  | 'profiling'
  | 'answerer_profile_ready'
  | 'asker_profile_ready'
  | 'research_ready'
  | 'debate_round'
  | 'strategy_ready'
  | 'publish_feedback_ready'
  | 'comment_turn_ready'
  | 'error';

export interface StreamMessage {
  type: StreamMessageType;
  payload: Record<string, unknown>;
  timestamp: string;
}
