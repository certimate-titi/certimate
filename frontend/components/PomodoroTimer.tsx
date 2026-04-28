/**
 * @file 番茄鐘倒數元件（Spec 21）— 純前端，localStorage 持久化。
 *
 * 顯示於測驗頁右上角，獨立於考試剩餘時間計時器：
 * - focus 階段（25/30/...分鐘）→ 結束提示「短休息」（不強制中斷）
 * - 每完成 N 個 focus → 提示「長休息」
 * - 短/長休息進度條也用同樣格式呈現
 *
 * 設計依 Spec 21 §「休息提醒為建議性質，不強制中斷測驗」。
 */
'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { Coffee, Sparkles, Settings, X } from 'lucide-react';

export interface PomodoroSettings {
  enabled: boolean;
  focus_min: number;
  short_break_min: number;
  long_break_min: number;
  long_break_interval: number; // 每 N 個 focus 後長休息
}

const DEFAULTS: PomodoroSettings = {
  enabled: false,
  focus_min: 25,
  short_break_min: 5,
  long_break_min: 15,
  long_break_interval: 4,
};

const STORAGE_KEY = 'certimate_pomodoro_settings';

export function loadSettings(): PomodoroSettings {
  if (typeof window === 'undefined') return DEFAULTS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return DEFAULTS;
  }
}

export function saveSettings(s: PomodoroSettings) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

interface PomodoroTimerProps {
  /** 考試總時長（秒）— Spec 21 §「考試時長短於專注時段時自動停用」 */
  examDurationSec: number;
  /** 是否暫停（同步父層 isPaused 狀態） */
  paused?: boolean;
}

type Phase = 'focus' | 'short_break' | 'long_break';

