import { useCallback, useEffect, useRef, useState } from 'react';
import type { DemoSession, DemoPhase, StreamMessage, StreamMessageType, CommentTurn } from '../types';
import { mockSession } from '../mocks/demoData';

const initialState: DemoSession = {
  session_id: '',
  phase: 'init',
  question_title: '',
  question_desc: '',
  debate_rounds: [],
  draft_content: '',
  comment_turns: [],
};

export function useDemo() {
  const [state, setState] = useState<DemoSession>(initialState);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startDemo = useCallback(async (questionTitle: string, questionDesc: string = '') => {
    setError(null);
    setIsLoading(true);
    setState({ ...initialState, question_title: questionTitle, question_desc: questionDesc });

    // 模拟 SSE 事件流：逐步展示分析过程
    setIsConnected(true);

    const events: Array<{ type: string; delay: number; payload: Record<string, unknown> }> = [
      { type: 'connected', delay: 200, payload: { message: '已连接' } },
      { type: 'profile_fetching', delay: 600, payload: { message: '正在拉取答主数据...' } },
      { type: 'answerer_profile_ready', delay: 1200, payload: { profile: mockSession.answerer_profile } },
      { type: 'asker_profile_ready', delay: 1800, payload: { profile: mockSession.asker_profile } },
      { type: 'research_ready', delay: 2400, payload: { research: mockSession.research } },
      ...mockSession.debate_rounds.map((round, i) => ({
        type: 'debate_round',
        delay: 3000 + i * 600,
        payload: { round, index: i },
      })),
      { type: 'strategy_ready', delay: 5000, payload: { strategy: mockSession.strategy } },
    ];

    events.forEach(({ type, delay, payload }) => {
      const t = setTimeout(() => {
        handleStreamMessage({ type: type as StreamMessageType, payload, timestamp: new Date().toISOString() });
      }, delay);
      if (type === 'strategy_ready') {
        timerRef.current = t;
      }
    });

    // 5.5秒后结束 loading
    const loadingTimer = setTimeout(() => {
      setIsLoading(false);
      setIsConnected(false);
    }, 5500);
    timerRef.current = loadingTimer;
  }, []);

  const handleStreamMessage = useCallback((msg: StreamMessage) => {
    const { type, payload } = msg;

    setState((prev) => {
      const next = { ...prev };

      switch (type) {
        case 'connected':
          next.phase = 'fetching';
          break;

        case 'profile_fetching':
          next.phase = 'fetching';
          break;

        case 'profiling':
          next.phase = 'profiling';
          break;

        case 'answerer_profile_ready':
          next.phase = 'profiling';
          next.answerer_profile = (payload.profile as unknown as DemoSession['answerer_profile']) || undefined;
          break;

        case 'asker_profile_ready':
          next.asker_profile = (payload.profile as unknown as DemoSession['asker_profile']) || undefined;
          break;

        case 'research_ready':
          next.research = (payload.research as unknown as DemoSession['research']) || undefined;
          break;

        case 'debate_round': {
          const round = payload.round as unknown as DemoSession['debate_rounds'][0];
          if (round) {
            next.debate_rounds = [...next.debate_rounds, round];
          }
          next.phase = 'debating';
          break;
        }

        case 'strategy_ready':
          next.phase = 'strategy_ready';
          next.strategy = (payload.strategy as unknown as DemoSession['strategy']) || undefined;
          break;

        case 'publish_feedback_ready':
          next.phase = 'feedback_ready';
          next.publish_feedback = (payload.feedback as unknown as DemoSession['publish_feedback']) || undefined;
          break;

        case 'comment_turn_ready': {
          const turn = payload.turn as unknown as CommentTurn;
          if (turn) {
            next.comment_turns = [...next.comment_turns, turn];
          }
          next.phase = 'commenting';
          break;
        }

        case 'error':
          next.phase = 'error';
          setError((payload.message as string) || '未知错误');
          setIsLoading(false);
          break;
      }

      return next;
    });
  }, []);

  const publishDraft = useCallback(async (draftContent: string) => {
    // 模拟发布：直接返回 mock 反馈
    setState((prev) => ({
      ...prev,
      phase: 'published',
      draft_content: draftContent,
    }));

    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 800));

    setState((prev) => ({
      ...prev,
      phase: 'feedback_ready',
      publish_feedback: mockSession.publish_feedback,
    }));
    setIsLoading(false);
  }, []);

  const sendComment = useCallback(async (reply: string) => {
    // 模拟评论互动：返回 mock 回复
    const turn = {
      turn_number: (state.comment_turns?.length || 0) + 1,
      answerer_reply: reply,
      asker_feedback: mockSession.comment_turns[0]?.asker_feedback || '谢谢回复！我还有其他问题想问...',
    };

    setState((prev) => ({
      ...prev,
      comment_turns: [...prev.comment_turns, turn as CommentTurn],
      phase: 'commenting',
    }));
  }, [state.comment_turns]);

  const setDraftContent = useCallback((content: string) => {
    setState((prev) => ({ ...prev, draft_content: content }));
  }, []);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  return {
    state,
    isConnected,
    isLoading,
    error,
    startDemo,
    publishDraft,
    sendComment,
    setDraftContent,
  };
}
