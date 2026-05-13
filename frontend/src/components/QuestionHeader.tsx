import type { DemoSession } from '../types';

interface Props {
  state: DemoSession;
}

export default function QuestionHeader({ state }: Props) {
  return (
    <div className="question-header">
      <div className="question-topics">
        <span className="question-topic-tag">知乎A2A</span>
        <span className="question-topic-tag">社交创作</span>
      </div>
      <h1 className="question-title">{state.question_title || '加载中...'}</h1>
      {state.question_desc && (
        <p className="question-desc">{state.question_desc}</p>
      )}
      <div className="question-meta">
        <span>128 关注</span>
        <span>3.2万 浏览</span>
      </div>
      <div className="question-actions">
        <button className="zhihu-btn zhihu-btn-primary">关注问题</button>
        <button className="zhihu-btn zhihu-btn-ghost">邀请回答</button>
        <button className="zhihu-btn zhihu-btn-ghost">写回答</button>
      </div>
    </div>
  );
}
