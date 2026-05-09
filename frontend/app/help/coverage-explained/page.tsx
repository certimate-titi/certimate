/**
 * @file 路由 `/help/coverage-explained` — 知識版圖解說頁（B.1 文案改寫）
 *
 * 標題：「你已解鎖 N% 的知識版圖」（N 用 mock 值 42）
 * 文案語言：解鎖框架，非警告框架
 *
 * TODO: backend wire-up — N 值目前為 mock 42，
 *       後端提供 /api/v1/subjects/{id}/completion 後改為動態值。
 */
'use client';

import Link from 'next/link';
import { BookOpen, Target, TrendingUp, Zap, Award, Map } from 'lucide-react';
import CompletionProgressBar from '@/components/completion/CompletionProgressBar';

// TODO: backend wire-up — mock 完成度，待接真實 API
const MOCK_PERCENT = 42;

export default function CoverageExplainedPage() {
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
        你已解鎖 {MOCK_PERCENT}% 的知識版圖
      </h1>
      <p className="text-sm text-slate-500 mb-6">
        每練習一個節點，你的版圖就會擴大。以下說明系統如何計算你的進度。
      </p>

      {/* 進度條展示 */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 mb-8">
        <p className="text-xs text-slate-500 mb-4">你目前的知識解鎖進度</p>
        <CompletionProgressBar
          percent={MOCK_PERCENT}
          sweetSpotReached={MOCK_PERCENT >= 85}
          label="當前版圖解鎖率"
        />
        <p className="text-[11px] text-slate-400 mt-3">
          {/* TODO: backend wire-up */}
          此數值為示意，登入後顯示你的實際進度。
        </p>
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
