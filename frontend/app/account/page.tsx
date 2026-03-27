'use client';

import { useState, useEffect } from 'react';
import { User, CreditCard, Shield, Settings, Zap, CheckCircle2, Award, Download, Trash2, Flame, Moon, Sun, AlertTriangle, X, BookOpen, Eye, EyeOff, Pencil } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import { accountService } from '@/lib/api/services';
import type { GetUserUsageResponse, GetAchievementsResponse, GetBillingHistoryResponse } from '@/types';
import AchievementGrid from '@/components/AchievementGrid';
import GrowthTimeline from '@/components/GrowthTimeline';

type TabId = 'profile' | 'billing' | 'security' | 'preferences' | 'achievements';

export default function AccountPage() {
  const { user, isPro, isProPlus, isUltra, subscriptionTier, setSubscriptionTier } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('profile');
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [darkMode, setDarkMode] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [notifDaily, setNotifDaily] = useState(true);
  const [notifPreExam, setNotifPreExam] = useState(true);
  const [notifWeekly, setNotifWeekly] = useState(true);

  // Mock billing history data
  const mockBillingHistory = [
    { date: '2026-03-01', description: 'PRO 方案 月費', amount: 199, status: 'paid' as const },
    { date: '2026-02-01', description: 'PRO 方案 月費', amount: 199, status: 'paid' as const },
  ];

  // Mock subject data
  const [subjects, setSubjects] = useState([
    { name: 'AWS SAA', date: '2026-06-15', level: '有基礎', mode: 'Standard' },
    { name: 'CFA Level 1', date: '2026-08-20', level: '初學', mode: 'Mastery' },
  ]);

  // Data for each tab
  const [usage, setUsage] = useState<GetUserUsageResponse | null>(null);
  const [achievements, setAchievements] = useState<GetAchievementsResponse | null>(null);
  const [billing, setBilling] = useState<GetBillingHistoryResponse | null>(null);

  useEffect(() => {
    accountService.getUsage().then(setUsage);
    accountService.getAchievements().then(setAchievements);
    accountService.getBillingHistory().then(setBilling);
  }, []);

  const handleSaveProfile = async () => {
    setSaving(true);
    await accountService.updateProfile({ displayName: user?.displayName });
    setSaving(false);
  };

  const handleChangePassword = () => {
    setPasswordMessage(null);
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordMessage({ type: 'error', text: '請填寫所有欄位' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: 'error', text: '新密碼與確認密碼不一致' });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMessage({ type: 'error', text: '新密碼長度需至少 8 個字元' });
      return;
    }
    // Mock success
    setPasswordMessage({ type: 'success', text: '密碼已成功更新' });
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setShowCurrentPassword(false);
    setShowNewPassword(false);
    setShowConfirmPassword(false);
  };

  const handleEditSubject = (name: string) => {
    alert(`編輯科目：${name}（Mock）`);
  };

  const handleRemoveSubject = (name: string) => {
    setSubjects(prev => prev.filter(s => s.name !== name));
  };

  const handleAddSubject = () => {
    alert('新增備考科目（Mock）');
  };

  const tabs: { id: TabId; label: string; icon: typeof User }[] = [
    { id: 'profile', label: '個人資料', icon: User },
    { id: 'billing', label: '訂閱與帳單', icon: CreditCard },
    { id: 'security', label: '安全性', icon: Shield },
    { id: 'preferences', label: '偏好設定', icon: Settings },
    { id: 'achievements', label: '成就與歷程', icon: Award },
  ];

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-3xl font-bold text-slate-900 mb-8">帳號與訂閱管理</h1>

      <div className="grid md:grid-cols-3 gap-8">
        {/* Sidebar */}
        <div className="space-y-2">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <tab.icon className="h-5 w-5" /> {tab.label}
            </button>
          ))}

          {/* Demo tier toggle */}
          <div className="mt-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Demo 模式</p>
            <div className="space-y-1.5">
              {(['FREE', 'PRO_199', 'PRO_PLUS_399', 'ULTRA_1599'] as const).map(tier => (
                <label key={tier} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="radio"
                    name="demo_tier"
                    checked={subscriptionTier === tier}
                    onChange={() => setSubscriptionTier(tier)}
                    className="text-emerald-500 focus:ring-emerald-500"
                  />
                  <span className="text-slate-700">
                    {tier === 'FREE' ? '免費版' : tier === 'PRO_199' ? 'Pro (199)' : tier === 'PRO_PLUS_399' ? 'Pro Plus (399)' : 'Ultra (1599)'}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="md:col-span-2 space-y-8">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
              <h2 className="text-xl font-bold text-slate-900 mb-6">個人資料</h2>

              <div className="flex items-center gap-6 mb-8">
                <div className="h-24 w-24 rounded-full bg-slate-200 flex items-center justify-center text-3xl font-bold text-slate-500 border-4 border-white shadow-sm">
                  {user?.displayName?.charAt(0) || 'U'}
                </div>
                <button className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-slate-200">
                  更換大頭貼
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">姓名</label>
                    <input type="text" defaultValue={user?.displayName || ''} className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">使用者名稱</label>
                    <input type="text" defaultValue="learner_01" className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">電子郵件</label>
                  <input type="email" defaultValue={user?.email || ''} disabled className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-slate-500 cursor-not-allowed" />
                </div>
                <div className="pt-4">
                  <button
                    onClick={handleSaveProfile}
                    disabled={saving}
                    className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                  >
                    {saving ? '儲存中...' : '儲存變更'}
                  </button>
                </div>
              </div>
            </section>
          )}

          {/* Billing Tab */}
          {activeTab === 'billing' && (
            <>
              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-slate-900">目前方案</h2>
                  <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-bold border ${
                    isUltra ? 'bg-purple-50 text-purple-700 border-purple-200' :
                    isProPlus ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                    isPro ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                    'bg-slate-100 text-slate-700 border-slate-200'
                  }`}>
                    {isUltra ? 'Ultra 版' : isProPlus ? 'Pro Plus 版' : isPro ? 'Pro 版' : 'Free 版'}
                  </span>
                </div>

                <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200 mb-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-slate-900 mb-1">
                        {isUltra ? 'Ultra 企業方案' : isProPlus ? 'Pro Plus 方案' : isPro ? 'Pro 方案' : '免費體驗中'}
                      </h3>
                      <p className="text-sm text-slate-500 mb-4">
                        {isUltra ? '無上限 AI 教練、Vision OCR、企業後台與進階分析。' :
                         isProPlus ? '解鎖 Vision OCR、對話式 AI 教練與動態弱點出題引擎。' :
                         isPro ? '無限制文件與 YouTube 解析、基礎 AI 功能。' :
                         '你目前享有基礎功能，每月 3 份文件與 3 次測驗。'}
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-extrabold text-slate-900">
                        NT${isUltra ? '1,599' : isProPlus ? '399' : isPro ? '199' : '0'}
                      </span>
                      <span className="text-slate-500 text-sm"> / 月</span>
                    </div>
                  </div>

                  {usage && (
                    <>
                      <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-emerald-500 rounded-full" style={{
                          width: `${Math.min(100, (usage.usage.documentsUploadedCount / usage.limits.documentsPerMonth) * 100)}%`
                        }} />
                      </div>
                      <p className="text-xs text-slate-500 text-right">
                        本月已使用 {usage.usage.documentsUploadedCount}/{usage.limits.documentsPerMonth} 份文件解析額度
                      </p>
                    </>
                  )}
                </div>

                {/* Usage Details */}
                {usage && (
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-xs text-slate-500 mb-1">AI 問答次數 (今日)</p>
                      <p className="text-lg font-bold text-slate-900">- / {usage.limits.aiQueriesPerDay}</p>
                    </div>
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <p className="text-xs text-slate-500 mb-1">Vision OCR</p>
                      <p className={`text-lg font-bold ${isProPlus ? 'text-slate-900' : 'text-slate-400'}`}>
                        {isProPlus ? `${usage.usage.visionOcrPagesCount} / ${usage.limits.visionOcrPagesPerMonth}` : '🔒 需 Pro Plus'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Upsell cards */}
                {!isPro && (
                  <div className="rounded-2xl border-2 border-emerald-500 bg-emerald-50 p-6 relative overflow-hidden mb-4">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-bl-full" />
                    <div className="flex items-center gap-3 mb-4">
                      <div className="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center">
                        <Zap className="h-5 w-5 text-emerald-600" />
                      </div>
                      <div>
                        <h3 className="font-bold text-emerald-900">升級至 Pro 版</h3>
                        <p className="text-sm text-emerald-700">NT$199 / 月</p>
                      </div>
                    </div>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2 text-sm text-emerald-800"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> 無限制文件與 YouTube 解析</li>
                      <li className="flex items-center gap-2 text-sm text-emerald-800"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> 無限制模擬測驗生成</li>
                      <li className="flex items-center gap-2 text-sm text-emerald-800"><CheckCircle2 className="h-4 w-4 text-emerald-500" /> 移除廣告，純淨備考體驗</li>
                    </ul>
                    <button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-3 rounded-xl font-bold transition-colors shadow-md shadow-emerald-500/20">
                      升級 Pro (NT$199/月)
                    </button>
                  </div>
                )}
                {!isProPlus && (
                  <div className="rounded-2xl border-2 border-yellow-400 bg-yellow-50 p-6 relative overflow-hidden mb-4">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-400/10 rounded-bl-full" />
                    <div className="flex items-center gap-3 mb-4">
                      <div className="h-10 w-10 rounded-full bg-yellow-100 flex items-center justify-center">
                        <Zap className="h-5 w-5 text-yellow-600" />
                      </div>
                      <div>
                        <h3 className="font-bold text-yellow-900">升級至 Pro Plus 版</h3>
                        <p className="text-sm text-yellow-700">NT$399 / 月</p>
                      </div>
                    </div>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2 text-sm text-yellow-800"><CheckCircle2 className="h-4 w-4 text-yellow-500" /> 解鎖對話式 AI 教練（每月 200 次）</li>
                      <li className="flex items-center gap-2 text-sm text-yellow-800"><CheckCircle2 className="h-4 w-4 text-yellow-500" /> Vision OCR 辨識手寫與工程圖</li>
                      <li className="flex items-center gap-2 text-sm text-yellow-800"><CheckCircle2 className="h-4 w-4 text-yellow-500" /> 動態弱點出題引擎</li>
                      <li className="flex items-center gap-2 text-sm text-yellow-800"><CheckCircle2 className="h-4 w-4 text-yellow-500" /> 遇到卡關可呼叫 Claude / GPT-4o</li>
                    </ul>
                    <button className="w-full bg-yellow-400 hover:bg-yellow-500 text-yellow-900 px-4 py-3 rounded-xl font-bold transition-colors shadow-md shadow-yellow-400/20">
                      升級 Pro Plus (NT$399/月)
                    </button>
                  </div>
                )}
                {!isUltra && (
                  <div className="rounded-2xl border border-purple-200 bg-purple-50 p-5 relative overflow-hidden">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-bold text-purple-900">Ultra 企業定錨版</h3>
                      <span className="text-sm font-bold text-purple-700">NT$1,599 / 月</span>
                    </div>
                    <p className="text-xs text-purple-700 mb-3">無額度上限 AI 教練、B2B 企業後台、Super Admin 控制台、自帶向量叢集。</p>
                    <button className="w-full bg-purple-600 hover:bg-purple-700 text-white px-4 py-2.5 rounded-xl text-sm font-bold transition-colors">
                      聯絡企業銷售
                    </button>
                  </div>
                )}
                {/* Cancel subscription */}
                {isPro && (
                  <div className="mt-4 text-center">
                    <button className="text-sm text-slate-400 hover:text-rose-500 underline transition-colors">
                      取消訂閱
                    </button>
                    <p className="text-xs text-slate-400 mt-1">取消後，您的方案將在當前帳單週期結束時降級為免費版</p>
                  </div>
                )}
              </section>

              {/* Billing History Table */}
              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-6">帳單記錄</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">日期</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">說明</th>
                        <th className="text-right py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">金額</th>
                        <th className="text-center py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">狀態</th>
                        <th className="text-center py-3 px-4 text-xs font-bold text-slate-500 uppercase tracking-wider">收據</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(billing && billing.invoices.length > 0
                        ? billing.invoices.map(inv => ({
                            date: inv.date,
                            description: `${inv.amount >= 1599 ? 'ULTRA' : inv.amount >= 399 ? 'PRO PLUS' : 'PRO'} 方案 月費`,
                            amount: inv.amount,
                            status: inv.status,
                          }))
                        : mockBillingHistory
                      ).map((row, idx) => (
                        <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                          <td className="py-3 px-4 text-slate-900">{new Date(row.date).toLocaleDateString('zh-TW')}</td>
                          <td className="py-3 px-4 text-slate-700">{row.description}</td>
                          <td className="py-3 px-4 text-right font-medium text-slate-900">NT${row.amount}</td>
                          <td className="py-3 px-4 text-center">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                              row.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                            }`}>
                              {row.status === 'paid' ? '已付款' : '處理中'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <button
                              disabled
                              className="inline-flex items-center gap-1 text-xs text-slate-400 cursor-not-allowed"
                              title="功能開發中"
                            >
                              <Download className="h-3.5 w-3.5" /> 下載收據
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <>
              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-6">變更密碼</h2>
                {passwordMessage && (
                  <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
                    passwordMessage.type === 'success'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}>
                    {passwordMessage.text}
                  </div>
                )}
                <div className="space-y-4 max-w-md">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">目前密碼</label>
                    <div className="relative">
                      <input
                        type={showCurrentPassword ? 'text' : 'password'}
                        value={currentPassword}
                        onChange={e => setCurrentPassword(e.target.value)}
                        className="w-full rounded-lg border border-slate-300 px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">新密碼</label>
                    <div className="relative">
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        value={newPassword}
                        onChange={e => setNewPassword(e.target.value)}
                        className="w-full rounded-lg border border-slate-300 px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">確認新密碼</label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        className="w-full rounded-lg border border-slate-300 px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="pt-4">
                    <button
                      onClick={handleChangePassword}
                      className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                    >
                      更新密碼
                    </button>
                  </div>
                </div>
              </section>

              <section className="bg-white rounded-3xl p-8 shadow-sm border border-rose-200">
                <h2 className="text-xl font-bold text-rose-700 mb-4">危險區域</h2>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-900">匯出我的資料</p>
                    <p className="text-xs text-slate-500">下載所有學習記錄與個人資料</p>
                  </div>
                  <button className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors flex items-center gap-2">
                    <Download className="h-4 w-4" /> 匯出
                  </button>
                </div>
                <div className="border-t border-rose-100 mt-4 pt-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-rose-700">刪除帳號</p>
                    <p className="text-xs text-slate-500">永久刪除帳號及所有資料，此操作無法復原</p>
                  </div>
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="px-4 py-2 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-sm font-bold hover:bg-rose-100 transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="h-4 w-4" /> 刪除帳號
                  </button>
                </div>
              </section>
            </>
          )}

          {/* Preferences Tab */}
          {activeTab === 'preferences' && (
            <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
              <h2 className="text-xl font-bold text-slate-900 mb-6">偏好設定</h2>

              <div className="space-y-8">
                <div>
                  <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">通知設定</h3>
                  <div className="space-y-4">
                    {[
                      { label: '每日複習提醒', desc: '根據艾賓浩斯排程發送每日複習提醒', checked: notifDaily, onChange: () => setNotifDaily(!notifDaily) },
                      { label: '考前衝刺通知', desc: '考試前發送衝刺通知與鼓勵信', checked: notifPreExam, onChange: () => setNotifPreExam(!notifPreExam) },
                      { label: '每週學習週報', desc: '每週日發送學習數據與進度週報', checked: notifWeekly, onChange: () => setNotifWeekly(!notifWeekly) },
                    ].map(item => (
                      <label key={item.label} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 cursor-pointer hover:border-slate-200 transition-colors">
                        <div>
                          <p className="text-sm font-medium text-slate-900">{item.label}</p>
                          <p className="text-xs text-slate-500">{item.desc}</p>
                        </div>
                        <button
                          type="button"
                          onClick={item.onChange}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${item.checked ? 'bg-emerald-500' : 'bg-slate-300'}`}
                        >
                          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${item.checked ? 'translate-x-6' : 'translate-x-1'}`} />
                        </button>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">外觀</h3>
                  <label className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100 cursor-pointer hover:border-slate-200 transition-colors">
                    <div className="flex items-center gap-3">
                      {darkMode ? <Moon className="h-5 w-5 text-indigo-500" /> : <Sun className="h-5 w-5 text-amber-500" />}
                      <div>
                        <p className="text-sm font-medium text-slate-900">深色模式</p>
                        <p className="text-xs text-slate-500">切換明/暗色主題</p>
                      </div>
                    </div>
                    <button
                      onClick={() => setDarkMode(!darkMode)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${darkMode ? 'bg-indigo-500' : 'bg-slate-300'}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${darkMode ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </label>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">語言</h3>
                  <select className="w-full max-w-xs bg-slate-50 border border-slate-200 rounded-xl px-4 py-2 text-sm outline-none focus:border-emerald-500 transition-all">
                    <option>繁體中文</option>
                    <option>English</option>
                  </select>
                </div>
              </div>
            </section>
          )}

          {/* Achievements Tab */}
          {activeTab === 'achievements' && achievements && (
            <>
              {/* Streak Records */}
              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <Flame className="h-6 w-6 text-orange-500" /> 學習連勝紀錄
                </h2>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-gradient-to-b from-orange-50 to-white rounded-2xl border border-orange-100">
                    <Flame className="h-8 w-8 text-orange-500 mx-auto mb-2" />
                    <span className="block text-3xl font-extrabold text-slate-900">12</span>
                    <span className="text-xs text-slate-500 font-medium">目前連勝</span>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-b from-amber-50 to-white rounded-2xl border border-amber-100">
                    <Award className="h-8 w-8 text-amber-500 mx-auto mb-2" />
                    <span className="block text-3xl font-extrabold text-slate-900">45</span>
                    <span className="text-xs text-slate-500 font-medium">歷史最長連勝</span>
                  </div>
                  <div className="text-center p-4 bg-gradient-to-b from-blue-50 to-white rounded-2xl border border-blue-100">
                    <Shield className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                    <span className="block text-3xl font-extrabold text-slate-900">2</span>
                    <span className="text-xs text-slate-500 font-medium">凍結額度餘額</span>
                  </div>
                </div>
              </section>

              {/* Backup Subject Management */}
              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <BookOpen className="h-6 w-6 text-indigo-500" /> 備考科目管理
                </h2>
                <div className="space-y-3">
                  {subjects.map(subject => (
                    <div key={subject.name} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <div>
                        <p className="font-medium text-slate-900">{subject.name}</p>
                        <p className="text-xs text-slate-500">
                          考試日期：{subject.date} · 自評程度：{subject.level} · 模式：{subject.mode}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleEditSubject(subject.name)}
                          className="text-xs text-emerald-600 hover:text-emerald-700 font-medium px-3 py-1 rounded-lg hover:bg-emerald-50 transition-colors inline-flex items-center gap-1"
                        >
                          <Pencil className="h-3 w-3" /> 編輯
                        </button>
                        <button
                          onClick={() => handleRemoveSubject(subject.name)}
                          className="text-xs text-rose-500 hover:text-rose-600 font-medium px-3 py-1 rounded-lg hover:bg-rose-50 transition-colors inline-flex items-center gap-1"
                        >
                          <Trash2 className="h-3 w-3" /> 移除
                        </button>
                      </div>
                    </div>
                  ))}
                  <button
                    onClick={handleAddSubject}
                    className="w-full py-3 border-2 border-dashed border-slate-200 rounded-xl text-sm font-medium text-slate-500 hover:border-emerald-300 hover:text-emerald-600 transition-colors"
                  >
                    + 新增備考科目
                  </button>
                </div>
              </section>

              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <Award className="h-6 w-6 text-amber-500" /> 成就徽章
                </h2>
                <AchievementGrid achievements={achievements.achievements} />
              </section>

              <section className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200">
                <h2 className="text-xl font-bold text-slate-900 mb-6">學習歷程</h2>
                <GrowthTimeline milestones={achievements.milestones} />
              </section>
            </>
          )}
        </div>
      </div>

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="h-12 w-12 rounded-full bg-rose-100 flex items-center justify-center">
                  <AlertTriangle className="h-6 w-6 text-rose-600" />
                </div>
                <h2 className="text-xl font-bold text-rose-700">刪除帳號</h2>
              </div>
              <button onClick={() => setShowDeleteModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4 mb-6">
              <p className="text-sm text-slate-700">此操作將<strong className="text-rose-700">永久刪除</strong>您的帳號及以下所有資料：</p>
              <ul className="text-sm text-slate-600 space-y-2 pl-4">
                <li className="flex items-start gap-2"><span className="text-rose-500 mt-0.5">•</span> 主資料庫中所有個人資料與測驗記錄</li>
                <li className="flex items-start gap-2"><span className="text-rose-500 mt-0.5">•</span> Redis 中所有關聯快取</li>
                <li className="flex items-start gap-2"><span className="text-rose-500 mt-0.5">•</span> 雲端存儲的實體檔案</li>
                <li className="flex items-start gap-2"><span className="text-rose-500 mt-0.5">•</span> 所有 JWT 存取憑證立即失效</li>
              </ul>
              <p className="text-sm text-rose-600 font-medium">此操作無法復原。</p>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  請輸入 <code className="bg-slate-100 px-1 py-0.5 rounded text-rose-600 font-mono text-xs">DELETE</code> 以確認
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={e => setDeleteConfirmText(e.target.value)}
                  placeholder="輸入 DELETE"
                  className="w-full rounded-lg border border-rose-200 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => { setShowDeleteModal(false); setDeleteConfirmText(''); }}
                className="flex-1 px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium transition-colors"
              >
                取消
              </button>
              <button
                disabled={deleteConfirmText !== 'DELETE'}
                className="flex-1 px-4 py-3 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Trash2 className="h-4 w-4" /> 永久刪除帳號
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
