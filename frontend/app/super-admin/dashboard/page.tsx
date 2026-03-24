'use client';

import React from 'react';
import { 
  Users, 
  TrendingUp, 
  DollarSign, 
  Cpu, 
  AlertTriangle, 
  ArrowUpRight, 
  ArrowDownRight,
  Activity,
  Zap,
  Clock
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
  BarChart,
  Bar,
  Legend
} from 'recharts';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Mock Data
const userGrowthData = [
  { name: '03/12', dau: 1200, mau: 4500 },
  { name: '03/13', dau: 1350, mau: 4600 },
  { name: '03/14', dau: 1100, mau: 4650 },
  { name: '03/15', dau: 1450, mau: 4800 },
  { name: '03/16', dau: 1600, mau: 5000 },
  { name: '03/17', dau: 1550, mau: 5100 },
  { name: '03/18', dau: 1720, mau: 5250 },
];

const revenueData = [
  { name: '03/12', mrr: 12000, arpu: 2.5 },
  { name: '03/13', mrr: 12500, arpu: 2.6 },
  { name: '03/14', mrr: 12800, arpu: 2.7 },
  { name: '03/15', mrr: 13200, arpu: 2.8 },
  { name: '03/16', mrr: 14000, arpu: 2.9 },
  { name: '03/17', mrr: 14500, arpu: 3.0 },
  { name: '03/18', mrr: 15200, arpu: 3.1 },
];

const aiCostData = [
  { name: '03/12', gemini: 45, claude: 30, gpt4: 25 },
  { name: '03/13', gemini: 50, claude: 35, gpt4: 28 },
  { name: '03/14', gemini: 48, claude: 32, gpt4: 26 },
  { name: '03/15', gemini: 55, claude: 40, gpt4: 30 },
  { name: '03/16', gemini: 60, claude: 45, gpt4: 35 },
  { name: '03/17', gemini: 58, claude: 42, gpt4: 32 },
  { name: '03/18', gemini: 65, claude: 50, gpt4: 40 },
];

const kpiCards = [
  { label: 'DAU / MAU', value: '1,720 / 5,250', trend: '+12.5%', icon: Users, color: 'emerald' },
  { label: '今日新註冊', value: '142', trend: '+8.2%', icon: TrendingUp, color: 'blue' },
  { label: '訂閱轉換率', value: '4.8%', trend: '+0.5%', icon: Zap, color: 'amber' },
  { label: 'MRR (每月營收)', value: '$15,200', trend: '+15.2%', icon: DollarSign, color: 'indigo' },
  { label: '今日 AI 成本', value: '$155.2', trend: '+5.4%', icon: Cpu, color: 'rose' },
  { label: '任務佇列', value: '12 任務', trend: '正常', icon: Clock, color: 'slate' },
];

const alerts = [
  { id: 1, type: 'error', message: 'Worker 任務失敗率超過 5%', time: '10 分鐘前' },
  { id: 2, type: 'warning', message: '用戶 ID: 12345 觸發 Rate Limit', time: '25 分鐘前' },
  { id: 3, type: 'info', message: 'Cloud SQL 連線數達到 75%', time: '1 小時前' },
  { id: 4, type: 'warning', message: 'OpenRouter 單日費用接近預算上限', time: '2 小時前' },
];

export default function OperationsDashboard() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">營運儀表板</h1>
          <p className="text-slate-500">即時監控系統健康度與商業指標</p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all">
            匯出報表
          </button>
          <button className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20">
            即時重新整理
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpiCards.map((kpi) => (
          <div key={kpi.label} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all">
            <div className="flex justify-between items-start mb-4">
              <div className={cn(
                "p-2 rounded-xl",
                kpi.color === 'emerald' && "bg-emerald-50 text-emerald-600",
                kpi.color === 'blue' && "bg-blue-50 text-blue-600",
                kpi.color === 'amber' && "bg-amber-50 text-amber-600",
                kpi.color === 'indigo' && "bg-indigo-50 text-indigo-600",
                kpi.color === 'rose' && "bg-rose-50 text-rose-600",
                kpi.color === 'slate' && "bg-slate-50 text-slate-600"
              )}>
                <kpi.icon className="h-5 w-5" />
              </div>
              <span className={cn(
                "text-xs font-bold px-2 py-1 rounded-lg",
                kpi.trend.startsWith('+') ? "bg-emerald-50 text-emerald-600" : "bg-slate-50 text-slate-600"
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
        {/* Charts Section */}
        <div className="lg:col-span-2 space-y-8">
          {/* User Growth Chart */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <Activity className="h-5 w-5 text-emerald-500" /> 用戶成長曲線
              </h2>
              <select className="text-sm border-none bg-slate-50 rounded-lg px-3 py-1 outline-none">
                <option>過去 7 天</option>
                <option>過去 30 天</option>
                <option>過去 90 天</option>
              </select>
            </div>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={userGrowthData}>
                  <defs>
                    <linearGradient id="colorDau" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Area type="monotone" dataKey="dau" stroke="#10b981" fillOpacity={1} fill="url(#colorDau)" strokeWidth={3} />
                  <Area type="monotone" dataKey="mau" stroke="#94a3b8" fill="transparent" strokeWidth={2} strokeDasharray="5 5" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* AI Cost Analysis */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <h2 className="font-bold text-slate-900 flex items-center gap-2">
                <Cpu className="h-5 w-5 text-rose-500" /> AI 成本分析 (USD)
              </h2>
            </div>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={aiCostData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                  <Tooltip 
                    cursor={{ fill: '#f8fafc' }}
                    contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0' }}
                  />
                  <Legend verticalAlign="top" align="right" iconType="circle" wrapperStyle={{ paddingBottom: '20px' }} />
                  <Bar dataKey="gemini" name="Gemini" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="claude" name="Claude" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="gpt4" name="GPT-4" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>

        {/* Sidebar Section: Alerts & Load */}
        <div className="space-y-8">
          {/* Alerts */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" /> 近期異常警報
            </h2>
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex gap-4 p-4 rounded-2xl bg-slate-50 border border-slate-100 hover:border-slate-200 transition-all group">
                  <div className={cn(
                    "h-2 w-2 rounded-full mt-1.5 shrink-0",
                    alert.type === 'error' && "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]",
                    alert.type === 'warning' && "bg-amber-500",
                    alert.type === 'info' && "bg-blue-500"
                  )}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900 leading-tight mb-1">{alert.message}</p>
                    <p className="text-xs text-slate-500">{alert.time}</p>
                  </div>
                  <button className="opacity-0 group-hover:opacity-100 text-xs font-bold text-emerald-600 hover:text-emerald-700 transition-all">
                    處理
                  </button>
                </div>
              ))}
            </div>
            <button className="w-full mt-6 py-3 text-sm font-bold text-slate-500 hover:text-slate-900 transition-all">
              查看所有警報 &rarr;
            </button>
          </section>

          {/* System Load */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <Activity className="h-5 w-5 text-indigo-500" /> 系統負載儀表
            </h2>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  <span>Cloud Run CPU</span>
                  <span className="text-emerald-600">32%</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: '32%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  <span>Cloud SQL 連線數</span>
                  <span className="text-amber-600">75%</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: '75%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  <span>Redis 快取命中率</span>
                  <span className="text-indigo-600">94%</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 rounded-full" style={{ width: '94%' }}></div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
