import Link from 'next/link';
import { ArrowRight, BrainCircuit, Calendar, CheckCircle2, Clock, FileText, Play, RefreshCw, ShieldCheck, Zap } from 'lucide-react';
import Image from 'next/image';

export default function LandingPage() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white pt-24 pb-32">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="container relative mx-auto px-4 text-center">
          <div className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-sm text-emerald-600 mb-8">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
            CertiMate 2.0 全新上線
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-6">
            AI 賦能證照考試平台<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-500 to-teal-400">打破單向學習</span>
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-slate-600 mb-10">
            上傳講義、貼上 YouTube 連結，AI 自動為你生成互動心智圖與專屬模擬考。
            錯題不再死背，蘇格拉底教練帶你深度推導，一次考取證照。
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup" className="w-full sm:w-auto rounded-full bg-emerald-500 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-emerald-500/30 hover:bg-emerald-600 transition-all hover:-translate-y-1 flex items-center justify-center gap-2">
              立即免費註冊 <ArrowRight className="h-5 w-5" />
            </Link>
            <Link href="#features" className="w-full sm:w-auto rounded-full bg-white border border-slate-200 px-8 py-4 text-lg font-semibold text-slate-700 hover:bg-slate-50 transition-all flex items-center justify-center gap-2">
              <Play className="h-5 w-5 text-slate-400" /> 觀看展示
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-slate-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">三步打造你的專屬學習路徑</h2>
            <p className="text-slate-600 max-w-2xl mx-auto">從資料匯入到弱點突破，CertiMate 為你包辦所有繁瑣的整理工作。</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
              <div className="h-14 w-14 rounded-2xl bg-blue-50 flex items-center justify-center mb-6">
                <FileText className="h-7 w-7 text-blue-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">1. 一鍵上傳解析</h3>
              <p className="text-slate-600">支援 PDF、Markdown、手寫筆記，甚至 YouTube 連結。AI 自動抓取重點並結構化。</p>
            </div>
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
              <div className="h-14 w-14 rounded-2xl bg-emerald-50 flex items-center justify-center mb-6">
                <Zap className="h-7 w-7 text-emerald-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">2. 智能生成考卷</h3>
              <p className="text-slate-600">根據你的知識庫，動態生成單選、複選、計算題。仿造真實機考介面，無縫接軌。</p>
            </div>
            <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-100">
              <div className="h-14 w-14 rounded-2xl bg-purple-50 flex items-center justify-center mb-6">
                <BrainCircuit className="h-7 w-7 text-purple-500" />
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-3">3. AI 蘇格拉底教練</h3>
              <p className="text-slate-600">錯題深度檢討，AI 教練引導你思考盲點，提供記憶口訣與公式推導，真正學懂。</p>
            </div>
          </div>
        </div>
      </section>

      {/* Ebbinghaus & Google Calendar Section */}
      <section className="py-24 bg-white border-t border-slate-100">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <div className="inline-flex items-center rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm text-blue-600 mb-4">
              <Calendar className="h-4 w-4 mr-2" />
              全新功能：自動化複習排程
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
              艾賓浩斯遺忘曲線 × Google 日曆
            </h2>
            <p className="text-lg text-slate-600 max-w-3xl mx-auto">
              徹底解決「看完就忘」、「不知道今天該複習什麼」的痛點。CertiMate 結合科學記憶法與你最常用的日曆工具，打造全自動的「虛擬備考特訓排程」。
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left side: Feature details */}
            <div className="space-y-12">
              {/* Feature 1 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-12 w-12 rounded-2xl bg-indigo-50 flex items-center justify-center">
                    <Clock className="h-6 w-6 text-indigo-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">科學化記憶追蹤</h3>
                  <p className="text-slate-600 leading-relaxed">
                    當你在測驗中產生「錯題」或標註「待釐清觀念」時，系統會自動賦予記憶權重，並在 <strong>24小時、3天、7天、14天、30天</strong> 後觸發複習。若再次答錯，權重重置，確保真正進入長期記憶。
                  </p>
                </div>
              </div>

              {/* Feature 2 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-12 w-12 rounded-2xl bg-blue-50 flex items-center justify-center">
                    <Calendar className="h-6 w-6 text-blue-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Google 日曆無縫整合</h3>
                  <p className="text-slate-600 leading-relaxed">
                    透過 Google OAuth 授權，自動建立 <code>[CertiMate] 專屬備考教練</code> 日曆。每天半夜自動計算今日應複習清單，並主動推播至你的日曆，不再被動等待登入。
                  </p>
                </div>
              </div>

              {/* Feature 3 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-12 w-12 rounded-2xl bg-emerald-50 flex items-center justify-center">
                    <RefreshCw className="h-6 w-6 text-emerald-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">動態變形專屬考卷</h3>
                  <p className="text-slate-600 leading-relaxed">
                    點擊日曆上的專屬連結，系統會根據當日排程，使用 LLM <strong>動態變形生成 5~10 題專屬考卷</strong>。拒絕死背原題答案，真正驗證觀念理解程度。
                  </p>
                </div>
              </div>

              {/* Feature 4 */}
              <div className="flex gap-4">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-12 w-12 rounded-2xl bg-amber-50 flex items-center justify-center">
                    <ShieldCheck className="h-6 w-6 text-amber-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">無可取代的陪伴感</h3>
                  <p className="text-slate-600 leading-relaxed">
                    宛如嚴厲又貼心的專屬家教每天盯著你讀書。未來更將銜接 Notion / Google Drive 雙向同步，昨天抄的新筆記，今天一早自動變成隨堂測驗。
                  </p>
                </div>
              </div>
            </div>

            {/* Right side: Visual representation / Mockup */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-100 to-emerald-50 rounded-3xl transform rotate-3 scale-105 opacity-50"></div>
              <div className="relative bg-white border border-slate-200 rounded-3xl shadow-xl overflow-hidden">
                {/* Calendar Header Mock */}
                <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-5 w-5 text-blue-600" />
                    <span className="font-semibold text-slate-700">Google Calendar</span>
                  </div>
                  <div className="flex gap-1">
                    <div className="w-3 h-3 rounded-full bg-red-400"></div>
                    <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                    <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
                  </div>
                </div>
                {/* Calendar Body Mock */}
                <div className="p-6">
                  <div className="mb-4 text-sm font-medium text-slate-500">今天, 3月17日</div>
                  
                  <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-xl p-4 mb-4 shadow-sm">
                    <h4 className="font-bold text-slate-900 flex items-center gap-2 mb-2">
                      <span>🎯 [CertiMate] 今日特訓：AWS IAM 與微積分極限</span>
                    </h4>
                    <div className="text-sm text-slate-600 space-y-2">
                      <p>你今天有 3 個遺忘曲線複習任務等待完成：</p>
                      <ol className="list-decimal list-inside space-y-1 ml-1">
                        <li>IAM Role 與 Policy 的差異 <span className="text-xs text-rose-500 bg-rose-50 px-1.5 py-0.5 rounded ml-1">(錯題複習)</span></li>
                        <li>微積分 L&apos;Hôpital&apos;s Rule 應用 <span className="text-xs text-amber-500 bg-amber-50 px-1.5 py-0.5 rounded ml-1">(觀念釐清)</span></li>
                        <li>React Hooks 基礎 <span className="text-xs text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded ml-1">(第 2 次複習)</span></li>
                      </ol>
                      <div className="pt-3 mt-3 border-t border-blue-100">
                        <span className="inline-flex items-center text-sm font-semibold text-blue-600">
                          👉 點擊專屬連結立即開始「今日特訓考卷」
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-50 border-l-4 border-slate-300 rounded-r-xl p-4 opacity-70">
                    <h4 className="font-medium text-slate-700">團隊週會</h4>
                    <p className="text-xs text-slate-500 mt-1">14:00 - 15:00</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">選擇適合你的方案</h2>
            <p className="text-slate-600 max-w-2xl mx-auto">無論是考前衝刺還是長期備戰，都有最適合的選擇。</p>
          </div>
          <div className="grid md:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {/* Free */}
            <div className="rounded-3xl border border-slate-200 p-7 flex flex-col">
              <h3 className="text-xl font-bold text-slate-900 mb-2">Free</h3>
              <p className="text-slate-500 text-sm mb-6">體驗基礎功能</p>
              <div className="mb-6">
                <span className="text-3xl font-extrabold text-slate-900">NT$0</span>
                <span className="text-slate-500 text-sm"> / 月</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 每月 3 份文件解析</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 每月 3 回模擬測驗</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 基礎錯題提示</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> YouTube &lt; 30 分鐘</li>
              </ul>
              <Link href="/signup" className="w-full rounded-full bg-slate-100 px-4 py-3 text-center font-semibold text-slate-900 hover:bg-slate-200 transition-colors text-sm">
                免費開始
              </Link>
            </div>
            {/* Pro */}
            <div className="rounded-3xl border-2 border-emerald-500 bg-emerald-50/30 p-7 flex flex-col relative transform md:-translate-y-4 shadow-xl shadow-emerald-100">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-emerald-500 text-white px-4 py-1 rounded-full text-sm font-bold tracking-wide">
                超值首選
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">Pro</h3>
              <p className="text-slate-500 text-sm mb-6">無限出題護城河</p>
              <div className="mb-6">
                <span className="text-3xl font-extrabold text-slate-900">NT$199</span>
                <span className="text-slate-500 text-sm"> / 月</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 無限制文件解析</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> YouTube 無時長限制</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 無限制模擬測驗</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 移除廣告、純淨閱讀</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" /> 互動式知識心智圖</li>
              </ul>
              <Link href="/signup" className="w-full rounded-full bg-emerald-500 px-4 py-3 text-center font-semibold text-white hover:bg-emerald-600 transition-colors shadow-md shadow-emerald-500/20 text-sm">
                升級 Pro
              </Link>
            </div>
            {/* Pro Plus */}
            <div className="rounded-3xl border-2 border-yellow-400 bg-yellow-50/30 p-7 flex flex-col relative transform md:-translate-y-4 shadow-xl shadow-yellow-100">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-yellow-400 text-yellow-900 px-4 py-1 rounded-full text-sm font-bold tracking-wide">
                主力推薦
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">Pro Plus</h3>
              <p className="text-slate-500 text-sm mb-6">AI 教練 + Vision OCR</p>
              <div className="mb-6">
                <span className="text-3xl font-extrabold text-slate-900">NT$399</span>
                <span className="text-slate-500 text-sm"> / 月</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" /> 包含所有 Pro 功能</li>
                <li className="flex items-start gap-2 text-sm text-slate-900 font-medium"><CheckCircle2 className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" /> 對話式 AI 教練 (200次/月)</li>
                <li className="flex items-start gap-2 text-sm text-slate-900 font-medium"><CheckCircle2 className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" /> Vision OCR 手寫辨識</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" /> 動態弱點出題引擎</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-yellow-500 shrink-0 mt-0.5" /> Claude / GPT-4o 深度救援</li>
              </ul>
              <Link href="/signup" className="w-full rounded-full bg-yellow-400 px-4 py-3 text-center font-semibold text-yellow-900 hover:bg-yellow-500 transition-colors shadow-md shadow-yellow-400/20 text-sm">
                升級 Pro Plus
              </Link>
            </div>
            {/* Ultra */}
            <div className="rounded-3xl border border-purple-200 p-7 flex flex-col">
              <h3 className="text-xl font-bold text-slate-900 mb-2">Ultra</h3>
              <p className="text-slate-500 text-sm mb-6">企業與補教機構專屬</p>
              <div className="mb-6">
                <span className="text-3xl font-extrabold text-slate-900">NT$1,599</span>
                <span className="text-slate-500 text-sm"> / 月</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-purple-500 shrink-0 mt-0.5" /> 包含所有 Pro Plus 功能</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-purple-500 shrink-0 mt-0.5" /> 無額度上限 AI 教練</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-purple-500 shrink-0 mt-0.5" /> Notion / Google Drive 同步</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-purple-500 shrink-0 mt-0.5" /> B2B 後台與席位管理</li>
                <li className="flex items-start gap-2 text-sm text-slate-600"><CheckCircle2 className="h-4 w-4 text-purple-500 shrink-0 mt-0.5" /> Super Admin 控制台</li>
              </ul>
              <Link href="/edu-console" className="w-full rounded-full bg-purple-600 px-4 py-3 text-center font-semibold text-white hover:bg-purple-700 transition-colors text-sm">
                聯絡企業銷售
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
