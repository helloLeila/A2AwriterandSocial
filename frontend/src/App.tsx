import { useState } from 'react';
import { useDemo } from './hooks/useDemo';
import Navbar from './components/Navbar';
import QuestionHeader from './components/QuestionHeader';
import Editor from './components/Editor';
import CreativeAssistant from './components/CreativeAssistant';
import QuestionModal from './components/QuestionModal';
import AnswerDetailPage from './components/AnswerDetailPage';
import type { NotificationItem } from './types';

export default function App() {
  const [showQuestionModal, setShowQuestionModal] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [view, setView] = useState<'editor' | 'answer'>('editor');
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

  const handleStart = (title: string, desc: string) => {
    setShowQuestionModal(false);
    setView('editor');
    startDemo(title, desc);
  };

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

  if (showQuestionModal) {
    return <QuestionModal onStart={handleStart} />;
  }

  if (view === 'answer') {
    return (
      <AnswerDetailPage
        state={state}
        isLoading={isLoading}
        notifications={notifications}
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
      <Navbar notifications={notifications} onNotificationClick={() => setView('answer')} />
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
