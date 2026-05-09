'use client';

/**
 * @file OrphanCoachPanel — 蘇格拉底 AI 教練對話面板（#9 Orphan 節點）
 *
 * 功能：
 * - mount 時先查詢現存對話（findExisting），避免重複建立 session
 * - 若有現存對話則 getConversation 恢復；否則 startConversation 啟動
 * - 訊息氣泡：user 右側 emerald、AI 左側 violet
 * - 頂部進度條：第 X 輪 / 8 輪，第 6 輪後轉 amber 警示
 * - 結束 CTA 依 status 渲染：positive_close / transfer_book /
 *   switch_to_question / force_end
 * - 配額不足（402）顯示升級引導
 * - 嚴禁顯示答案；輸入框限 500 字
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { Send, BookOpen, Brain, RotateCcw, X } from 'lucide-react';
import { orphanCoachService } from '@/lib/api/services';
import type {
  CoachStatus,
  OrphanCoachMessage,
  CoachRoundScores,
  CoachBookRecommendation,
} from '@/types/api';
import SocraticBadge from './SocraticBadge';
import CoachQuotaBanner from './CoachQuotaBanner';

// ─── 內部型別 ──────────────────────────────────────────────────

interface PanelMessage {
  role: 'user' | 'assistant';
  text: string;
  scores?: CoachRoundScores;
}

interface QuotaErrorState {
  used: number;
  quota: number;
}

// ─── Props ────────────────────────────────────────────────────

export interface OrphanCoachPanelProps {
  /** 知識節點 UUID */
  nodeId: string;
  /** 節點顯示名稱 */
  nodeName: string;
  /** 關閉面板的回呼（選用） */
  onClose?: () => void;
  /** 切到答題流程的回呼（status === 'switch_to_question' 時觸發） */
  onSwitchToQuestion?: (questionId: string) => void;
}

// ─── 工具函式 ─────────────────────────────────────────────────

function ScoreChip({ label, value }: { label: string; value: number }) {
  const ok = value >= 0.5;
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-[9px] px-1 py-0.5 rounded border ${
        ok
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
          : 'bg-slate-50 text-slate-400 border-slate-200'
      }`}
    >
      {ok ? '✓' : '○'} {label}
    </span>
  );
}

function RoundProgressBar({ current, max }: { current: number; max: number }) {
  const pct = Math.min((current / max) * 100, 100);
  const isWarning = current >= 6;
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 border-b border-violet-100 bg-violet-50/50 shrink-0">
      <span className="text-[10px] text-violet-600 font-medium whitespace-nowrap">
        第 {current} 輪 / 最多 {max} 輪
      </span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isWarning ? 'bg-amber-400' : 'bg-violet-400'
          }`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {isWarning && (
        <span className="text-[9px] text-amber-600 font-semibold whitespace-nowrap">接近上限</span>
      )}
    </div>
  );
}

function MasteryDisclaimer() {
  return (
    <div className="mx-3 mb-2 px-2 py-1.5 rounded bg-violet-50 border border-violet-200 text-[10px] text-violet-600 leading-relaxed">
      此對話 mastery 計入 40%，建議再答考古題鞏固。
    </div>
  );
}

// ─── 結束 CTA 區 ─────────────────────────────────────────────

interface EndCtaProps {
  status: CoachStatus;
  nodeId: string;
  bookRecommendation?: CoachBookRecommendation;
  transitionQuestionId?: string;
  onSwitchToQuestion?: (questionId: string) => void;
  onRestart: () => void;
}

