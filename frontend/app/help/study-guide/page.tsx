/**
 * @file 路由 `/help/study-guide` — 備考生使用指南。
 * 教育顧問版三階段路徑 + 四道防線 + 五個 anti-pattern + 系統限制誠實聲明。
 */
'use client';

import Link from 'next/link';
import { BookOpen, Target, Rocket, Shield, AlertTriangle, Coffee } from 'lucide-react';

export default function StudyGuidePage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <main className="container mx-auto max-w-3xl px-4 py-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            📚 備考生使用指南
          </h1>
          <p className="text-sm text-slate-600">
            教育顧問版 — 三階段路徑 + 四道防線 + 系統限制誠實聲明
          </p>
        </header>

        {/* 三階段 */}
        <Section title="三階段備考路徑" icon={<Target className="h-5 w-5 text-emerald-600" />}>
          <Phase
            color="emerald"
            icon={<BookOpen className="h-5 w-5" />}
            title="Phase A — 系統性學習"
            timing="考前 8-12 週｜目標 0→70%"
            steps={[
              '上傳 PDF / 影片教材',
              '進 /knowledge 點未測節點',
              '右側鷹架按順序看：🧭 定錨 → ⚡ 檢索 → 🔭 思考',
              '章節讀完做 InlinePractice 帶的 2-3 題',
            ]}
            kpi="每章鷹架互動率 > 80%"
          />
          <Phase
            color="amber"
            icon={<Target className="h-5 w-5" />}
            title="Phase B — 考古題演練"
            timing="考前 4-8 週｜目標 70%→85%"
            steps={[
              '/practice 系統依弱節點優先排題',
              '每題必標 confident / somewhat / guessing',
              '答錯立即看 AI 教練詳解（蘇格拉底式提問）',
              '答錯題進 SM-2 → 隔天 /today/reviews 自動排',
            ]}
            kpi="每節點正確率 > 70% 才進下個節點"
          />
          <Phase
            color="indigo"
            icon={<Rocket className="h-5 w-5" />}
            title="Phase C — 衝刺整合"
            timing="考前 2-4 週｜目標 85%→95%+"
            steps={[
              '/exam/setup 跨章節 mock exam',
              '計時答題 → /exam/results 結算',
              '看 dashboard 信心度校準區',
              '對「自信但答錯」題重點檢討（最危險盲點）',
            ]}
            kpi="模擬考及格率 ≥ 70% × 連續 3 次"
          />
        </Section>

        {/* 四道防線 */}
        <Section title="避免遺漏的四道防線" icon={<Shield className="h-5 w-5 text-blue-600" />}>
          <Defense
            n="1"
            title="節點 mastery 顏色檢核"
            content="/knowledge 列表每天看一次：🟢 精熟、🟡 部分、🔴 弱、⚪ 未測。優先處理紅色與灰色。"
          />
          <Defense
            n="2"
            title="⚠️ Orphan Node 主動補洞"
            content="看到節點顯示「此節點尚未對應到教材鷹架」絕對不能跳過 — 代表「考綱有但 PDF 沒寫」。處理方式：上傳第三方教材 / 純練該節點考古題 / 搜尋網路資源。"
          />
          <Defense
            n="3"
            title="信心度校準是備考生黃金指標"
            content="dashboard 看「自信但答錯」率：> 30% 紅色警報、10-30% 正常、< 10% 太保守。最致命的是「以為懂」。"
          />
          <Defense
            n="4"
            title="每週日 review 學習旅程"
            content="花 30 分鐘看 /dashboard 週報：本週讀章 vs 計畫、orphan 列表、信心度趨勢、距考試剩天數。"
          />
        </Section>

        {/* 系統限制 */}
        <Section title="🚨 系統限制（誠實聲明）" icon={<AlertTriangle className="h-5 w-5 text-rose-600" />}>
          <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 space-y-3">
            <p className="text-sm font-bold text-rose-800">
              這套系統 ≠ 唯一教材。設計上會有 5-15% 內容遺漏可能。
            </p>
            <ul className="text-xs text-rose-700 space-y-1.5 list-disc list-inside">
              <li>鷹架覆蓋率 70-80%（cosine + rerank 天花板）→ 配紙本書 / 線上課程交叉學</li>
              <li>節點抽取上限 48 個（每科）→ 邊緣概念可能被合併吃掉</li>
              <li>考古題年份限制（近 3-5 年）→ 早期 / 新考點可能漏</li>
              <li>🟡 amber 邊框「考古題反推」鷹架信心度低 → 搭配教材交叉驗證</li>
              <li>AI 教練可能 hallucinate → 答案標準仍以官方詳解為主</li>
              <li>節點命名偶有異常（檔名 / 章節編號）→ 看到請反映給平台</li>
            </ul>
          </div>
        </Section>

        {/* Anti-pattern */}
        <Section title="千萬別犯的 5 個錯誤" icon={<Coffee className="h-5 w-5 text-orange-600" />}>
          <AntiPattern wrong="只刷考古題不讀教材" right="讀+測 1:1 配合（testing effect 需要先有 schema）" />
          <AntiPattern wrong="看鷹架答案就翻頁" right="至少先想 30 秒再揭曉（Karpicke retrieval > 50% 提升記憶）" />
          <AntiPattern wrong="跳過弱節點不補" right="考試最愛問你最弱的（命題者反偽 bias）" />
          <AntiPattern wrong="不標 confidence" right="失去元認知校準價值（Dunning-Kruger 警告）" />
          <AntiPattern wrong="臨考前才開 SM-2" right="spaced repetition 需 4-6 週才看效果" />
        </Section>

        {/* 黃金 30 分鐘 */}
        <Section title="黃金 30 分鐘 Daily Routine">
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
            <ul className="text-sm text-slate-700 space-y-2">
              <li>🌅 <strong>早晨 (10min)</strong>：<Link href="/today" className="text-emerald-600 underline">/today</Link> reviews — SM-2 due 鷹架</li>
              <li>🌞 <strong>中午 (15min)</strong>：<Link href="/knowledge" className="text-emerald-600 underline">/knowledge</Link> 點未掌握節點，三 tab 學</li>
              <li>🌙 <strong>晚間 (5min)</strong>：<Link href="/practice" className="text-emerald-600 underline">/practice</Link> 5 題答錯題重練</li>
              <li>📅 <strong>週日 +30min</strong>：<Link href="/dashboard" className="text-emerald-600 underline">/dashboard</Link> 週報 + 找下週要補的 orphan nodes</li>
            </ul>
          </div>
        </Section>

        <footer className="mt-10 text-xs text-slate-400 border-t border-slate-200 pt-4">
          <p>
            這份指南由教育顧問依學習科學原則設計（Karpicke 2008 testing effect / Bjork desirable difficulty / Roediger 2011 / Sweller cognitive load / Dunning-Kruger 1999 metacognition）。
          </p>
          <p className="mt-1">
            建議搭配 <Link href="/help/coverage-explained" className="text-slate-500 underline">「為何覆蓋率不是 100%？」</Link> 一起閱讀。
          </p>
        </footer>
      </main>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="flex items-center gap-2 text-lg font-bold text-slate-800 mb-3">
        {icon}{title}
      </h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

