import { useCallback, useEffect, useRef, useState } from 'react';
import type { DemoSession, DemoPhase, StreamMessage, CommentTurn } from '../types';

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
  const eventSourceRef = useRef<EventSource | null>(null);

  const startDemo = useCallback(async (questionTitle: string, questionDesc: string = '') => {
    setError(null);
    setIsLoading(true);
    setState({ ...initialState, question_title: questionTitle, question_desc: questionDesc });

    try {
      const res = await fetch('/api/demo/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_title: questionTitle, question_desc: questionDesc }),
      });

      if (!res.ok) {
        setError('创建会话失败');
        setIsLoading(false);
        return;
      }

      const data = await res.json();
      const sessionId = data.session_id;
      setState((prev) => ({ ...prev, session_id: sessionId }));

      const events = new EventSource(`/api/demo/session/${sessionId}/events`);
      eventSourceRef.current = events;

      events.onopen = () => {
        setIsConnected(true);
      };

      events.onmessage = (event) => {
        const msg: StreamMessage = JSON.parse(event.data);
        handleStreamMessage(msg);
      };

      events.onerror = () => {
        setError('SSE 事件流连接错误');
        setIsConnected(false);
        setIsLoading(false);
        events.close();
      };

      [
        'connected',
        'profile_fetching',
        'profiling',
        'answerer_profile_ready',
        'asker_profile_ready',
        'research_ready',
        'debate_round',
        'strategy_ready',
        'publish_feedback_ready',
        'comment_turn_ready',
        'error',
      ].forEach((type) => {
        events.addEventListener(type, (event) => {
          const msg: StreamMessage = JSON.parse((event as MessageEvent).data);
          handleStreamMessage(msg);
        });
      });
    } catch (e) {
      setError('连接失败: ' + String(e));
      setIsLoading(false);
    }
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
          setIsLoading(false);
          eventSourceRef.current?.close();
          setIsConnected(false);
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
    if (!state.session_id) return;

    // 1. 立即更新UI，用户1秒内看到反馈
    setState((prev) => ({
      ...prev,
      phase: 'published',
      draft_content: draftContent,
    }));

    // 2. 异步调用后端生成Agent反馈
    setIsLoading(true);
    try {
      const res = await fetch(`/api/demo/session/${state.session_id}/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ draft_content: draftContent }),
      });
      const data = await res.json();
      if (data.feedback) {
        setState((prev) => ({
          ...prev,
          phase: 'feedback_ready',
          publish_feedback: data.feedback as DemoSession['publish_feedback'],
        }));
      }
    } catch (e) {
      setError('发布失败: ' + String(e));
    } finally {
      setIsLoading(false);
    }
  }, [state.session_id]);

  const sendComment = useCallback(async (reply: string) => {
    if (!state.session_id) return;
    try {
      const res = await fetch(`/api/demo/session/${state.session_id}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answerer_reply: reply }),
      });
      const data = await res.json();
      if (data.turn) {
        setState((prev) => ({
          ...prev,
          comment_turns: [...prev.comment_turns, data.turn as CommentTurn],
        }));
      }
    } catch (e) {
      setError('评论失败: ' + String(e));
    }
  }, [state.session_id]);

  const setDraftContent = useCallback((content: string) => {
    setState((prev) => ({ ...prev, draft_content: content }));
  }, []);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
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