function EndCta({
  status,
  nodeId,
  bookRecommendation,
  transitionQuestionId,
  onSwitchToQuestion,
  onRestart,
}: EndCtaProps) {
  if (status === 'continuing') return null;

  return (
    <div className="mx-3 mb-3 p-3 rounded-xl border bg-white shadow-sm">
      {status === 'positive_close' && (
        <>
          <p className="text-xs font-semibold text-emerald-700 mb-2">
            思考方向很到位！繼續鞏固這個概念
          </p>
          <MasteryDisclaimer />
          <div className="flex flex-wrap gap-2">
            <Link
              href={`/practice?nodeId=${nodeId}`}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-500 text-white rounded-lg text-xs font-semibold hover:bg-emerald-600 transition-colors"
            >
              <Brain className="h-3.5 w-3.5" />
              去答考古題
            </Link>
            <Link
              href={`/knowledge?tab=material`}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-violet-100 text-violet-700 rounded-lg text-xs font-semibold hover:bg-violet-200 transition-colors border border-violet-200"
            >
              <BookOpen className="h-3.5 w-3.5" />
              看 AI 補洞鷹架
            </Link>
          </div>
        </>
      )}

      {status === 'transfer_book' && bookRecommendation && (
        <>
          <p className="text-xs font-semibold text-amber-700 mb-1">建議參考教材</p>
          <div className="p-2 rounded bg-amber-50 border border-amber-200 mb-2">
            <p className="text-xs text-amber-800 font-medium">
              《{bookRecommendation.title}》
            </p>
            <p className="text-[11px] text-amber-600">第 {bookRecommendation.chapter} 章</p>
          </div>
          <MasteryDisclaimer />
          <button
            onClick={onRestart}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-amber-500 text-white rounded-lg text-xs font-semibold hover:bg-amber-600 transition-colors"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            看完後再試一次
          </button>
        </>
      )}

      {status === 'switch_to_question' && (
        <>
          <p className="text-xs font-semibold text-blue-700 mb-2">
            你已有基礎了！來一道考古題測試看看
          </p>
          <MasteryDisclaimer />
          <button
            onClick={() => transitionQuestionId && onSwitchToQuestion?.(transitionQuestionId)}
            disabled={!transitionQuestionId}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs font-semibold hover:bg-blue-600 transition-colors disabled:opacity-50"
          >
            <Brain className="h-3.5 w-3.5" />
            開始答題
          </button>
        </>
      )}

      {status === 'force_end' && (
        <>
          <p className="text-xs font-semibold text-slate-700 mb-1">
            今日探索到這裡，改天繼續
          </p>
          <p className="text-[11px] text-slate-500 mb-2">
            8 輪探索已完成。下次進入此節點可自動接續對話。
          </p>
          <MasteryDisclaimer />
          <div className="flex gap-2">
            <Link
              href={`/practice?nodeId=${nodeId}`}
              className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-500 text-white rounded-lg text-xs font-semibold hover:bg-slate-600 transition-colors"
            >
              <Brain className="h-3.5 w-3.5" />
              去答考古題
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

// ─── 主元件 ──────────────────────────────────────────────────

export default function OrphanCoachPanel({
  nodeId,
  nodeName,
  onClose,
  onSwitchToQuestion,
}: OrphanCoachPanelProps) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<PanelMessage[]>([]);
  const [currentRound, setCurrentRound] = useState(0);
  const [status, setStatus] = useState<CoachStatus>('continuing');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [inputText, setInputText] = useState('');
  const [quotaError, setQuotaError] = useState<QuotaErrorState | null>(null);
  const [bookRecommendation, setBookRecommendation] = useState<CoachBookRecommendation | undefined>();
  const [transitionQuestionId, setTransitionQuestionId] = useState<string | undefined>();
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // ── 初始化：查現存對話或啟新對話 ────────────────────────────
  useEffect(() => {
    if (!nodeId) return;
    let cancelled = false;

    async function init() {
      setLoading(true);
      setInitError(null);
      setQuotaError(null);

      try {
        // Step 1: 查詢是否有現存對話
        const existing = await orphanCoachService.findExisting(nodeId);

        if (existing.existing_conversation_id && !cancelled) {
          // Step 2a: 恢復現存對話
          const conv = await orphanCoachService.getConversation(
            existing.existing_conversation_id
          );
          if (!cancelled) {
            setConversationId(existing.existing_conversation_id);
            setMessages(
              conv.messages.map(m => ({
                role: m.role,
                text: m.text,
                scores: m.scores,
              }))
            );
            setCurrentRound(conv.round_number);
            setStatus(conv.status);
          }
        } else if (!cancelled) {
          // Step 2b: 啟動新對話
          const res = await orphanCoachService.startConversation(nodeId);

          if ('error' in res && res.error) {
            // 402 配額不足
            setQuotaError({ used: res.used, quota: res.quota });
            return;
          }

          const started = res as import('@/types/api').OrphanCoachStartResponse;
          if (!cancelled) {
            setConversationId(started.conversation_id);
            setMessages([
              {
                role: 'assistant',
                text: started.opening_message,
              },
            ]);
            setCurrentRound(1);
            setStatus('continuing');
          }
        }
      } catch (e) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : '初始化失敗，請稍後再試';
          setInitError(msg);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    init();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId]);

  // ── 送出訊息 ────────────────────────────────────────────────
  const handleSend = async () => {
    const text = inputText.trim();
    if (!text || sending || status !== 'continuing' || !conversationId) return;

    setInputText('');
    setSending(true);

    // 即時顯示學生訊息
    setMessages(prev => [...prev, { role: 'user', text }]);

    try {
      const res = await orphanCoachService.sendMessage(conversationId, text);

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: res.assistant_reply,
          scores: res.scores,
        },
      ]);
      setCurrentRound(res.round_number);
      setStatus(res.status);

      if (res.book_recommendation) {
        setBookRecommendation(res.book_recommendation);
      }
      if (res.transition_question_id) {
        setTransitionQuestionId(res.transition_question_id);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : '傳送失敗，請稍後再試';
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: `⚠️ ${msg}` },
      ]);
    } finally {
      setSending(false);
    }
  };

  // ── 重啟對話 ─────────────────────────────────────────────────
  const handleRestart = async () => {
    setMessages([]);
    setCurrentRound(0);
    setStatus('continuing');
    setConversationId(null);
    setQuotaError(null);
    setInitError(null);
    setBookRecommendation(undefined);
    setTransitionQuestionId(undefined);
    setLoading(true);

    try {
      const res = await orphanCoachService.startConversation(nodeId);
      if ('error' in res && res.error) {
        setQuotaError({ used: res.used, quota: res.quota });
        return;
      }
      const started = res as import('@/types/api').OrphanCoachStartResponse;
      setConversationId(started.conversation_id);
      setMessages([{ role: 'assistant', text: started.opening_message }]);
      setCurrentRound(1);
      setStatus('continuing');
    } catch (e) {
      const msg = e instanceof Error ? e.message : '重啟失敗';
      setInitError(msg);
    } finally {
      setLoading(false);
    }
  };

  const isEnded = status !== 'continuing';
  const canSend = !sending && !loading && status === 'continuing' && !!conversationId;

  // ── 渲染 ─────────────────────────────────────────────────────
  return (
    <div className="h-full flex flex-col overflow-hidden bg-white">
      {/* Header */}
      <div className="px-3 py-2 border-b border-violet-200 bg-violet-50 shrink-0">
        <div className="flex items-center gap-2">
          <div className="flex flex-col min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-violet-800 truncate">
                AI 教練探索：{nodeName}
              </span>
              {onClose && (
                <button
                  onClick={onClose}
                  className="shrink-0 p-0.5 rounded hover:bg-violet-200 transition-colors"
                  title="關閉"
                >
                  <X className="h-3.5 w-3.5 text-violet-500" />
                </button>
              )}
            </div>
            <SocraticBadge className="mt-0.5 self-start" />
          </div>
        </div>
      </div>

      {/* 進度條 */}
      {currentRound > 0 && (
        <RoundProgressBar current={currentRound} max={8} />
      )}

      {/* 配額 Banner */}
      {quotaError && (
        <CoachQuotaBanner
          used={quotaError.used}
          quota={quotaError.quota}
          isBlocked
        />
      )}

      {/* 訊息區 */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="flex flex-col items-center gap-2">
              <div className="w-5 h-5 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-violet-500">AI 教練準備中...</span>
            </div>
          </div>
        )}

        {initError && !loading && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-center">
            <p className="text-xs text-rose-600 mb-2">{initError}</p>
            <button
              onClick={handleRestart}
              className="px-3 py-1 bg-rose-500 text-white rounded-lg text-xs font-semibold hover:bg-rose-600"
            >
              重試
            </button>
          </div>
        )}

        {quotaError && !loading && (
          <div className="px-3 py-6 text-center">
            <span className="text-4xl">📊</span>
            <p className="text-xs text-slate-600 mt-2 mb-1">
              本月蘇格拉底對話配額已滿（{quotaError.used} / {quotaError.quota} 次）
            </p>
            <p className="text-[11px] text-slate-400 mb-3">
              升級方案可獲得更多次數
            </p>
            <Link
              href="/account"
              className="inline-flex items-center gap-1 px-4 py-2 bg-violet-500 text-white rounded-lg text-xs font-bold hover:bg-violet-600 transition-colors"
            >
              升級方案
            </Link>
          </div>
        )}

        {!loading && !quotaError && messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* 頭像 */}
            <div
              className={`h-6 w-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold ${
                msg.role === 'assistant'
                  ? 'bg-violet-100 text-violet-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}
            >
              {msg.role === 'assistant' ? '🧠' : 'U'}
            </div>

            {/* 訊息氣泡 */}
            <div className="max-w-[85%] flex flex-col gap-1">
              <div
                className={`p-2.5 rounded-xl text-xs leading-relaxed ${
                  msg.role === 'assistant'
                    ? 'bg-violet-50 border border-violet-200 text-violet-900 rounded-tl-none'
                    : 'bg-emerald-500 text-white rounded-tr-none whitespace-pre-line'
                }`}
              >
                {msg.text}
              </div>

              {/* 評分標示（僅 AI 回覆有 scores，顯示在氣泡下方） */}
              {msg.role === 'assistant' && msg.scores && (
                <div className="flex flex-wrap gap-1 pl-1">
                  <ScoreChip label="概念" value={msg.scores.concept} />
                  <ScoreChip label="推理" value={msg.scores.reasoning} />
                  <ScoreChip label="主動" value={msg.scores.initiative} />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* 送出中 loading 氣泡 */}
        {sending && (
          <div className="flex gap-2">
            <div className="h-6 w-6 rounded-full bg-violet-100 flex items-center justify-center shrink-0 text-[10px]">
              🧠
            </div>
            <div className="bg-violet-50 border border-violet-200 p-2.5 rounded-xl rounded-tl-none">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 bg-violet-300 rounded-full animate-bounce" />
                <div className="w-1.5 h-1.5 bg-violet-300 rounded-full animate-bounce [animation-delay:0.1s]" />
                <div className="w-1.5 h-1.5 bg-violet-300 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 結束 CTA */}
      {isEnded && !loading && (
        <EndCta
          status={status}
          nodeId={nodeId}
          bookRecommendation={bookRecommendation}
          transitionQuestionId={transitionQuestionId}
          onSwitchToQuestion={onSwitchToQuestion}
          onRestart={handleRestart}
        />
      )}

      {/* 輸入框 */}
      {!quotaError && !loading && (
        <div className="px-3 pb-3 shrink-0">
          {isEnded && (
            <div className="mb-2 px-2 py-1 rounded bg-slate-50 border border-slate-200 text-center">
              <span className="text-[11px] text-slate-400">對話已結束</span>
            </div>
          )}
          <div className="relative">
            <textarea
              value={inputText}
              onChange={e => {
                // 限制 500 字
                if (e.target.value.length <= 500) setInputText(e.target.value);
              }}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                isEnded
                  ? '對話已結束'
                  : !conversationId
                  ? '等待連接...'
                  : '輸入你的想法（Enter 送出，Shift+Enter 換行）'
              }
              disabled={!canSend}
              rows={2}
              className="w-full pl-3 pr-10 py-2 rounded-xl border border-violet-200 bg-white focus:outline-none focus:ring-2 focus:ring-violet-400 text-xs resize-none disabled:opacity-50 disabled:bg-slate-50"
            />
            <div className="absolute bottom-2 right-2 flex items-center gap-1">
              {inputText.length > 400 && (
                <span className="text-[9px] text-amber-500">{inputText.length}/500</span>
              )}
              <button
                onClick={handleSend}
                disabled={!canSend || !inputText.trim()}
                className="h-6 w-6 bg-violet-500 text-white rounded-lg flex items-center justify-center hover:bg-violet-600 transition-colors disabled:opacity-40"
              >
                <Send className="h-3 w-3" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
