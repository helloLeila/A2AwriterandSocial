import { useMemo, useState } from 'react';
import type { DemoSession, NotificationItem, ZhihuOAuthUser } from '../types';
import Navbar from './Navbar';

interface Props {
  state: DemoSession;
  isLoading: boolean;
  notifications: NotificationItem[];
  authUser?: ZhihuOAuthUser;
  authLoading?: boolean;
  onLogin?: () => void;
  onLogout?: () => void;
  onBackToEditor: () => void;
  onSendComment: (reply: string) => void;
}

export default function AnswerDetailPage({
  state,
  isLoading,
  notifications,
  authUser,
  authLoading,
  onLogin,
  onLogout,
  onBackToEditor,
  onSendComment,
}: Props) {
  const [reply, setReply] = useState('');
  const [showEvidence, setShowEvidence] = useState(false);
  const firstComment = state.publish_feedback?.asker_comment;
  const suggestion = state.publish_feedback?.answerer_suggestion;

  const answerParagraphs = useMemo(() => {
    const text = state.draft_content.trim() || '答主刚刚发布了回答，内容正在同步中。';
    return text.split(/\n+/).filter(Boolean);
  }, [state.draft_content]);

  const submitReply = () => {
    const value = reply.trim();
    if (!value) return;
    onSendComment(value);
    setReply('');
  };

  return (
    <div className="answer-detail-page">
      <Navbar
        notifications={notifications}
        onNotificationClick={() => {}}
        authUser={authUser}
        authLoading={authLoading}
        onLogin={onLogin}
        onLogout={onLogout}
      />
      <main className="answer-detail-shell">
        <section className="answer-question-card">
          <div className="question-topics">
            <span className="question-topic-tag">知乎A2A</span>
            <span className="question-topic-tag">学习成长</span>
          </div>
          <h1>{state.question_title}</h1>
          {state.question_desc && <p>{state.question_desc}</p>}
          <div className="answer-question-actions">
            <button className="zhihu-btn zhihu-btn-primary">关注问题</button>
            <button className="zhihu-btn zhihu-btn-ghost" onClick={onBackToEditor}>回到编辑器</button>
            <span>128 关注 · 3.2 万浏览</span>
          </div>
        </section>

        <section className="answer-content-card">
          <div className="answer-author-row">
            <div className="answer-avatar">我</div>
            <div>
              <div className="answer-author-name">Leila</div>
              <div className="answer-author-desc">知乎创作者 · A2A 创作协同体验中</div>
            </div>
          </div>

          <article className="published-answer">
            {answerParagraphs.map((paragraph, index) => (
              <p key={index}>{paragraph}</p>
            ))}
          </article>

          <div className="answer-actions-row">
            <button>赞同 128</button>
            <button>喜欢</button>
            <button>收藏</button>
            <button>分享</button>
            <button>更多</button>
          </div>
        </section>

        <section className="comments-card">
          <div className="comments-title-row">
            <h2>评论</h2>
            <span>{(firstComment ? 1 : 0) + state.comment_turns.length} 条互动</span>
          </div>

          <div className="direct-answer-bar">
            <div>
              <strong>直答追问</strong>
              <span> 发现这个回答还有 1 个读者可能会追问的点</span>
            </div>
            <div className="direct-answer-actions">
              <button onClick={() => setShowEvidence((v) => !v)}>查看依据</button>
              <button disabled={Boolean(firstComment) || isLoading}>生成追问</button>
            </div>
          </div>
          {showEvidence && (
            <div className="direct-answer-evidence">
              <div>回答缺口：没有进一步说明普通学生如何判断自己的优先级。</div>
              <div>关联参考：相似高赞回答通常会先拆学习目标、社交质量和复盘节奏。</div>
              <div>预计读者意图：希望得到可执行的排序方法，而不是泛泛建议。</div>
            </div>
          )}

          <div className="comment-composer">
            <input
              value={reply}
              onChange={(event) => setReply(event.target.value)}
              placeholder="写下你的回复..."
            />
            <button className="zhihu-btn zhihu-btn-primary" onClick={submitReply} disabled={!reply.trim()}>
              发送并生成下一轮
            </button>
          </div>

          {suggestion && (
            <div className="answerer-suggestion">
              <div>
                <strong>答主 Agent 建议</strong>
                <span>{suggestion}</span>
              </div>
              <button onClick={() => setReply(suggestion)}>采用</button>
            </div>
          )}

          <div className="comment-thread">
            {firstComment && (
              <CommentBlock
                author="提问者 小青"
                tag="Agent 对话"
                text={firstComment}
                time="刚刚"
              />
            )}
            {state.comment_turns.map((turn) => (
              <div key={turn.turn_number}>
                <CommentBlock author="我" text={turn.answerer_reply} time="刚刚" isMine />
                <CommentBlock author="提问者 小青" tag="继续追问" text={turn.asker_feedback} time="刚刚" />
              </div>
            ))}
            {!firstComment && (
              <div className="comments-empty">
                {isLoading ? '提问者侧 Agent 正在阅读回答...' : '发布后，提问者侧 Agent 的评论会出现在这里'}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function CommentBlock({
  author,
  tag,
  text,
  time,
  isMine = false,
}: {
  author: string;
  tag?: string;
  text: string;
  time: string;
  isMine?: boolean;
}) {
  return (
    <div className={`detail-comment ${isMine ? 'mine' : ''}`}>
      <div className="detail-comment-avatar">{isMine ? '我' : '青'}</div>
      <div className="detail-comment-main">
        <div className="detail-comment-meta">
          <strong>{author}</strong>
          {tag && <span>{tag}</span>}
          <time>{time}</time>
        </div>
        <p>{text}</p>
        <div className="detail-comment-actions">赞 · 回复 · 喜欢</div>
      </div>
    </div>
  );
}