function Phase({ color, icon, title, timing, steps, kpi }: {
  color: 'emerald' | 'amber' | 'indigo';
  icon: React.ReactNode;
  title: string;
  timing: string;
  steps: string[];
  kpi: string;
}) {
  const cls = {
    emerald: 'border-emerald-200 bg-emerald-50/50',
    amber: 'border-amber-200 bg-amber-50/50',
    indigo: 'border-indigo-200 bg-indigo-50/50',
  }[color];
  return (
    <div className={`rounded-lg border ${cls} p-4`}>
      <h3 className="flex items-center gap-2 font-bold text-slate-800 text-sm mb-1">
        {icon}{title}
      </h3>
      <p className="text-xs text-slate-500 mb-2">{timing}</p>
      <ol className="text-sm text-slate-700 list-decimal list-inside space-y-1">
        {steps.map((s, i) => <li key={i}>{s}</li>)}
      </ol>
      <p className="text-xs font-medium text-slate-600 mt-2">📊 KPI：{kpi}</p>
    </div>
  );
}

function Defense({ n, title, content }: { n: string; title: string; content: string }) {
  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50/40 p-3">
      <h3 className="text-sm font-bold text-blue-900">🛡️ 防線 {n}：{title}</h3>
      <p className="text-xs text-slate-700 mt-1 leading-relaxed">{content}</p>
    </div>
  );
}

function AntiPattern({ wrong, right }: { wrong: string; right: string }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3">
      <p className="text-sm text-rose-700">❌ {wrong}</p>
      <p className="text-sm text-emerald-700 mt-1">✅ {right}</p>
    </div>
  );
}
