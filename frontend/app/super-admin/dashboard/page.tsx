'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api/client';
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

import { superAdminService } from '@/lib/api/services';

interface DashboardData {
  dau: number;
  mau: number;
  new_registrations: number;
  conversion_rate: number;
  mrr: number;
  ai_token_today: number;
  queue_depth: number;
}

function buildKpiCards(data: DashboardData | null): { label: string; value: string; sub?: string; change: string; changeDir: 'up' | 'down' | 'neutral'; icon: typeof Users; color: string }[] {
  if (!data) {
    return [
      { label: '日活躍 / 月活躍用戶', value: '--', change: '--', changeDir: 'neutral', icon: Users, color: 'emerald' },
      { label: '新註冊', value: '--', sub: '本週', change: '--', changeDir: 'neutral', icon: TrendingUp, color: 'blue' },
      { label: '轉換率', value: '--', change: '--', changeDir: 'neutral', icon: Zap, color: 'amber' },
      { label: '每月經常性收入', value: '--', change: '--', changeDir: 'neutral', icon: DollarSign, color: 'indigo' },
      { label: 'AI 使用成本', value: '--', change: '--', changeDir: 'neutral', icon: Cpu, color: 'rose' },
      { label: '任務佇列', value: '--', change: '--', changeDir: 'neutral', icon: Clock, color: 'slate' },
    ];
  }
  return [
    { label: '日活躍 / 月活躍用戶', value: `${data.dau.toLocaleString()} / ${data.mau.toLocaleString()}`, change: '--', changeDir: 'neutral', icon: Users, color: 'emerald' },
    { label: '新註冊', value: data.new_registrations.toLocaleString(), sub: '本週', change: '--', changeDir: 'neutral', icon: TrendingUp, color: 'blue' },
    { label: '轉換率', value: `${(data.conversion_rate * 100).toFixed(1)}%`, change: '--', changeDir: 'neutral', icon: Zap, color: 'amber' },
    { label: '每月經常性收入', value: `NT$ ${data.mrr.toLocaleString()}`, change: '--', changeDir: 'neutral', icon: DollarSign, color: 'indigo' },
    { label: 'AI 使用成本', value: data.ai_token_today.toLocaleString(), change: '--', changeDir: 'neutral', icon: Cpu, color: 'rose' },
    { label: '任務佇列', value: data.queue_depth.toLocaleString(), change: '--', changeDir: 'neutral', icon: Clock, color: 'slate' },
  ];
}

