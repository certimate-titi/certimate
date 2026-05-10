/**
 * @file 路由 `/help/coverage-explained` — 知識版圖解說頁（B.1 文案改寫）
 *
 * 標題：「你已解鎖 N% 的知識版圖」
 * 文案語言：解鎖框架，非警告框架
 *
 * Wire-up：從 localStorage 讀取 activeSubjectId 後呼叫後端
 *   GET /api/v1/subjects/{id}/completion
 * 若 API 未回應（未登入或無科目），fallback 顯示 mock 42%。
 */
'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { BookOpen, Target, TrendingUp, Zap, Award, Map } from 'lucide-react';
import CompletionProgressBar from '@/components/completion/CompletionProgressBar';
import { completionService } from '@/lib/api/services';
import type { SubjectCompletionResponse } from '@/types/api';

// fallback mock 完成度（未登入 / API 失敗時顯示）
const FALLBACK_PERCENT = 42;

/** 假 UUID（00000000-0000-0000-0000-000000000000）偵測 */
const FAKE_UUID_RE = /^0{8}-0{4}-0{4}-0{4}-0{12}$/;

export default function CoverageExplainedPage() {
  const [completion, setCompletion] = useState<SubjectCompletionResponse | null>(null);
  const [fetching, setFetching] = useState(false);
  // 'none'：無科目 / 'not_found'：API 404 / 'server_error'：API 5xx / null：正常
  const [fetchError, setFetchError] = useState<'none' | 'not_found' | 'server_error' | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  const doFetch = useCallback((subjectId: string) => {
    setFetching(true);
    setFetchError(null);
    completionService
      .getCompletion(subjectId)
      .then((res) => { setCompletion(res); setFetchError(null); })
      .catch((err: any) => {
        setCompletion(null);
        const status = err?.response?.status ?? err?.status;
        if (status === 404) setFetchError('not_found');
        else if (status >= 500) setFetchError('server_error');
        // 其他錯誤 fallback 到 mock，不設 fetchError
      })
      .finally(() => setFetching(false));
  }, []);

  useEffect(() => {
    const subjectId =
      typeof window !== 'undefined'
        ? localStorage.getItem('certimate_active_subject_id')
        : null;

    // 守衛：無 subjectId 或假 UUID → 不發 API
    if (!subjectId || FAKE_UUID_RE.test(subjectId)) {
      setFetchError('none');
      return;
    }

    doFetch(subjectId);
  }, [doFetch, retryKey]);

  const percent = completion ? completion.sweet_spot_progress : FALLBACK_PERCENT;
  const isMock = completion === null && !fetching && !fetchError;

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      {/* 麵包屑 */}
      <nav className="text-xs text-slate-400 mb-6 flex items-center gap-1.5">
        <Link href="/dashboard" className="hover:text-emerald-600 transition-colors">首頁</Link>
        <span>/</span>
        <span className="text-slate-600">知識版圖說明</span>
      </nav>

      {/* 主標題（B.1 改寫：解鎖語言） */}
      <h1 className="text-2xl font-bold text-slate-900 mb-2">
        你已解鎖 {percent}% 的知識版圖
      </h1>
      <p className="text-sm text-slate-500 mb-6">
        每練習一個節點，你的版圖就會擴大。以下說明系統如何計算你的進度。
      </p>

      {/* 進度條 / 提示卡區域 */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 mb-8">
        <p className="text-xs text-slate-500 mb-4">你目前的知識解鎖進度</p>

        {/* 載入中 */}
        {fetching && (
          <div className="h-6 bg-slate-100 rounded animate-pulse" />
        )}

        {/* 無科目提示卡 */}
        {!fetching && fetchError === 'none' && (
          <div className="p-4 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-center">
            <p className="text-sm font-medium text-slate-700 mb-1">選擇一個科目以查看你的解鎖進度</p>
            <p className="text-xs text-slate-500 mb-3">登入後前往帳號或 Onboarding 頁選擇備考科目</p>
            <Link
              href="/onboarding"
              className="inline-block px-4 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold rounded-full transition-colors"
            >
              選擇科目 →
            </Link>
          </div>
        )}

        {/* 5xx 錯誤 + 重試 */}
        {!fetching && fetchError === 'server_error' && (
          <div className="p-4 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-center">
            <p className="text-xs text-slate-500 mb-2">進度載入失敗，請稍後再試</p>
            <button
              onClick={() => setRetryKey(k => k + 1)}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-800 underline"
            >
              重試
            </button>
          </div>
        )}

        {/* 404 提示卡 */}
        {!fetching && fetchError === 'not_found' && (
          <div className="p-4 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-center">
            <p className="text-sm text-slate-600 mb-2">找不到此科目的進度資料</p>
            <Link href="/account" className="text-xs font-semibold text-emerald-600 hover:text-emerald-800 underline">
              前往帳號設定 →
            </Link>
          </div>
        )}

        {/* 正常顯示進度條 */}
        {!fetching && !fetchError && (
          <CompletionProgressBar
            percent={percent}
            sweetSpotReached={percent >= 85}
            label="當前版圖解鎖率"
          />
        )}

        {isMock && (
          <p className="text-[11px] text-slate-400 mt-3">
            此數值為示意，登入並選擇科目後顯示你的實際進度。
          </p>
        )}
        {completion && (
          <p className="text-[11px] text-slate-400 mt-3">
            全覆蓋進度：{completion.full_coverage_progress}%　衝刺模式：{completion.sprint_mode_progress}%
          </p>
        )}
      </div>

      {/* 說明清單（B.1 解鎖語言） */}
      <div className="space-y-4 mb-8">
        <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
          <Map className="h-4 w-4 text-emerald-500" />
          版圖如何計算？
        </h2>

        <div className="space-y-3">
          <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <BookOpen className="h-4 w-4 text-indigo-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-800">每個知識節點都是一扇門</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                系統將課綱拆解為數十個知識節點，每練習一個節點就解鎖一扇門。
                節點越多，你的知識版圖越完整。
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <Zap className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-800">📍 高頻關卡權重加倍</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                標記為「高頻」的節點（歷屆考試高度重複出現）在計算中
                佔更高比重，優先解鎖這些關卡讓你事半功倍。
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <Target className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-800">🎯 85% 是甜蜜點</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                研究顯示，解鎖 85% 的知識版圖後，通過率已大幅提升。
                繼續衝往 100% 需要更多投入，但邊際效益會逐漸遞減。
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl border border-slate-100">
            <TrendingUp className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-800">掌握度決定解鎖深度</p>
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                每個節點有「初探」→「熟悉」→「精熟」三個層次。
                答題正確率越高，該節點的解鎖比例越高。
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-emerald-50 rounded-xl border border-emerald-200">
            <Award className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-emerald-800">📍 解鎖徽章里程碑</p>
              <p className="text-xs text-emerald-700 mt-0.5 leading-relaxed">
                每達到一個里程碑（25% / 50% / 85% / 100% 等），你將解鎖對應徽章。
                這些徽章代表你真實的學習成就，不能手動取得。
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 行動呼籲 */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          href="/knowledge"
          className="flex-1 text-center bg-emerald-500 text-white py-3 px-4 rounded-xl font-semibold text-sm hover:bg-emerald-600 transition-colors"
        >
          前往知識地圖 →
        </Link>
        <Link
          href="/practice"
          className="flex-1 text-center bg-slate-100 text-slate-700 py-3 px-4 rounded-xl font-semibold text-sm hover:bg-slate-200 transition-colors"
        >
          開始練習解鎖
        </Link>
      </div>
    </div>
  );
}
