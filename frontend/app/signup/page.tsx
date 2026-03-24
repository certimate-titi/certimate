'use client';

import { useState } from 'react';
import Link from 'next/link';
import { BrainCircuit, ArrowRight, X } from 'lucide-react';

/* ─────────────────────────────────────────────
   Modal component
───────────────────────────────────────────── */
function LegalModal({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      onClick={onClose}
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm" />

      {/* modal box */}
      <div
        className="relative z-10 w-full max-w-lg bg-white rounded-3xl shadow-2xl flex flex-col max-h-[80vh]"
        onClick={e => e.stopPropagation()}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-bold text-slate-900">{title}</h2>
          <button
            onClick={onClose}
            className="h-8 w-8 flex items-center justify-center rounded-full hover:bg-slate-100 transition-colors text-slate-500"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* scrollable body */}
        <div className="overflow-y-auto px-6 py-5 text-sm text-slate-700 leading-relaxed space-y-4">
          {children}
        </div>

        {/* footer */}
        <div className="px-6 py-4 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold rounded-xl transition-colors"
          >
            我已閱讀，關閉
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Terms of Service content
───────────────────────────────────────────── */
function TermsContent() {
  return (
    <>
      <p className="text-xs text-slate-400">最後更新：2026 年 3 月 19 日</p>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">1. AI 內容免責聲明</h3>
        <p>本平台所產生之測驗考題、知識節點及 AI 教練對話，皆由人工智慧模型自動生成，<strong>系統無法 100% 保證內容之正確性、完整性與時效性</strong>。請使用者自行查證重要資訊。</p>
        <p className="mt-2">本平台提供的模擬考試成績僅供參考，<strong>平台對使用者的實際考試、證照取得結果不負任何直接或間接之擔保責任</strong>。因信賴本系統解答而導致考試失利，不構成退款或賠償之理由。</p>
      </section>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">2. 使用者內容上傳與著作權</h3>
        <p>使用者上傳之任何文檔（PDF、圖片）與影音連結（YouTube 網址），皆須自行保證擁有<strong>合法使用權利或已取得版權方授權</strong>，得用以作為個人學習之用途。</p>
        <p className="mt-2">平台做為網路服務提供者（ISP），不事先審核使用者上傳之檔案。若第三方版權方提出侵權申訴，平台有權徑行刪除或隱藏爭議資源，且不承擔任何連帶賠償責任。</p>
        <p className="mt-2">使用者不得將包含未授權版權內容的測驗庫公開至社群，否則平台有權立刻停權。</p>
      </section>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">3. 服務中斷與第三方依賴</h3>
        <p>本平台使用第三方 AI 模型服務與雲端基礎設施。如遇不可抗力（包含但不限於上游模型 API 故障），導致功能暫時無法使用，平台將盡力修復，但<strong>不對暫時性服務中斷衍生的損失提供賠償</strong>。</p>
        <p className="mt-2">使用者同意在上傳文件及發送對話時，相關資料將可能傳輸至 OpenAI / Anthropic / Google 以進行處理，並受各該第三方之服務條款及隱私權政策規範。</p>
      </section>
    </>
  );
}

/* ─────────────────────────────────────────────
   Privacy Policy content
───────────────────────────────────────────── */
function PrivacyContent() {
  return (
    <>
      <p className="text-xs text-slate-400">最後更新：2026 年 3 月 19 日</p>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">1. AI 模型訓練排除聲明</h3>
        <p><strong>本平台承諾：使用者上傳之私人學習資料、文件與測驗記錄，絕不會被用來訓練平台自家 AI 模型</strong>。所有資料僅透過安全的 API 傳送給第三方 LLM（且我們要求第三方不作為訓練資料）進行您專屬的任務處理。</p>
      </section>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">2. 個人資料的蒐集範圍</h3>
        <p>我們蒐集的個人資料包含：</p>
        <ul className="list-disc pl-5 mt-1 space-y-1">
          <li>您在註冊時提供的姓名、電子郵件</li>
          <li>您上傳的學習文件內容（僅用於生成個人化考題）</li>
          <li>您的測驗記錄與學習進度</li>
        </ul>
      </section>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">3. 個資保留與刪除權</h3>
        <p>於退費或刪除帳號時，您有權要求清空所有使用紀錄與個人資訊。系統將於 <strong>30 個工作天內</strong>從資料庫（包含向量資料庫中的 Embedding 特徵）中徹底銷毀您的資料。</p>
      </section>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">4. Cookie 與追蹤技術</h3>
        <p>本平台使用必要性 Cookie 維持您的登入狀態，以及分析性 Cookie 了解網站使用狀況。您可隨時透過瀏覽器設定停用，但可能影響部分功能的正常運作。</p>
      </section>

      <section>
        <h3 className="font-bold text-slate-800 mb-1">5. 聯絡我們</h3>
        <p>如對隱私權政策有任何疑問，歡迎來信至：<strong>privacy@certimate.app</strong></p>
      </section>
    </>
  );
}

/* ─────────────────────────────────────────────
   Main Signup Page
───────────────────────────────────────────── */
export default function SignupPage() {
  const [showTerms, setShowTerms] = useState(false);
  const [showPrivacy, setShowPrivacy] = useState(false);

  return (
    <>
      {/* Terms of Service Modal */}
      <LegalModal open={showTerms} title="服務條款" onClose={() => setShowTerms(false)}>
        <TermsContent />
      </LegalModal>

      {/* Privacy Policy Modal */}
      <LegalModal open={showPrivacy} title="隱私權政策" onClose={() => setShowPrivacy(false)}>
        <PrivacyContent />
      </LegalModal>

      <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
          <div className="text-center">
            <div className="mx-auto h-12 w-12 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
              <BrainCircuit className="h-8 w-8 text-emerald-600" />
            </div>
            <h2 className="text-3xl font-extrabold text-slate-900">建立帳號</h2>
            <p className="mt-2 text-sm text-slate-600">
              開始你的 AI 學習旅程
            </p>
          </div>
          
          <form className="mt-8 space-y-6" action="#" method="POST">
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="sr-only">姓名</label>
                <input id="name" name="name" type="text" required className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm" placeholder="姓名" />
              </div>
              <div>
                <label htmlFor="email-address" className="sr-only">電子郵件</label>
                <input id="email-address" name="email" type="email" autoComplete="email" required className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm" placeholder="電子郵件" />
              </div>
              <div>
                <label htmlFor="password" className="sr-only">密碼</label>
                <input id="password" name="password" type="password" autoComplete="new-password" required className="appearance-none rounded-xl relative block w-full px-4 py-3 border border-slate-300 placeholder-slate-500 text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm" placeholder="密碼 (至少 8 個字元)" />
              </div>
            </div>

            <div className="flex items-start gap-2">
              <input id="terms" name="terms" type="checkbox" required className="h-4 w-4 mt-0.5 text-emerald-600 focus:ring-emerald-500 border-slate-300 rounded shrink-0" />
              <label htmlFor="terms" className="block text-sm text-slate-700 leading-snug">
                我同意{' '}
                <button
                  type="button"
                  onClick={() => setShowTerms(true)}
                  className="text-emerald-600 hover:underline font-medium"
                >
                  服務條款
                </button>
                {' '}與{' '}
                <button
                  type="button"
                  onClick={() => setShowPrivacy(true)}
                  className="text-emerald-600 hover:underline font-medium"
                >
                  隱私權政策
                </button>
                ，並知悉上傳之私有資料<span className="font-semibold text-slate-900">絕不用於訓練本平台專屬 AI 模型</span>。
              </label>
            </div>

            <div>
              <button type="submit" className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-emerald-500 hover:bg-emerald-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-colors shadow-md shadow-emerald-500/20">
                免費註冊
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-slate-500">
                  或使用以下方式註冊
                </span>
              </div>
            </div>

            <div className="mt-6">
              <button className="w-full flex items-center justify-center px-4 py-3 border border-slate-300 rounded-xl shadow-sm bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
                <svg className="h-5 w-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                Google 註冊
              </button>
            </div>
          </div>

          <p className="mt-8 text-center text-sm text-slate-600">
            已經有帳號了？{' '}
            <Link href="/login" className="font-medium text-emerald-600 hover:text-emerald-500">
              登入 <ArrowRight className="inline h-4 w-4" />
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