export default function OperationsDashboard() {
  const router = useRouter();
  const [dashData, setDashData] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<{ id: number; type: string; message: string; time: string }[]>([]);
  const [systemAlerts, setSystemAlerts] = useState<{ severity: string; message: string; time: string }[]>([]);
  const [systemLoad, setSystemLoad] = useState({ cpu_percent: 0, db_connections_percent: 0, cache_hit_rate: 0 });
  const [userGrowthData, setUserGrowthData] = useState<{ name: string; dau: number; mau: number }[]>([]);
  const [aiCostData, setAiCostData] = useState<{ name: string; gemini: number; claude: number; gpt4: number }[]>([]);

  useEffect(() => {
    apiClient.get<DashboardData>('/admin/dashboard').then(setDashData).catch(() => {});
    superAdminService.getDashboardAlerts().then(res => {
      if (Array.isArray(res?.alerts)) setAlerts(res.alerts);
      if (Array.isArray(res?.system_alerts)) setSystemAlerts(res.system_alerts);
    }).catch(() => {});
    superAdminService.getSystemLoad().then(res => {
      if (res && typeof res.cpu_percent === 'number') setSystemLoad(res);
    }).catch(() => {});
    superAdminService.getDashboardCharts().then(res => {
      if (Array.isArray(res?.user_growth)) setUserGrowthData(res.user_growth);
      if (Array.isArray(res?.ai_cost)) setAiCostData(res.ai_cost);
    }).catch(() => {});
  }, []);

  const kpiCards = buildKpiCards(dashData);

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">營運儀表板</h1>
          <p className="text-slate-500">即時監控系統健康度與商業指標</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={async () => {
              try {
                const blob = await superAdminService.exportUsersCSV();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `dashboard-report-${new Date().toISOString().split('T')[0]}.csv`;
                a.click();
                URL.revokeObjectURL(url);
              } catch { alert('匯出失敗，請稍後再試'); }
            }}
            className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all"
          >
            匯出報表
          </button>
          <button
            onClick={() => {
              apiClient.get<DashboardData>('/admin/dashboard').then(setDashData).catch(() => {});
              superAdminService.getDashboardAlerts().then(res => { if (Array.isArray(res?.alerts)) setAlerts(res.alerts); if (Array.isArray(res?.system_alerts)) setSystemAlerts(res.system_alerts); }).catch(() => {});
              superAdminService.getSystemLoad().then(res => { if (res && typeof res.cpu_percent === 'number') setSystemLoad(res); }).catch(() => {});
              superAdminService.getDashboardCharts().then(res => { if (Array.isArray(res?.user_growth)) setUserGrowthData(res.user_growth); if (Array.isArray(res?.ai_cost)) setAiCostData(res.ai_cost); }).catch(() => {});
            }}
            className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-all shadow-lg shadow-emerald-500/20"
          >
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
                "text-[10px] font-bold px-1.5 py-0.5 rounded-lg inline-flex items-center gap-0.5",
                kpi.changeDir === 'up' ? "bg-emerald-50 text-emerald-600" : "bg-slate-50 text-slate-600"
              )}>
                {kpi.changeDir === 'up' && <ArrowUpRight className="h-3 w-3" />}
                {kpi.change}
              </span>
            </div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">
              {kpi.label}
              {kpi.sub && <span className="normal-case ml-1">({kpi.sub})</span>}
            </p>
            <p className="text-2xl font-extrabold text-slate-900 tracking-tight">{kpi.value}</p>
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
                  <button
                    onClick={() => router.push('/super-admin/moderation')}
                    className="opacity-0 group-hover:opacity-100 text-xs font-bold text-emerald-600 hover:text-emerald-700 transition-all"
                  >
                    處理
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={() => router.push('/super-admin/audit-logs')}
              className="w-full mt-6 py-3 text-sm font-bold text-slate-500 hover:text-slate-900 transition-all"
            >
              查看所有警報 &rarr;
            </button>
          </section>

          {/* System Alerts */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-rose-500" /> 系統警報
            </h2>
            <div className="space-y-3">
              {systemAlerts.map((alert, idx) => (
                <div key={idx} className={cn(
                  "p-4 rounded-2xl border transition-all",
                  alert.severity === 'critical' && "bg-red-50 border-red-200",
                  alert.severity === 'warning' && "bg-amber-50 border-amber-200",
                  alert.severity === 'info' && "bg-blue-50 border-blue-200"
                )}>
                  <div className="flex items-start gap-3">
                    <div className={cn(
                      "h-2 w-2 rounded-full mt-1.5 shrink-0",
                      alert.severity === 'critical' && "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]",
                      alert.severity === 'warning' && "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.4)]",
                      alert.severity === 'info' && "bg-blue-500"
                    )} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn(
                          "text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded",
                          alert.severity === 'critical' && "bg-red-100 text-red-700",
                          alert.severity === 'warning' && "bg-amber-100 text-amber-700",
                          alert.severity === 'info' && "bg-blue-100 text-blue-700"
                        )}>
                          {alert.severity}
                        </span>
                      </div>
                      <p className={cn(
                        "text-sm font-medium leading-tight mb-1",
                        alert.severity === 'critical' && "text-red-900",
                        alert.severity === 'warning' && "text-amber-900",
                        alert.severity === 'info' && "text-blue-900"
                      )}>{alert.message}</p>
                      <p className="text-xs text-slate-500">{alert.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* System Load */}
          <section className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
            <h2 className="font-bold text-slate-900 mb-6 flex items-center gap-2">
              <Activity className="h-5 w-5 text-indigo-500" /> 系統負載儀表
            </h2>
            <div className="space-y-6">
              {[
                { label: 'Cloud Run CPU', value: systemLoad.cpu_percent, color: 'emerald' },
                { label: 'Cloud SQL 連線數', value: systemLoad.db_connections_percent, color: 'amber' },
                { label: 'Redis 快取命中率', value: systemLoad.cache_hit_rate, color: 'indigo' },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                    <span>{item.label}</span>
                    <span className={cn(
                      item.color === 'emerald' && "text-emerald-600",
                      item.color === 'amber' && "text-amber-600",
                      item.color === 'indigo' && "text-indigo-600"
                    )}>{item.value}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className={cn(
                      "h-full rounded-full",
                      item.color === 'emerald' && "bg-emerald-500",
                      item.color === 'amber' && "bg-amber-500",
                      item.color === 'indigo' && "bg-indigo-500"
                    )} style={{ width: `${item.value}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
