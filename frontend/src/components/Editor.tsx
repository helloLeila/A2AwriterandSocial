import type { DemoSession } from '../types';

interface Props {
  state: DemoSession;
  isFullscreen: boolean;
  onDraftChange: (content: string) => void;
  onPublish: () => void;
  onToggleFullscreen: () => void;
}

const demoDraft = `我不建议把大学生活拆成“学习、社交、成长”三个互相抢时间的任务。

更现实的做法是先确认自己的主线：这学期最重要的能力是什么，哪些社交能帮我进入更好的信息环境，哪些成长只是看起来很忙。

我的建议是把学习当作底盘，把社交当作信息入口，把个人成长当作复盘机制。不要追求每天都平衡，而是以两周为单位调整节奏。`;

export default function Editor({ state, isFullscreen, onDraftChange, onPublish, onToggleFullscreen }: Props) {
  const isPublished = state.phase === 'published' || state.phase === 'feedback_ready' || state.phase === 'commenting';
  const toolbarItems = ['撤销', '重做', '清除格式', '标题', '加粗', '斜体', '列表', '目录', '引用', '分割线', '代码块', '注释', '图片', '视频', '链接', '收益', '公式', '表格', '附件', '导入', '草稿备份', '更多'];

  return (
    <div className="editor-card" style={{ height: isFullscreen ? '100%' : 'auto', display: 'flex', flexDirection: 'column' }}>
      {/* Tabs */}
      <div className="editor-tabs">
        <div className="editor-tab active">图文回答</div>
        <div className="editor-tab" style={{ marginLeft: 'auto', cursor: 'pointer' }} onClick={onToggleFullscreen}>
          {isFullscreen ? '退出全屏' : '全屏编辑'}
        </div>
      </div>

      {/* Toolbar */}
      <div className="editor-toolbar">
        {toolbarItems.map((item) => (
          <button key={item} className="editor-toolbar-btn">{item}</button>
        ))}
        <span style={{ flex: 1 }} />
        <button
          className="editor-toolbar-btn"
          onClick={() => onDraftChange(demoDraft)}
          disabled={isPublished}
        >
          插入 Demo 草稿
        </button>
        <button className="editor-toolbar-btn primary">创作助手</button>
      </div>

      {/* Question title in editor */}
      <div className="editor-question-line">
        <div>{state.question_title}</div>
        <button>问题描述 ▾</button>
      </div>

      {/* Textarea */}
      <textarea
        className="editor-textarea"
        placeholder={isPublished ? '回答已发布' : '写回答...'}
        value={state.draft_content}
        onChange={(e) => onDraftChange(e.target.value)}
        disabled={isPublished}
        style={{ flex: 1, minHeight: isFullscreen ? 0 : 300 }}
      />

      {/* Footer */}
      <div className="editor-footer">
        <div className="editor-footer-left">
          <span>Markdown 语法输入中</span>
          <span>字数：{state.draft_content.length}</span>
        </div>
        {!isPublished ? (
          <button
            className="zhihu-btn zhihu-btn-primary"
            onClick={onPublish}
            disabled={!state.draft_content.trim() || state.phase === 'fetching'}
          >
            发布回答
          </button>
        ) : (
          <span style={{ fontSize: 13, color: 'var(--zhihu-green)' }}>✅ 已模拟发布</span>
        )}
      </div>
    </div>
  );
}
