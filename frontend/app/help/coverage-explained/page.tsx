/**
 * @file 路由 `/help/coverage-explained` — 教育顧問誠實聲明：為何覆蓋率不是 100%。
 * 列 9 個遺漏風險源 + 4 道緩解設計，給備考生對系統能力的實際認知。
 */
'use client';

import Link from 'next/link';
import { AlertCircle, Shield } from 'lucide-react';

export default function CoverageExplainedPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <main className="container mx-auto max-w-3xl px-4 py-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            🎯 為何覆蓋率不是 100%？
          </h1>
          <p className="text-sm text-slate-600">
            教育顧問誠實聲明 — 9 個遺漏風險 + 4 道緩解設計
          </p>
        </header>

        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6 text-sm">
          <p className="font-bold text-amber-900 mb-1">老實說：YES，設計上會有 5-15% 內容遺漏可能。</p>
          <p className="text-amber-800 leading-relaxed">
            任何 AI 學習系統都有覆蓋極限。重點是<strong>讓你知道遺漏在哪</strong>，並提供補洞工具。
          </p>
        </div>

        <Section title="🔴 高風險：直接遺漏內容">
          <Risk
            n="1"
            title="節點 ↔ 鷹架命中率天花板（71-80%）"
            why="voyage cosine + rerank 對「抽象 vs 具體」對應力的天花板"
            impact="5-10% 鷹架找不到節點 / 5-10% 節點找不到鷹架"
            mitigate="UI orphan 標示 + 主動補洞"
          />
          <Risk
            n="2"
            title="節點抽取數量上限"
            why="prompt 限制每科目最多 8 章 × 6 節 = 48 節點，真實考綱可能 80-100 個"
            impact="LLM 自動「合併不重要的」→ 邊緣概念被吃掉"
            mitigate="未來 Sprint：放寬上限 + 加細粒度第三層"
          />
          <Risk
            n="3"
            title="考古題年份偏差"
            why="只看近 3-5 年題目"
            impact="早期重要概念若近期沒考 / 新考點若還沒考過 → 抓不到"
            mitigate="用戶主動上傳早期 / 最新題庫"
          />
          <Risk
            n="4"
            title="PDF parse 失敗 silent gap"
            why="部分章節 image 太多 / 格式怪 → parse 失敗"
            impact="失敗章節 = 0 鷹架（學生根本不知道有這章）"
            mitigate="dashboard 顯示「教材完整度 X%」+ 失敗清單"
          />
        </Section>

        <Section title="🟡 中風險：影響學習品質">
          <Risk
            n="5"
            title="題目映射節點命中率（70-85%）"
            why="voyage embedding 同類限制"
            impact="你答的題對應節點可能對錯 → mastery 計算貢獻錯誤節點"
            mitigate="多題答+confidence 標記提升信號穩定性"
          />
          <Risk
            n="6"
            title="SM-2 只追「答過題的鷹架」"
            why="鷹架沒測過 → 不會進複習迴圈"
            impact="只刷考古題不答鷹架題 → 大量鷹架沒進入 SM-2"
            mitigate="每章鷹架走完一遍才往下章"
          />
          <Risk
            n="7"
            title="跨資源整合限制"
            why="Concept-center 跨資源語意搜尋 70-85% 命中"
            impact="部分需要跨章節整合的考點對應不到"
            mitigate="主動使用 /concept-center 搜尋"
          />
        </Section>

        <Section title="🟢 低風險：可被其他防線抓到">
          <Risk
            n="8"
            title="鷹架類型偏「個別概念」"
            why="takeaway / pitfall 適合單概念"
            impact="跨概念綜合題（如「比較 A 和 B」）少有對應鷹架"
            mitigate="模擬考 + AI 教練蘇格拉底引導"
          />
          <Risk
            n="9"
            title="信心度校準需要量"
            why="至少 50+ 題標 confidence 才算得準"
            impact="備考前期樣本少 → 校準不可靠"
            mitigate="從 Phase A 開始就標 confidence，累積樣本"
          />
        </Section>

        <Section title="🛡️ 系統的四道緩解設計" icon={<Shield className="h-5 w-5 text-blue-600" />}>
          <Mitigation
            n="A"
            title="Coverage Dashboard"
            content="dashboard 顯示「節點 ↔ 鷹架命中率」「答題覆蓋率」「教材完整度」三個指標，讓你看到自己的遺漏地圖。"
          />
          <Mitigation
            n="B"
            title="Coverage Gap 主動告知"
            content="/today 顯示「⚠️ N 個節點教材待補」/ /knowledge 節點清單區分顏色：教材有 vs 教材缺。"
          />
          <Mitigation
            n="C"
            title="Question-derived scaffold（規劃中）"
            content="從考古題反推 takeaway/pitfall 填補 orphan 節點，但 amber 邊框 + retrieval-first 格式 + 信任度標示，明確告訴你「這份重點 AI 從考古題萃取，建議交叉驗證」。"
          />
          <Mitigation
            n="D"
            title="Coverage Report 週寄"
            content="每週日 email 告訴你：本週讀章 / 還有多少 orphan / 距考試 X 天 / 建議補 Y 個概念。"
          />
        </Section>

        <Section title="🧭 看到遺漏地圖時，平台這樣陪你處理">
          <div className="rounded-lg border border-violet-200 bg-violet-50/50 p-4 text-sm leading-relaxed text-slate-800 space-y-3">
            <p className="font-bold">揭露遺漏不是製造焦慮 — 每個 orphan 都會配補洞出口。</p>
            <div>
              <p className="font-semibold text-violet-900">① AI 自動補洞鷹架（amber 邊框）</p>
              <p className="text-xs text-slate-700 mt-0.5">orphan 節點不是空白 — 平台用考古題反推「定義 + 範例 + 一道題」的 retrieval-first 鷹架，amber 邊框 + 信任度標示提醒你交叉驗證，但至少有東西可以練。</p>
            </div>
            <div>
              <p className="font-semibold text-violet-900">② 完成度框架（不是紅字警告）</p>
              <p className="text-xs text-slate-700 mt-0.5">「⚠️ 5 個遺漏」會改成「📍 還有 5 個關卡待解鎖」+ 進度條 + 徽章。覆蓋率 85% 是備考甜蜜點，追求 100% 是邊際效益遞減 — 系統會幫你界定「該補哪幾個」而非「全部要補」。</p>
            </div>
            <div>
              <p className="font-semibold text-violet-900">③ AI 教練回應 orphan</p>
              <p className="text-xs text-slate-700 mt-0.5">點 orphan 節點直接觸發蘇格拉底對話 — AI 教練會問你「你覺得這個概念跟 X 有什麼關係？」陪你從零思考，不是丟一行紅字讓你自己想辦法。</p>
            </div>
          </div>
        </Section>

        <Section title="💡 給備考生的關鍵建議">
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm leading-relaxed text-slate-800">
            <p className="font-bold mb-2">這套系統是「學習教練 + 進度監控 + 弱點放大鏡」，不是「終身教材」。</p>
            <p>正確使用方式：</p>
            <ol className="list-decimal list-inside mt-2 space-y-1">
              <li>配 PDF 教材 / 線上課程當主軸（涵蓋 ≥ 85%）</li>
              <li>用本系統做「進度監控 + 弱點挖掘」（補 10-15% 漏洞）</li>
              <li>遇到 ⚠️ 標示節點主動補洞（書 / Coursera / YouTube）</li>
              <li>標 confidence + 答錯題進 SM-2 維持節奏</li>
              <li>每週看 dashboard 信心度趨勢校準自己</li>
            </ol>
          </div>
        </Section>

        <footer className="mt-10 text-xs text-slate-500 border-t border-slate-200 pt-4">
          <p>
            完整使用指南見 <Link href="/help/study-guide" className="text-emerald-600 underline">/help/study-guide</Link>。
          </p>
        </footer>
      </main>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="mb-7">
      <h2 className="flex items-center gap-2 text-lg font-bold text-slate-800 mb-3">
        {icon}{title}
      </h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Risk({ n, title, why, impact, mitigate }: { n: string; title: string; why: string; impact: string; mitigate: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
      <h3 className="font-bold text-slate-800 mb-1">
        <AlertCircle className="inline h-4 w-4 text-rose-500 mr-1" />
        風險 {n}：{title}
      </h3>
      <p className="text-xs text-slate-500 mb-1"><strong>為什麼</strong>：{why}</p>
      <p className="text-xs text-rose-700 mb-1"><strong>影響</strong>：{impact}</p>
      <p className="text-xs text-emerald-700"><strong>緩解</strong>：{mitigate}</p>
    </div>
  );
}

function Mitigation({ n, title, content }: { n: string; title: string; content: string }) {
  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50/40 p-3">
      <h3 className="text-sm font-bold text-blue-900">設計 {n}：{title}</h3>
      <p className="text-xs text-slate-700 mt-1 leading-relaxed">{content}</p>
    </div>
  );
}
