import { useState, useEffect } from 'react';
import type { DemoSession, DemoPhase } from '../types';
import { useInView } from '../hooks/useInView';

interface Props {
  state: DemoSession;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

// ===== 渐入动画 =====
function FadeIn({ children, delay = 0, active = true }: { children: React.ReactNode; delay?: number; active?: boolean }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!active) return;
    const t = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(t);
  }, [delay, active]);
  return (
    <div style={{
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(6px)',
      transition: 'all 0.35s ease',
    }}>
      {children}
    </div>
  );
}

// ===== 知乎风格标签（4-6px圆角） =====
function Tag({ children, color = 'blue' }: { children: React.ReactNode; color?: 'blue' | 'green' | 'red' | 'gray' }) {
  const colorMap = {
    blue:  { bg: '#F0F7FF', text: '#0066FF', border: '#D6E4FF' },
    green: { bg: '#F0F9F4', text: '#0D7D3C', border: '#C8E6D4' },
    red:   { bg: '#FFF2F0', text: '#CF1322', border: '#FFCCC7' },
    gray:  { bg: '#F5F5F5', text: '#595959', border: '#D9D9D9' },
  };
  const c = colorMap[color];
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', fontSize: 11, fontWeight: 400,
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      borderRadius: 4, margin: '2px 4px 2px 0', lineHeight: 1.45,
      maxWidth: '100%', whiteSpace: 'normal',
    }}>
      {children}
    </span>
  );
}

// ===== 解析结构化参考素材 =====
function parseReference(link: string) {
  const parts = link.split('｜');
  return {
    title: extract(parts[0], '标题'),
    source: extract(parts[1], '来源'),
    url: extract(parts[2], '链接'),
    summary: extract(parts[3], '摘要'),
    usefulFor: extract(parts[4], '可借鉴'),
    risk: extract(parts[5], '风险'),
  };
}
function extract(part: string | undefined, key: string) {
  if (!part) return '';
  return part.replace(new RegExp(`^${key}[:：]`), '').trim();
}

function ReferenceCard({ link }: { link: string }) {
  const ref = parseReference(link);
  return (
    <div style={{ marginBottom: 8, padding: 8, background: '#FAFAFA', borderRadius: 6, border: '1px solid #E8E8E8' }}>
      <div style={{ fontSize: 12, fontWeight: 500, marginBottom: 2, lineHeight: 1.45 }}>
        {ref.url ? (
          <a href={ref.url} target="_blank" rel="noopener noreferrer" style={{ color: '#0066FF', textDecoration: 'none' }}>
            {ref.title || ref.url}
          </a>
        ) : (
          <span style={{ color: '#121212' }}>{ref.title || link}</span>
        )}
      </div>
      {ref.source && <div style={{ fontSize: 11, color: '#999', marginBottom: 2 }}>来源：{ref.source}</div>}
      {ref.summary && <div style={{ fontSize: 11, color: '#666', lineHeight: 1.5 }}>{ref.summary}</div>}
      {ref.usefulFor && (
        <div style={{ marginTop: 3, fontSize: 11, color: '#0D7D3C', lineHeight: 1.45 }}>
          <strong>可借鉴：</strong>{ref.usefulFor}
        </div>
      )}
      {ref.risk && (
        <div style={{ marginTop: 2, fontSize: 11, color: '#CF1322', lineHeight: 1.45 }}>
          <strong>风险：</strong>{ref.risk}
        </div>
      )}
    </div>
  );
}

// ===== 从 debate_rounds 提取摘要 =====
function buildDebateSummary(rounds: DemoSession['debate_rounds']): string {
  if (rounds.length === 0) return '';
  return rounds.map(r => {
    const label = r.agent_name.includes('答主') ? '答主' : r.agent_name.includes('提问者') ? '提问者' : '全网';
    const text = r.stance.slice(0, 40) + (r.stance.length > 40 ? '...' : '');
    return `${label}${text}`;
  }).join('；');
}

