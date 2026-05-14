import { useEffect, useState } from 'react';
import { useDemo } from './hooks/useDemo';
import { useZhihuAuth } from './hooks/useZhihuAuth';
import Navbar from './components/Navbar';
import QuestionHeader from './components/QuestionHeader';
import Editor from './components/Editor';
import CreativeAssistant from './components/CreativeAssistant';
import AnswerDetailPage from './components/AnswerDetailPage';
import type { NotificationItem } from './types';

const DEFAULT_QUESTION_TITLE = '大学期间如何平衡学业、社交与个人成长？';
const DEFAULT_QUESTION_DESC = '想写一篇对普通大学生有参考价值的回答：不代写完整答案，只生成写作框架和互动预演。';
let hasBootstrappedDefaultDemo = false;

export default function App() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [view, setView] = useState<'editor' | 'answer'>('editor');
  const zhihuAuth = useZhihuAuth();
  const {
    state,
    isConnected,
    isLoading,
    error,
    startDemo,
    publishDraft,
    sendComment,
    setDraftContent,
  } = useDemo();

  useEffect(() => {
    if (hasBootstrappedDefaultDemo) return;
    hasBootstrappedDefaultDemo = true;
    startDemo(DEFAULT_QUESTION_TITLE, DEFAULT_QUESTION_DESC);
  }, [startDemo]);

  const notifications: NotificationItem[] = [
    ...(state.publish_feedback?.asker_comment
      ? [{
          id: 'first-feedback',
          tag: 'Agent 对话 · 直答追问',
          title: `提问者 小青 评论了你的回答「${state.question_title}」`,
          excerpt: state.publish_feedback.asker_comment,
          time: '刚刚',
        }]
      : []),
    ...state.comment_turns.map((turn) => ({
      id: `turn-${turn.turn_number}`,
      tag: '互动',
      title: '小青 回复了你在评论区的解释',
      excerpt: turn.asker_feedback,
      time: '刚刚',
    })),
  ];

  const handlePublish = () => {
    publishDraft(state.draft_content);
    setIsFullscreen(false);
    setView('answer');
  };

  if (view === 'answer') {
    return (
      <AnswerDetailPage
        state={state}
        isLoading={isLoading}
        notifications={notifications}
        authUser={zhihuAuth.user}
        authLoading={zhihuAuth.loading}
        onLogin={zhihuAuth.login}
        onLogout={zhihuAuth.logout}
        onBackToEditor={() => setView('editor')}
        onSendComment={sendComment}
      />
    );
  }

  if (isFullscreen) {
    return (
      <div className="fullscreen-editor">
        <div className="fullscreen-header">
          <div className="fullscreen-header-left">
            <span className="logo" style={{ color: 'var(--zhihu-blue)' }}>知乎</span>
            <span style={{ color: '#ccc' }}>|</span>
            <span>图文回答</span>
          </div>
          <button className="zhihu-btn-ghost" onClick={() => setIsFullscreen(false)}>
            退出全屏
          </button>
        </div>
        <div className="fullscreen-body">
          <div className="fullscreen-editor-area">
            <Editor
              state={state}
              isFullscreen={true}
              onDraftChange={setDraftContent}
              onPublish={handlePublish}
              onToggleFullscreen={() => setIsFullscreen(false)}
            />
          </div>
          <div className="fullscreen-sidebar">
            <CreativeAssistant
              state={state}
              isConnected={isConnected}
              isLoading={isLoading}
              error={error}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Navbar
        notifications={notifications}
        onNotificationClick={() => setView('answer')}
        authUser={zhihuAuth.user}
        authLoading={zhihuAuth.loading}
        onLogin={zhihuAuth.login}
        onLogout={zhihuAuth.logout}
      />
      <div className="main-content">
        <QuestionHeader state={state} />
        <div className="editor-layout">
          <div className="editor-main">
            <Editor
              state={state}
              isFullscreen={false}
              onDraftChange={setDraftContent}
              onPublish={handlePublish}
              onToggleFullscreen={() => setIsFullscreen(true)}
            />
          </div>
          <CreativeAssistant
            state={state}
            isConnected={isConnected}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}
