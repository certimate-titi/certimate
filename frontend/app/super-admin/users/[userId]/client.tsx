'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
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

// Mock Data for a single user
const userData = {
  id: 'usr_1',
  name: '張小明',
  email: 'ming@example.com',
  avatar: '張',
  tier: 'Ultra',
  status: 'active',
  joined: '2026-01-15',
  method: 'Google SSO',
  stripeId: 'cus_Q9z2x8v1',
  expiry: '2027-01-15',
  usage: {
    uploads: 142,
    exams: 85,
    qna: 1240,
    ocr: 320
  },
  tokens: {
    today: '12.5k',
    month: '340k',
    distribution: [
      { name: 'Gemini Flash', value: 65, color: '#10b981' },
      { name: 'Claude Sonnet', value: 25, color: '#6366f1' },
      { name: 'GPT-4o', value: 10, color: '#f59e0b' },
    ]
  },
  logins: [
    { time: '2026-03-18 14:30', ip: '114.32.1.45', device: 'Chrome / macOS' },
    { time: '2026-03-18 09:15', ip: '114.32.1.45', device: 'Chrome / macOS' },
    { time: '2026-03-17 21:00', ip: '223.140.5.12', device: 'Safari / iPhone' },
    { time: '2026-03-17 10:20', ip: '114.32.1.45', device: 'Chrome / macOS' },
  ],
  abnormal: [
    { type: 'Rate Limit', detail: '10 分鐘內超過 100 次請求', time: '2026-03-10' },
    { type: 'Moderation', detail: '上傳檔案包含敏感關鍵字', time: '2026-02-28' },
  ]
};

export default function UserDetailsPage() {
  const params = useParams();
  const userId = params.userId;

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
              <button className="py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold hover:bg-emerald-600 transition-all flex items-center justify-center gap-2">
                <ShieldCheck className="h-4 w-4" /> 恢復正常
              </button>
              <button className="py-2 bg-white border border-slate-200 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-50 transition-all flex items-center justify-center gap-2">
                <ShieldAlert className="h-4 w-4" /> 停權帳號
              </button>
            </div>
          </section>

          {/* Subscription Details */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h3 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-indigo-500" /> 訂閱狀態
            </h3>
            <div className="space-y-4">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">當前方案</p>
                <div className="flex justify-between items-end">
                  <p className="text-lg font-bold text-slate-900">{userData.tier}</p>
                  <p className="text-xs text-slate-500">到期日: {userData.expiry}</p>
                </div>
              </div>
              <div className="flex justify-between text-sm px-2">
                <span className="text-slate-500">Stripe ID</span>
                <span className="font-mono text-slate-900 flex items-center gap-1">
                  {userData.stripeId} <ExternalLink className="h-3 w-3" />
                </span>
              </div>
              <button className="w-full py-3 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition-all">
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
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: '45%' }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                      <span>本月 Token 用量</span>
                      <span className="text-indigo-600">{userData.tokens.month}</span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: '68%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
              <button className="mt-8 w-full py-3 border border-slate-200 rounded-xl text-sm font-bold text-slate-600 hover:bg-slate-50 transition-all">
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
    </div>
  );
}
