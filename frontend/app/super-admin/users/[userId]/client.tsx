'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { superAdminService } from '@/lib/api/services';
import { 
  ChevronLeft, 
  Mail, 
  ShieldAlert, 
  ShieldCheck, 
  CreditCard, 
  Activity, 
  Cpu, 
  Clock, 
  History,
  AlertCircle,
  ExternalLink,
  Calendar,
  Zap,
  FileText,
  BrainCircuit
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface UserData {
  id: string;
  name: string;
  email: string;
  avatar: string;
  tier: string;
  status: string;
  joined: string;
  method: string;
  stripeId: string;
  expiry: string;
  planSource: 'payment' | 'admin' | 'unknown';
  usage: { uploads: number; exams: number; qna: number; ocr: number };
  tokens: { today: string; month: string; distribution: { name: string; value: number; color: string }[] };
  logins: { time: string; ip: string; device: string }[];
  abnormal: { type: string; detail: string; time: string }[];
}

const defaultUserData: UserData = {
  id: '--', name: '--', email: '--', avatar: '-', tier: '--', status: '--',
  joined: '--', method: '--', stripeId: '--', expiry: '--', planSource: 'unknown',
  usage: { uploads: 0, exams: 0, qna: 0, ocr: 0 },
  tokens: { today: '0', month: '0', distribution: [] },
  logins: [], abnormal: [],
};

export default function UserDetailsPage() {
  const params = useParams();
  const userId = params.userId;
  const [userData, setUserData] = useState<UserData>(defaultUserData);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [planStartDate, setPlanStartDate] = useState('');
  const [planEndDate, setPlanEndDate] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmName, setDeleteConfirmName] = useState('');
  const [showUsageModal, setShowUsageModal] = useState(false);

  useEffect(() => {
    if (!userId) return;
    superAdminService.getUserDetail(String(userId)).then((raw) => {
      const profile = (raw.profile || {}) as Record<string, unknown>;
      const subscription = (raw.subscription || {}) as Record<string, unknown>;
      const behavior = (raw.behavior || {}) as Record<string, unknown>;
      const tokenUsage = (raw.token_usage || {}) as Record<string, unknown>;
      const anomalies = (raw.anomalies || {}) as Record<string, unknown>;

      setUserData({
        id: String(raw.id || userId),
        name: String(profile.display_name || profile.name || profile.email || '--'),
        email: String(profile.email || '--'),
        avatar: String(profile.display_name || profile.name || profile.email || '-').charAt(0),
        tier: String(subscription.plan || '--'),
        status: String(subscription.status || profile.status || 'active'),
        joined: String(profile.created_at || '--'),
        method: String(profile.auth_method || '--'),
        stripeId: String(subscription.stripe_id || '--'),
        expiry: String(subscription.next_billing_date || '--'),
        planSource: (subscription.plan_source as 'payment' | 'admin') || 'unknown',
        usage: {
          uploads: Number((raw.usage as Record<string, unknown>)?.uploads || 0),
          exams: Number((raw.usage as Record<string, unknown>)?.exams || 0),
          qna: Number((raw.usage as Record<string, unknown>)?.qna || 0),
          ocr: Number((raw.usage as Record<string, unknown>)?.ocr || 0),
        },
        tokens: {
          today: String(tokenUsage.remaining_quota || '0'),
          month: String(tokenUsage.monthly_tokens || '0'),
          distribution: [],
        },
        logins: Array.isArray(raw.login_history) ? (raw.login_history as { time: string; ip: string; device: string }[]) : [],
        abnormal: Array.isArray((anomalies.cooling_records)) ? (anomalies.cooling_records as { type: string; detail: string; time: string }[]) : [],
      });
    }).catch(() => {});
  }, [userId]);

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4">
        <Link 
          href="/super-admin/users"
          className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-900 transition-all"
        >
          <ChevronLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">用戶詳情</h1>
          <p className="text-slate-500">檢視與管理用戶 {userId} 的完整資訊</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Left Column: Profile & Subscription */}
        <div className="space-y-8">
          {/* Basic Profile */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <div className="flex flex-col items-center text-center mb-6">
              <div className="h-24 w-24 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 text-3xl font-bold border-4 border-white shadow-lg mb-4">
                {userData.avatar}
              </div>
              <h2 className="text-xl font-bold text-slate-900">{userData.name}</h2>
              <p className="text-sm text-slate-500">{userData.email}</p>
              <div className="mt-4 flex gap-2">
                <span className={cn(
                  "text-xs font-bold px-3 py-1 rounded-full",
                  userData.status === 'active' ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"
                )}>
                  {userData.status === 'active' ? '帳號正常' : '已停權'}
                </span>
                <span className="text-xs font-bold px-3 py-1 bg-indigo-50 text-indigo-600 rounded-full">
                  {userData.tier} 方案
                </span>
              </div>
            </div>

            <div className="space-y-4 pt-6 border-t border-slate-100">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">User ID</span>
                <span className="font-mono text-slate-900">{userData.id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">註冊方式</span>
                <span className="text-slate-900">{userData.method}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">註冊日期</span>
                <span className="text-slate-900">{userData.joined}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 mt-8">
              <button
                onClick={async () => {
                  if (!confirm('確定要恢復此用戶帳號？')) return;
                  try {
                    await superAdminService.activateUser(String(userId));
                    setUserData(prev => ({ ...prev, status: 'active' }));
                  } catch { alert('操作失敗'); }
                }}
                className="py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all flex items-center justify-center gap-2"
              >
                <ShieldCheck className="h-4 w-4" /> 恢復正常
              </button>
              <button
                onClick={async () => {
                  const reason = prompt('請輸入停權原因:');
                  if (!reason) return;
                  try {
                    await superAdminService.suspendUser(String(userId), reason);
                    setUserData(prev => ({ ...prev, status: 'suspended' }));
                    alert('帳號已停權');
                  } catch { alert('操作失敗'); }
                }}
                className="py-2 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center justify-center gap-2"
              >
                <ShieldAlert className="h-4 w-4" /> 停權帳號
              </button>
            </div>
            <button
              onClick={() => { setDeleteConfirmName(''); setShowDeleteModal(true); }}
              className="w-full mt-3 py-2 bg-white border border-rose-200 text-rose-500 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all"
            >
              刪除用戶帳號
            </button>
          </section>

          {/* Subscription Details */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-indigo-500" /> 訂閱狀態
            </h3>
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">當前方案</p>
                <p className="text-lg font-bold text-slate-900">{userData.tier}</p>
              </div>
              <div className="space-y-3 px-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5" /> 有效期限
                  </span>
                  <span className="text-slate-900 font-medium">
                    {userData.expiry && userData.expiry !== '--'
                      ? `至 ${userData.expiry.split('T')[0]}`
                      : '未設定'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">權限來源</span>
                  <span className={cn(
                    "text-xs font-bold px-2 py-0.5 rounded-lg",
                    userData.planSource === 'payment' && "bg-blue-50 text-blue-600",
                    userData.planSource === 'admin' && "bg-amber-50 text-amber-600",
                    userData.planSource === 'unknown' && "bg-slate-100 text-slate-500"
                  )}>
                    {userData.planSource === 'payment' && '信用卡付款'}
                    {userData.planSource === 'admin' && '管理員調整'}
                    {userData.planSource === 'unknown' && '未記錄'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Stripe ID</span>
                  <span className="font-mono text-slate-900 flex items-center gap-1">
                    {userData.stripeId} <ExternalLink className="h-3 w-3" />
                  </span>
                </div>
              </div>
              <button
                onClick={() => { setSelectedPlan(userData.tier); setPlanStartDate(new Date().toISOString().split('T')[0]); setPlanEndDate(''); setShowPlanModal(true); }}
                className="w-full py-3 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition-all"
              >
                調整訂閱等級
              </button>
            </div>
          </section>
        </div>

        {/* Middle Column: Usage & Tokens */}
        <div className="lg:col-span-2 space-y-8">
          {/* Usage Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: '上傳文件', value: userData.usage.uploads, icon: FileText, color: 'blue' },
              { label: '生成考試', value: userData.usage.exams, icon: Zap, color: 'amber' },
              { label: 'AI 問答', value: userData.usage.qna, icon: BrainCircuit, color: 'emerald' },
              { label: 'Vision OCR', value: userData.usage.ocr, icon: Activity, color: 'rose' },
            ].map((stat) => (
              <div key={stat.label} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                <stat.icon className={cn("h-5 w-5 mb-3", 
                  stat.color === 'blue' && "text-blue-500",
                  stat.color === 'amber' && "text-amber-500",
                  stat.color === 'emerald' && "text-emerald-500",
                  stat.color === 'rose' && "text-rose-500"
                )} />
                <p className="text-xs text-slate-500 font-medium mb-1">{stat.label}</p>
                <p className="text-xl font-bold text-slate-900">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* Token Consumption */}
          <div className="grid md:grid-cols-2 gap-8">
            <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
              <h3 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
                <Cpu className="h-5 w-5 text-rose-500" /> Token 消耗分佈
              </h3>
              <div className="h-[200px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={userData.tokens.distribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={70}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {userData.tokens.distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 space-y-2">
                {userData.tokens.distribution.map((item) => (
                  <div key={item.name} className="flex justify-between items-center text-xs">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                      <span className="text-slate-600">{item.name}</span>
                    </div>
                    <span className="font-bold text-slate-900">{item.value}%</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
                  <Activity className="h-5 w-5 text-emerald-500" /> 用量摘要
                </h3>
                <div className="space-y-6">
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                      <span>今日 Token 用量</span>
                      <span className="text-emerald-600">{userData.tokens.today}</span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(Number(userData.tokens.today) || 0, 100)}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                      <span>本月 Token 用量</span>
                      <span className="text-indigo-600">{userData.tokens.month}</span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${Math.min(Number(userData.tokens.month) || 0, 100)}%` }}></div>
                    </div>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setShowUsageModal(true)}
                className="mt-8 w-full py-3 border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all"
              >
                查看詳細用量日誌
              </button>
            </section>
          </div>

          {/* Tables: Logins & Abnormal */}
          <div className="grid md:grid-cols-2 gap-8">
            <section className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                <History className="h-5 w-5 text-slate-400" />
                <h3 className="font-bold text-slate-900">登入紀錄 (最近 20 次)</h3>
              </div>
              <div className="divide-y divide-slate-100">
                {userData.logins.map((login, i) => (
                  <div key={i} className="px-6 py-3 flex justify-between items-center hover:bg-slate-50 transition-all">
                    <div>
                      <p className="text-sm font-medium text-slate-900">{login.time}</p>
                      <p className="text-xs text-slate-500">{login.device}</p>
                    </div>
                    <span className="text-xs font-mono text-slate-400">{login.ip}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-rose-500" />
                <h3 className="font-bold text-slate-900">異常紀錄</h3>
              </div>
              <div className="divide-y divide-slate-100">
                {userData.abnormal.map((record, i) => (
                  <div key={i} className="px-6 py-3 hover:bg-rose-50/30 transition-all">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded">
                        {record.type}
                      </span>
                      <span className="text-xs text-slate-400">{record.time}</span>
                    </div>
                    <p className="text-sm text-slate-700">{record.detail}</p>
                  </div>
                ))}
                {userData.abnormal.length === 0 && (
                  <div className="p-8 text-center">
                    <p className="text-sm text-slate-400">目前無異常紀錄</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
      {/* 用量日誌 Modal */}
      {showUsageModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowUsageModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 mb-4">用量日誌摘要</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-100">
                  <p className="text-xs text-emerald-600 uppercase tracking-wider font-medium mb-1">今日 Token</p>
                  <p className="text-xl font-bold text-emerald-700">{userData.tokens.today}</p>
                </div>
                <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-100">
                  <p className="text-xs text-indigo-600 uppercase tracking-wider font-medium mb-1">本月 Token</p>
                  <p className="text-xl font-bold text-indigo-700">{userData.tokens.month}</p>
                </div>
              </div>
              <div className="space-y-3 px-1">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">上傳文件</span>
                  <span className="font-bold text-slate-900">{userData.usage.uploads}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">生成考試</span>
                  <span className="font-bold text-slate-900">{userData.usage.exams}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">AI 問答</span>
                  <span className="font-bold text-slate-900">{userData.usage.qna}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">Vision OCR</span>
                  <span className="font-bold text-slate-900">{userData.usage.ocr}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowUsageModal(false)}
              className="w-full mt-6 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-50 transition-all"
            >
              關閉
            </button>
          </div>
        </div>
      )}
      {/* 調整訂閱等級 Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowPlanModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-slate-900 mb-4">調整訂閱等級</h3>
            <p className="text-sm text-slate-500 mb-4">目前方案：<span className="font-bold text-slate-900">{userData.tier}</span></p>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {['FREE', 'PRO', 'PRO_PLUS', 'ULTRA'].map(plan => (
                <button
                  key={plan}
                  onClick={() => setSelectedPlan(plan)}
                  className={cn(
                    "py-3 rounded-xl text-sm font-bold transition-all border",
                    selectedPlan === plan
                      ? "bg-emerald-500 text-white border-emerald-500 shadow-lg shadow-emerald-500/20"
                      : "bg-white text-slate-700 border-slate-200 hover:border-emerald-300"
                  )}
                >
                  {plan}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1 block">起始日期</label>
                <input
                  type="date"
                  value={planStartDate}
                  onChange={e => setPlanStartDate(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-emerald-500 transition-all"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1 block">結束日期</label>
                <input
                  type="date"
                  value={planEndDate}
                  onChange={e => setPlanEndDate(e.target.value)}
                  min={planStartDate}
                  className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-emerald-500 transition-all"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowPlanModal(false)}
                className="flex-1 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-50 transition-all"
              >
                取消
              </button>
              <button
                onClick={async () => {
                  if (!selectedPlan || !planStartDate || !planEndDate) { alert('請選擇方案並設定有效期限'); return; }
                  if (planEndDate < planStartDate) { alert('結束日期不能早於起始日期'); return; }
                  try {
                    const { apiClient } = await import('@/lib/api/client');
                    await apiClient.post(`/admin/users/${userId}/adjust-subscription`, { plan: selectedPlan, start_date: planStartDate, end_date: planEndDate });
                    setUserData(prev => ({ ...prev, tier: selectedPlan, expiry: planEndDate, planSource: 'admin' }));
                    setShowPlanModal(false);
                    alert('訂閱等級已更新');
                  } catch { alert('調整失敗，請稍後再試'); }
                }}
                className="flex-1 py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-bold hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20"
              >
                確認調整
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 刪除用戶確認 Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowDeleteModal(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-rose-600 mb-2">刪除用戶帳號</h3>
            <p className="text-sm text-slate-500 mb-4">
              此操作將永久刪除用戶 <span className="font-bold text-slate-900">{userData.name}</span> 的帳號，無法復原。
            </p>
            <div className="p-4 bg-rose-50 rounded-xl border border-rose-100 mb-4">
              <p className="text-xs text-rose-700 mb-2">
                請輸入用戶名稱 <span className="font-bold">「{userData.name}」</span> 以確認刪除：
              </p>
              <input
                type="text"
                value={deleteConfirmName}
                onChange={e => setDeleteConfirmName(e.target.value)}
                placeholder={userData.name}
                className="w-full px-4 py-2 bg-white border border-rose-200 rounded-xl text-sm outline-none focus:border-rose-500 transition-all"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-2.5 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-50 transition-all"
              >
                取消
              </button>
              <button
                disabled={deleteConfirmName !== userData.name}
                onClick={async () => {
                  try {
                    await superAdminService.deleteUser(String(userId), deleteConfirmName);
                    setShowDeleteModal(false);
                    alert('用戶已刪除');
                    window.location.href = '/super-admin/users';
                  } catch { alert('刪除失敗，請確認名稱是否正確'); }
                }}
                className="flex-1 py-2.5 bg-rose-500 text-white rounded-xl text-sm font-bold hover:bg-rose-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                確認刪除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
