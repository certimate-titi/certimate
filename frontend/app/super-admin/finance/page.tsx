'use client';

import React from 'react';
import { 
  CreditCard, 
  DollarSign, 
  TrendingUp, 
  ArrowUpRight, 
  ArrowDownRight,
  Download,
  Filter,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Mock Data
const mrrTrendData = [
  { name: '03/12', new: 1200, expansion: 400, churn: 150 },
  { name: '03/13', new: 1350, expansion: 450, churn: 100 },
  { name: '03/14', new: 1100, expansion: 300, churn: 200 },
  { name: '03/15', new: 1450, expansion: 500, churn: 120 },
  { name: '03/16', new: 1600, expansion: 600, churn: 80 },
  { name: '03/17', new: 1550, expansion: 550, churn: 110 },
  { name: '03/18', new: 1720, expansion: 650, churn: 90 },
];

const planDistribution = [
  { name: 'Free', value: 3500, color: '#94a3b8' },
  { name: 'Pro', value: 1250, color: '#10b981' },
  { name: 'Ultra', value: 500, color: '#6366f1' },
];

const transactions = [
  { id: 'txn_1', user: '張小明', amount: '$29.99', plan: 'Ultra', status: 'success', time: '2026-03-18 14:30' },
  { id: 'txn_2', user: '李華', amount: '$14.99', plan: 'Pro', status: 'success', time: '2026-03-18 10:15' },
  { id: 'txn_3', user: '王大同', amount: '$29.99', plan: 'Ultra', status: 'failed', time: '2026-03-18 09:00' },
  { id: 'txn_4', user: '陳美玲', amount: '$29.99', plan: 'Ultra', status: 'success', time: '2026-03-17 15:45' },
  { id: 'txn_5', user: '林志豪', amount: '$14.99', plan: 'Pro', status: 'refunded', time: '2026-03-17 22:30' },
];

const financeKpis = [
  { label: 'MRR (每月經常性收入)', value: '$15,200', trend: '+15.2%', icon: DollarSign, color: 'emerald' },
  { label: 'ARPU (平均用戶收入)', value: '$3.1', trend: '+5.4%', icon: TrendingUp, color: 'blue' },
  { label: 'Churn Rate (流失率)', value: '2.4%', trend: '-0.5%', icon: ArrowDownRight, color: 'rose' },
  { label: 'LTV (終身價值)', value: '$145', trend: '+8.2%', icon: CreditCard, color: 'indigo' },
];

export default function FinancePage() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">財務與訂閱管理</h1>
          <p className="text-slate-500">掌握金流狀況、訂閱轉換與成本分析</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center gap-2">
            <Download className="h-4 w-4" /> 匯出財務報表
          </button>
        </div>
      </div>

      {/* Finance KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {financeKpis.map((kpi) => (
          <div key={kpi.label} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
            <div className="flex justify-between items-start mb-4">
              <div className={cn(
                "p-2 rounded-xl",
                kpi.color === 'emerald' && "bg-emerald-50 text-emerald-600",
                kpi.color === 'blue' && "bg-blue-50 text-blue-600",
                kpi.color === 'rose' && "bg-rose-50 text-rose-600",
                kpi.color === 'indigo' && "bg-indigo-50 text-indigo-600"
              )}>
                <kpi.icon className="h-5 w-5" />
              </div>
              <span className={cn(
                "text-xs font-bold px-2 py-1 rounded-lg",
                kpi.trend.startsWith('+') || kpi.trend.startsWith('-') ? "bg-emerald-50 text-emerald-600" : "bg-slate-50 text-slate-600"
              )}>
                {kpi.trend}
              </span>
            </div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{kpi.label}</p>
            <p className="text-xl font-bold text-slate-900">{kpi.value}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* MRR Trend Chart */}
        <section className="lg:col-span-2 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h2 className="font-bold text-slate-900 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-500" /> MRR 趨勢分析
            </h2>
            <div className="flex gap-2">
              <button className="px-3 py-1 text-xs font-bold bg-emerald-50 text-emerald-600 rounded-lg">New MRR</button>
              <button className="px-3 py-1 text-xs font-bold bg-indigo-50 text-indigo-600 rounded-lg">Expansion</button>
              <button className="px-3 py-1 text-xs font-bold bg-rose-50 text-rose-600 rounded-lg">Churn</button>
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mrrTrendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0' }}
                />
                <Area type="monotone" dataKey="new" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.1} />
                <Area type="monotone" dataKey="expansion" stackId="1" stroke="#6366f1" fill="#6366f1" fillOpacity={0.1} />
                <Area type="monotone" dataKey="churn" stackId="1" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Plan Distribution */}
        <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
          <h2 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
            <PieChartIcon className="h-5 w-5 text-indigo-500" /> 方案分布
          </h2>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={planDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {planDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" align="center" iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-6 space-y-3">
            {planDistribution.map((plan) => (
              <div key={plan.name} className="flex justify-between items-center text-sm">
                <span className="text-slate-500">{plan.name}</span>
                <span className="font-bold text-slate-900">{plan.value} 用戶</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Transaction Table */}
      <section className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center">
          <h2 className="font-bold text-slate-900 flex items-center gap-2">
            <CreditCard className="h-5 w-5 text-blue-500" /> 近期交易紀錄
          </h2>
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input 
                type="text" 
                placeholder="搜尋交易 ID 或用戶..." 
                className="pl-10 pr-4 py-1.5 bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-lg text-xs transition-all outline-none"
              />
            </div>
            <button className="p-1.5 bg-slate-50 border-transparent hover:bg-slate-100 rounded-lg transition-all">
              <Filter className="h-4 w-4 text-slate-500" />
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">交易 ID</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">用戶</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">金額</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">方案</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">狀態</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">時間</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {transactions.map((txn) => (
                <tr key={txn.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4 text-sm font-mono text-slate-500">{txn.id}</td>
                  <td className="px-6 py-4 text-sm font-bold text-slate-900">{txn.user}</td>
                  <td className="px-6 py-4 text-sm font-bold text-slate-900">{txn.amount}</td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "text-xs font-bold px-2 py-1 rounded-lg",
                      txn.plan === 'Ultra' ? "bg-indigo-50 text-indigo-600" : "bg-emerald-50 text-emerald-600"
                    )}>
                      {txn.plan}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {txn.status === 'success' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                      {txn.status === 'failed' && <XCircle className="h-4 w-4 text-rose-500" />}
                      {txn.status === 'refunded' && <Clock className="h-4 w-4 text-amber-500" />}
                      <span className={cn(
                        "text-xs font-medium",
                        txn.status === 'success' && "text-emerald-600",
                        txn.status === 'failed' && "text-rose-600",
                        txn.status === 'refunded' && "text-amber-600"
                      )}>
                        {txn.status === 'success' && "交易成功"}
                        {txn.status === 'failed' && "交易失敗"}
                        {txn.status === 'refunded' && "已退款"}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">{txn.time}</td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-xs font-bold text-emerald-600 hover:text-emerald-700 transition-all">
                      詳情
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