export default function CreativeAssistant({ state, isLoading, error }: Props) {
  const [inA2A, setInA2A] = useState(false);
  const [a2aTab, setA2aTab] = useState<'align' | 'reference'>('align');
  const [debateExpanded, setDebateExpanded] = useState(false);

  const phase = state.phase;
  const hasStrategy = ['strategy_ready', 'drafting', 'published', 'feedback_ready', 'commenting'].includes(phase);

  // 小圆桌滚动到视口才触发动画
  const { ref: debateRef, isInView: debateInView } = useInView(0.1);

  // A2A 入口状态文案
  const a2aStatusText = (() => {
    if (phase === 'strategy_ready') return '✅ 策略已就绪';
    if (isLoading) return '⏳ 画像生成中...';
    return '👉 开始分析';
  })();

  // ===== 首页 =====
  if (!inA2A) {
    return (
      <div className="creative-assistant">
        <div className="ca-header">
          <span>创作助手</span>
          <span style={{ fontSize: 12, color: 'var(--zhihu-text-secondary)' }}>✕</span>
        </div>
        <div className="ca-body">
          <div className="ca-welcome">Hello，欢迎使用知乎创作助手，你可选择以下功能辅助创作更优质的内容</div>

          {/* A2A 创作协同入口卡片 */}
          <div className="ca-a2a-card" onClick={() => setInA2A(true)}>
            <div className="ca-a2a-title">A2A 创作协同</div>
            <div className="ca-a2a-desc">基于你的关注流、提问者画像和全网语境，对齐问题意图、参考语境和发布后的互动承接</div>
            <div className="ca-a2a-status">{a2aStatusText}</div>
          </div>

          <div className="ca-grid">
            {['🔍 内容检测', '✨ 智能排版', '📝 提取导语', '🖼️ AI配图'].map((item, i) => (
              <div key={i} className="ca-card"><div className="ca-card-title">{item}</div></div>
            ))}
          </div>

          {error && (
            <div style={{ marginTop: 10, padding: 10, background: '#FFF2F0', borderRadius: 6, fontSize: 12, color: '#CF1322' }}>
              {error}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ===== A2A 子面板 =====
  return (
    <div className="creative-assistant">
      <div className="ca-header">
        <span style={{ cursor: 'pointer', fontSize: 13, color: 'var(--zhihu-text-secondary)' }} onClick={() => setInA2A(false)}>← 返回全部功能</span>
        <span style={{ fontSize: 15, fontWeight: 600 }}>创作助手</span>
        <span style={{ fontSize: 12, color: 'var(--zhihu-text-secondary)' }}>✕</span>
      </div>

      <div className="ca-body">
        {/* 次级标题 */}
        <div style={{ fontSize: 14, fontWeight: 600, color: '#121212', marginBottom: 8 }}>A2A 创作协同</div>

        {/* 两段式 Tab */}
        <div style={{ display: 'flex', gap: 2, marginBottom: 10, borderBottom: '1px solid #EBEBEB', paddingBottom: 6 }}>
          {[
            { key: 'align' as const, label: '写前对齐' },
            { key: 'reference' as const, label: '参考素材' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setA2aTab(tab.key)}
              style={{
                padding: '5px 10px', fontSize: 12, border: 'none', background: 'none',
                cursor: 'pointer', borderRadius: 4,
                color: a2aTab === tab.key ? '#0066FF' : '#8590A6',
                fontWeight: a2aTab === tab.key ? 600 : 400,
                backgroundColor: a2aTab === tab.key ? '#F0F7FF' : 'transparent',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ===== 写前对齐 ===== */}
        {a2aTab === 'align' && (
          <div>
            {/* 进度 */}
            {isLoading && phase !== 'strategy_ready' && (
              <FadeIn>
                <div style={{ marginBottom: 10, padding: 8, background: '#FAFAFA', borderRadius: 6, border: '1px solid #EBEBEB' }}>
                  <ProgressStep label="答主画像" phase={phase} target="fetching" />
                  <ProgressStep label="提问者画像" phase={phase} target="profiling" />
                  <ProgressStep label="全网语境" phase={phase} target="profiling" />
                  <ProgressStep label="三方互搏" phase={phase} target="debating" />
                  <ProgressStep label="策略生成" phase={phase} target="strategy_ready" />
                </div>
              </FadeIn>
            )}

            {/* 写作策略 — 置顶，最轻量 */}
            {state.strategy && (
              <FadeIn delay={100}>
                <div style={{ marginBottom: 10, padding: 10, background: '#fff', border: '1px solid #C8E6D4', borderRadius: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#0D7D3C', marginBottom: 8 }}>写作策略</div>

                  {/* 主切入 */}
                  <div style={{ marginBottom: 8 }}>
                    <div style={{ fontSize: 11, color: '#0D7D3C', fontWeight: 500, marginBottom: 3 }}>建议切入角度</div>
                    <div style={{ fontSize: 12, color: '#121212', lineHeight: 1.6 }}>
                      {state.strategy.recommended_angles?.slice(0, 2).join('；')}
                    </div>
                  </div>

                  {/* 避坑 */}
                  {state.strategy.avoid_angles && state.strategy.avoid_angles.length > 0 && (
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ fontSize: 11, color: '#CF1322', fontWeight: 500, marginBottom: 3 }}>别踩的坑</div>
                      <div>{state.strategy.avoid_angles.slice(0, 3).map((t, i) => <Tag key={i} color="red">{t}</Tag>)}</div>
                    </div>
                  )}

                  {/* 发布后追问 */}
                  {state.strategy.likely_followup && (
                    <div>
                      <div style={{ fontSize: 11, color: '#0066FF', fontWeight: 500, marginBottom: 3 }}>发布后最可能被追问</div>
                      <div style={{ fontSize: 12, color: '#444' }}>{state.strategy.likely_followup}</div>
                    </div>
                  )}
                </div>
              </FadeIn>
            )}

            {/* 答主画像 */}
            {state.answerer_profile && (
              <FadeIn delay={150}>
                <div style={{ marginBottom: 8, padding: 10, background: '#FAFAFA', border: '1px solid #E8E8E8', borderRadius: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>答主画像</div>
                  <div style={{ marginBottom: 4 }}>{state.answerer_profile.content_interests?.map((t, i) => <Tag key={i} color="blue">{t}</Tag>)}</div>
                  <div style={{ fontSize: 12, color: '#444', lineHeight: 1.6 }}>
                    <div><strong style={{ color: '#0066FF' }}>受众期待：</strong>{state.answerer_profile.audience_expectation}</div>
                    <div style={{ marginTop: 2 }}><strong style={{ color: '#0066FF' }}>表达风格：</strong>{state.answerer_profile.expression_style}</div>
                    <div style={{ marginTop: 4, padding: 6, background: '#fff', borderRadius: 4, border: '1px solid #D6E4FF' }}>
                      <strong style={{ color: '#0066FF', fontSize: 11 }}>切入建议</strong>
                      <div style={{ marginTop: 2, fontSize: 12, color: '#444', lineHeight: 1.6 }}>{state.answerer_profile.suitable_angle}</div>
                      {state.answerer_profile.angle_reference_links && state.answerer_profile.angle_reference_links.length > 0 && (
                        <div style={{ marginTop: 6 }}>
                          <div style={{ fontSize: 11, color: '#8590A6', marginBottom: 3 }}>支撑文章</div>
                          {state.answerer_profile.angle_reference_links.slice(0, 2).map((link, i) => {
                            const ref = parseReference(link);
                            return (
                              <div key={i} style={{ fontSize: 11, lineHeight: 1.5, marginBottom: 3 }}>
                                {ref.url ? (
                                  <a href={ref.url} target="_blank" rel="noopener noreferrer" style={{ color: '#0066FF', textDecoration: 'none' }}>
                                    {ref.title || ref.url}
                                  </a>
                                ) : (
                                  <span style={{ color: '#595959' }}>{ref.title || link}</span>
                                )}
                                {ref.source && <span style={{ color: '#999' }}> · {ref.source}</span>}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                  <div style={{ marginTop: 4 }}>{state.answerer_profile.experience_boundary?.map((t, i) => <Tag key={i} color="red">🚫 {t}</Tag>)}</div>
                </div>
              </FadeIn>
            )}

            {/* 提问者画像 — 蓝灰体系 */}
            {state.asker_profile && (
              <FadeIn delay={200}>
                <div style={{ marginBottom: 8, padding: 10, background: '#FAFAFA', border: '1px solid #E8E8E8', borderRadius: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>
                    提问者画像 · {state.asker_profile.asker_type === 'anxious' ? '焦虑求助型' : state.asker_profile.asker_type === 'skeptical' ? '理性质疑型' : '经验补充型'}
                  </div>
                  {state.asker_profile.real_confusion && (
                    <div style={{ marginBottom: 6, padding: 6, background: '#fff', borderRadius: 4, border: '1px solid #D6E4FF' }}>
                      <div style={{ fontSize: 11, fontWeight: 500, color: '#0066FF', marginBottom: 2 }}>真实困惑</div>
                      <div style={{ fontSize: 12, color: '#444', lineHeight: 1.6 }}>{state.asker_profile.real_confusion}</div>
                    </div>
                  )}
                  {state.asker_profile.hot_answer_angles && state.asker_profile.hot_answer_angles.length > 0 && (
                    <>
                      <div style={{ marginBottom: 2 }}><strong style={{ color: '#595959', fontSize: 11 }}>高赞思路：</strong></div>
                      <div style={{ marginBottom: 4 }}>{state.asker_profile.hot_answer_angles.map((t, i) => <Tag key={i} color="gray">{t}</Tag>)}</div>
                    </>
                  )}
                  <div style={{ marginBottom: 2 }}><strong style={{ color: '#CF1322', fontSize: 11 }}>讨厌：</strong></div>
                  <div style={{ marginBottom: 4 }}>{state.asker_profile.hated_expressions?.map((t, i) => <Tag key={i} color="red">{t}</Tag>)}</div>
                  <div style={{ marginBottom: 2 }}><strong style={{ color: '#0D7D3C', fontSize: 11 }}>希望补充：</strong></div>
                  <div>{state.asker_profile.hoped_details?.map((t, i) => <Tag key={i} color="green">{t}</Tag>)}</div>
                </div>
              </FadeIn>
            )}

            {/* 全网语境 */}
            {state.research && (
              <FadeIn delay={250}>
                <div style={{ marginBottom: 8, padding: 10, background: '#FAFAFA', border: '1px solid #E8E8E8', borderRadius: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>全网语境</div>
                  <div style={{ marginBottom: 2 }}><strong style={{ color: '#CF1322', fontSize: 11 }}>已说烂：</strong></div>
                  <div style={{ marginBottom: 4 }}>{state.research.overused_angles?.map((t, i) => <Tag key={i} color="red">{t}</Tag>)}</div>
                  <div style={{ marginBottom: 2 }}><strong style={{ color: '#595959', fontSize: 11 }}>争议点：</strong></div>
                  <div style={{ marginBottom: 4 }}>{state.research.controversy_points?.map((t, i) => <Tag key={i} color="gray">{t}</Tag>)}</div>
                  <div style={{ marginBottom: 2 }}><strong style={{ color: '#CF1322', fontSize: 11 }}>风险表达：</strong></div>
                  <div>{state.research.risky_expressions?.map((t, i) => <Tag key={i} color="red">{t}</Tag>)}</div>
                </div>
              </FadeIn>
            )}

            {/* 互搏日志 — 放在写前对齐内，默认折叠 */}
            {state.debate_rounds.length > 0 && (
              <FadeIn delay={300}>
                <div style={{ marginBottom: 8, padding: 10, background: '#FAFAFA', border: '1px solid #E8E8E8', borderRadius: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>互搏日志</div>

                  {!debateExpanded && (
                    <>
                      <div style={{ fontSize: 12, color: '#444', lineHeight: 1.6, marginBottom: 8 }}>
                        <strong>结论：</strong>{buildDebateSummary(state.debate_rounds)}
                      </div>
                      <button
                        onClick={() => setDebateExpanded(true)}
                        style={{
                          width: '100%', padding: '8px', background: '#fff', border: '1px dashed #C0C0C0',
                          borderRadius: 6, fontSize: 12, color: '#666', cursor: 'pointer', textAlign: 'center',
                        }}
                      >
                        查看完整互搏过程 ↓
                      </button>
                    </>
                  )}

                  {debateExpanded && (
                    <div ref={debateRef} style={{ background: '#F5F5F5', borderRadius: 8, padding: 8 }}>
                      {state.debate_rounds.map((r, i) => (
                        <DebateBubble key={i} round={r} index={i} delay={debateInView ? i * 500 : 0} active={debateInView} />
                      ))}
                    </div>
                  )}
                </div>
              </FadeIn>
            )}

            {!hasStrategy && !isLoading && (
              <div className="ca-empty">点击「开始分析」后，将生成写前策略</div>
            )}
          </div>
        )}

        {/* ===== 参考素材 ===== */}
        {a2aTab === 'reference' && (
          <div>
            {state.answerer_profile?.angle_reference_links && state.answerer_profile.angle_reference_links.length > 0 && (
              <FadeIn delay={80}>
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>切入建议支撑文章</div>
                  {state.answerer_profile.angle_reference_links.map((link, i) => (
                    <ReferenceCard key={i} link={link} />
                  ))}
                </div>
              </FadeIn>
            )}

            {state.asker_profile?.reference_links && state.asker_profile.reference_links.length > 0 && (
              <FadeIn delay={100}>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>推荐阅读</div>
                  {state.asker_profile.reference_links.map((link, i) => (
                    <ReferenceCard key={i} link={link} />
                  ))}
                </div>
              </FadeIn>
            )}

            {state.research?.reference_materials && state.research.reference_materials.length > 0 && (
              <FadeIn delay={200}>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#121212', marginBottom: 6 }}>参考素材</div>
                  {state.research.reference_materials.map((mat, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#444', lineHeight: 1.6, padding: '3px 0', paddingLeft: 10, position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 0, color: '#999' }}>•</span>
                      {mat}
                    </div>
                  ))}
                  <div style={{ marginTop: 4, fontSize: 10, color: '#999', fontStyle: 'italic' }}>
                    以上素材仅供思路参考，请勿直接抄袭原文
                  </div>
                </div>
              </FadeIn>
            )}

            {!state.answerer_profile?.angle_reference_links?.length && !state.asker_profile?.reference_links?.length && !state.research?.reference_materials?.length && (
              <div className="ca-empty">分析完成后将展示参考素材</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ===== 微信风格辩论气泡 =====
function DebateBubble({ round, index, delay = 0, active = true }: {
  round: { round_number: number; agent_name: string; stance: string; risk_or_blindspot: string };
  index: number; delay?: number; active?: boolean;
}) {
  const isAnswerer = round.agent_name.includes('答主');
  const isAsker = round.agent_name.includes('提问者');
  const label = isAnswerer ? '答主' : isAsker ? '提问者' : '全网';
  const labelColor = isAnswerer ? '#0066FF' : isAsker ? '#595959' : '#0D7D3C';
  const roundLabel = round.round_number === 2 ? '反思' : '立论';

  return (
    <FadeIn delay={delay} active={active}>
      <div style={{
        display: 'flex', flexDirection: 'column',
        alignItems: isAnswerer ? 'flex-end' : 'flex-start',
        marginBottom: 10,
      }}>
        <div style={{ fontSize: 10, fontWeight: 500, color: labelColor, marginBottom: 2, opacity: 0.7 }}>
          {label} · {roundLabel}
        </div>
        <div style={{
          maxWidth: '92%', padding: '10px 14px',
          borderRadius: isAnswerer ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
          background: isAnswerer ? '#95EC69' : '#fff',
          border: isAnswerer ? 'none' : '1px solid #E8E8E8',
          fontSize: 12, lineHeight: 1.65, color: '#121212',
          boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
          wordBreak: 'break-word',
        }}>
          {round.stance && (
            <div style={{ marginBottom: round.risk_or_blindspot ? 6 : 0 }}>{round.stance}</div>
          )}
          {round.risk_or_blindspot && (
            <div style={{
              marginTop: 5, paddingTop: 5,
              borderTop: round.stance ? '1px dashed rgba(0,0,0,0.08)' : 'none',
              fontSize: 11, color: '#666', lineHeight: 1.55,
            }}>
              💡 {round.risk_or_blindspot}
            </div>
          )}
        </div>
      </div>
    </FadeIn>
  );
}

function ProgressStep({ label, phase, target }: { label: string; phase: DemoPhase; target: string }) {
  const order: DemoPhase[] = ['init', 'fetching', 'profiling', 'debating', 'strategy_ready'];
  const currentIdx = order.indexOf(phase);
  const targetIdx = order.indexOf(target as DemoPhase);
  let status: 'done' | 'active' | 'pending' = 'pending';
  if (currentIdx > targetIdx) status = 'done';
  else if (currentIdx === targetIdx) status = 'active';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8, padding: '3px 0', fontSize: 11,
      color: status === 'done' ? '#0D7D3C' : status === 'active' ? '#0066FF' : '#999',
      fontWeight: status === 'active' ? 600 : 400,
    }}>
      <span>{status === 'done' ? '✓' : status === 'active' ? '●' : '○'}</span>
      <span>{label}</span>
    </div>
  );
}
