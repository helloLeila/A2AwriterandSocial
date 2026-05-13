import { useState } from 'react';

interface Props {
  onStart: (title: string, desc: string) => void;
}

const PRESETS = [
  '大学期间如何平衡学业、社交与个人成长？',
  '作为职场新人，如何快速建立专业形象？',
  '如何培养深度思考的能力？',
  '在AI时代，个人如何保持竞争力？',
];

export default function QuestionModal({ onStart }: Props) {
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');

  return (
    <div className="question-modal-overlay">
      <div className="question-modal">
        <h2>A2A 社交创作助手</h2>
        <p style={{ fontSize: 13, color: 'var(--zhihu-text-secondary)', marginBottom: 16 }}>
          输入一个知乎问题，开启A2A社交预演与创作参谋
        </p>

        <input
          placeholder="问题标题"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          placeholder="问题描述（可选）"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
        />

        <div style={{ marginBottom: 12 }}>
          <p style={{ fontSize: 12, color: 'var(--zhihu-text-secondary)', marginBottom: 8 }}>
            快速选择热门问题：
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {PRESETS.map((p, i) => (
              <div
                key={i}
                style={{
                  padding: '8px 12px',
                  border: '1px solid var(--zhihu-border)',
                  borderRadius: 6,
                  fontSize: 13,
                  cursor: 'pointer',
                }}
                onClick={() => setTitle(p)}
              >
                {p}
              </div>
            ))}
          </div>
        </div>

        <div className="question-modal-actions">
          <button
            className="zhihu-btn zhihu-btn-primary"
            onClick={() => title.trim() && onStart(title.trim(), desc.trim())}
            disabled={!title.trim()}
          >
            开始A2A分析
          </button>
        </div>
      </div>
    </div>
  );
}