export default function PomodoroTimer({ examDurationSec, paused = false }: PomodoroTimerProps) {
  const [settings, setSettings] = useState<PomodoroSettings>(loadSettings);
  const [showSettings, setShowSettings] = useState(false);
  const [phase, setPhase] = useState<Phase>('focus');
  const [secondsLeft, setSecondsLeft] = useState(settings.focus_min * 60);
  const [pomodoroCount, setPomodoroCount] = useState(0); // 已完成 focus 數
  const [showRestPrompt, setShowRestPrompt] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Spec 21 §「考試時長短於專注時段時自動停用」
  const tooShort = examDurationSec < settings.focus_min * 60;

  // 若 settings 改變 → 重置計時
  useEffect(() => {
    if (phase === 'focus') setSecondsLeft(settings.focus_min * 60);
    else if (phase === 'short_break') setSecondsLeft(settings.short_break_min * 60);
    else setSecondsLeft(settings.long_break_min * 60);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.focus_min, settings.short_break_min, settings.long_break_min, phase]);

  // Countdown
  useEffect(() => {
    if (!settings.enabled || tooShort || paused || showRestPrompt) return;
    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          // 切換階段
          if (phase === 'focus') {
            const nextCount = pomodoroCount + 1;
            setPomodoroCount(nextCount);
            const next: Phase =
              nextCount % settings.long_break_interval === 0 ? 'long_break' : 'short_break';
            setPhase(next);
            setShowRestPrompt(true);
            try { audioRef.current?.play(); } catch { /* silent */ }
          } else {
            setPhase('focus');
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [settings.enabled, tooShort, paused, phase, pomodoroCount, settings.long_break_interval, showRestPrompt]);

  const handleEnable = useCallback(() => {
    const s = { ...settings, enabled: !settings.enabled };
    setSettings(s);
    saveSettings(s);
    if (!s.enabled) setShowRestPrompt(false);
  }, [settings]);

  const handleSkipBreak = () => {
    setShowRestPrompt(false);
    setPhase('focus');
    setSecondsLeft(settings.focus_min * 60);
  };

  const handleStartBreak = () => {
    setShowRestPrompt(false);
    // phase 已在計時器內切換為 short_break / long_break，此處不變
  };

  const fmt = (s: number) => {
    const m = Math.floor(s / 60);
    const ss = s % 60;
    return `${String(m).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;
  };

  if (!settings.enabled) {
    return (
      <button
        onClick={handleEnable}
        className="flex items-center gap-1 px-2 py-1 text-xs text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded"
        title="啟用番茄鐘（focus 25 / 短休息 5 / 長休息 15 分鐘）"
      >
        🍅 啟用番茄鐘
      </button>
    );
  }

  if (tooShort) {
    return (
      <span className="text-[10px] text-slate-400" title="考試時長短於專注時段，番茄鐘已停用">
        🍅 已停用（考試 &lt; 專注時段）
      </span>
    );
  }

  const phaseLabel =
    phase === 'focus' ? '專注中' : phase === 'short_break' ? '短休息' : '長休息';
  const phaseColor =
    phase === 'focus' ? 'text-rose-600 bg-rose-50' : 'text-emerald-600 bg-emerald-50';

  return (
    <>
      <div className="flex items-center gap-2">
        <span className={`px-2 py-1 rounded text-xs font-mono font-medium ${phaseColor}`}>
          🍅 {phaseLabel} {fmt(secondsLeft)}
        </span>
        <span className="text-[10px] text-slate-400">已完成 {pomodoroCount} 個</span>
        <button
          onClick={() => setShowSettings(true)}
          className="text-slate-400 hover:text-slate-600"
          title="番茄鐘設定"
        >
          <Settings className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleEnable}
          className="text-slate-400 hover:text-rose-500"
          title="關閉番茄鐘"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 休息提示 modal */}
      {showRestPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-3">
              <Coffee className="h-6 w-6 text-emerald-500" />
              <h3 className="text-lg font-bold">
                {phase === 'long_break' ? '長休息時間' : '短休息時間'}
              </h3>
            </div>
            <p className="text-sm text-slate-600 mb-1">
              你完成了第 {pomodoroCount} 個番茄鐘 🎉
            </p>
            <p className="text-xs text-slate-500 mb-5 leading-relaxed">
              {phase === 'long_break'
                ? `建議休息 ${settings.long_break_min} 分鐘，起身走動 / 喝水 / 看遠方放鬆視線。`
                : `建議休息 ${settings.short_break_min} 分鐘，深呼吸放鬆。`}
              <br />
              （休息為建議性質，可選擇繼續作答）
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleStartBreak}
                className="flex-1 px-3 py-2 bg-emerald-500 text-white rounded text-sm font-medium hover:bg-emerald-600"
              >
                開始休息
              </button>
              <button
                onClick={handleSkipBreak}
                className="flex-1 px-3 py-2 bg-slate-100 text-slate-700 rounded text-sm font-medium hover:bg-slate-200"
              >
                繼續作答
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 設定 modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowSettings(false)}>
          <div
            className="bg-white rounded-2xl p-5 max-w-sm mx-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-emerald-500" /> 番茄鐘設定
              </h3>
              <button onClick={() => setShowSettings(false)}>
                <X className="w-5 h-5 text-slate-400 hover:text-slate-700" />
              </button>
            </div>
            {[
              { key: 'focus_min' as const, label: '專注時長（分鐘）', min: 15, max: 60 },
              { key: 'short_break_min' as const, label: '短休息（分鐘）', min: 1, max: 15 },
              { key: 'long_break_min' as const, label: '長休息（分鐘）', min: 5, max: 30 },
              { key: 'long_break_interval' as const, label: '幾個 focus 後長休息', min: 2, max: 8 },
            ].map((f) => (
              <div key={f.key} className="mb-3">
                <label className="block text-xs text-slate-600 mb-1">{f.label}（{f.min}–{f.max}）</label>
                <input
                  type="number"
                  min={f.min}
                  max={f.max}
                  value={settings[f.key]}
                  onChange={(e) => {
                    const v = Math.max(f.min, Math.min(f.max, Number(e.target.value) || f.min));
                    const s = { ...settings, [f.key]: v };
                    setSettings(s);
                    saveSettings(s);
                  }}
                  className="w-full px-2 py-1 border border-slate-200 rounded text-sm"
                />
              </div>
            ))}
            <p className="text-[11px] text-slate-400 mt-2">設定立即生效並儲存於本機 localStorage。</p>
          </div>
        </div>
      )}

      {/* notification sound（可選，瀏覽器自動阻擋音訊也沒關係）*/}
      <audio
        ref={audioRef}
        src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
        preload="auto"
      />
    </>
  );
}
