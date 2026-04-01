'use client';

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { superAdminService } from '@/lib/api/services';
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

interface FinanceOverview {
  mrr: number;
  arpu: number;
  churn_rate: number;
  ltv: number;
  mrr_trend: string;
  arpu_trend: string;
  churn_trend: string;
  ltv_trend: string;
}

function buildFinanceKpis(data: FinanceOverview | null) {
  if (!data) {
    return [
      { label: '每月經常性收入', value: '--', trend: '--', icon: DollarSign, color: 'emerald' },
      { label: '平均用戶收入', value: '--', trend: '--', icon: TrendingUp, color: 'blue' },
      { label: '用戶流失率', value: '--', trend: '--', icon: ArrowDownRight, color: 'rose' },
      { label: '用戶終身價值', value: '--', trend: '--', icon: CreditCard, color: 'indigo' },
    ];
  }
  return [
    { label: '每月經常性收入', value: `NT$ ${data.mrr.toLocaleString()}`, trend: data.mrr_trend || '--', icon: DollarSign, color: 'emerald' },
    { label: '平均用戶收入', value: `NT$ ${data.arpu.toLocaleString()}`, trend: data.arpu_trend || '--', icon: TrendingUp, color: 'blue' },
    { label: '用戶流失率', value: `${(data.churn_rate * 100).toFixed(1)}%`, trend: data.churn_trend || '--', icon: ArrowDownRight, color: 'rose' },
    { label: '用戶終身價值', value: `NT$ ${data.ltv.toLocaleString()}`, trend: data.ltv_trend || '--', icon: CreditCard, color: 'indigo' },
  ];
}

export default function FinancePage() {
  const [overview, setOverview] = useState<FinanceOverview | null>(null);
  const [mrrTrendData, setMrrTrendData] = useState<{ name: string; new: number; expansion: number; churn: number }[]>([]);
  const [planDistribution, setPlanDistribution] = useState<{ name: string; value: number; color: string }[]>([]);
  const [transactions, setTransactions] = useState<{ id: string; user: string; amount: string; plan: string; status: string; time: string }[]>([]);
  const [txnSearch, setTxnSearch] = useState('');
  const [txnStatusFilter, setTxnStatusFilter] = useState('all');
  const [selectedTxnId, setSelectedTxnId] = useState<string | null>(null);
  const [visibleSeries, setVisibleSeries] = useState({ new: true, expansion: true, churn: true });

  useEffect(() => {
    superAdminService.getFinanceOverview().then(setOverview).catch(() => {});
    superAdminService.getMrrTrend().then(res => {
      if (Array.isArray(res.data)) setMrrTrendData(res.data);
    }).catch(() => {});
    superAdminService.getSubscriptionDistribution().then(res => {
      if (Array.isArray(res.distribution)) setPlanDistribution(res.distribution);
    }).catch(() => {});
    superAdminService.getFinanceTransactions().then(res => {
      if (Array.isArray(res.transactions)) setTransactions(res.transactions);
    }).catch(() => {});
  }, []);

  const financeKpis = buildFinanceKpis(overview);

  const filteredTransactions = transactions.filter(txn => {
    const matchesSearch = !txnSearch || txn.id.toLowerCase().includes(txnSearch.toLowerCase()) || txn.user.toLowerCase().includes(txnSearch.toLowerCase());
    const matchesStatus = txnStatusFilter === 'all' || txn.status === txnStatusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">財務與訂閱管理</h1>
          <p className="text-slate-500">掌握金流狀況、訂閱轉換與成本分析</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={async () => {
              try {
                const { superAdminService } = await import('@/lib/api/services');
                const data = await superAdminService.getFinanceTransactions();
                const json = JSON.stringify(data, null, 2);
                const blob = new Blob([json], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `finance-report-${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
              } catch { alert('匯出失敗，請稍後再試'); }
            }}
            className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-all flex items-center gap-2"
          >
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
              <TrendingUp className="h-5 w-5 text-emerald-500" /> 每月經常性收入趨勢分析
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setVisibleSeries(prev => ({ ...prev, new: !prev.new }))}
                className={cn("px-3 py-1 text-xs font-bold bg-emerald-50 text-emerald-600 rounded-lg transition-all", !visibleSeries.new && "opacity-40")}
              >
                新增收入
              </button>
              <button
                onClick={() => setVisibleSeries(prev => ({ ...prev, expansion: !prev.expansion }))}
                className={cn("px-3 py-1 text-xs font-bold bg-indigo-50 text-indigo-600 rounded-lg transition-all", !visibleSeries.expansion && "opacity-40")}
              >
                擴增收入
              </button>
              <button
                onClick={() => setVisibleSeries(prev => ({ ...prev, churn: !prev.churn }))}
                className={cn("px-3 py-1 text-xs font-bold bg-rose-50 text-rose-600 rounded-lg transition-all", !visibleSeries.churn && "opacity-40")}
              >
                流失收入
              </button>
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
                {visibleSeries.new && <Area type="monotone" dataKey="new" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.1} />}
                {visibleSeries.expansion && <Area type="monotone" dataKey="expansion" stackId="1" stroke="#6366f1" fill="#6366f1" fillOpacity={0.1} />}
                {visibleSeries.churn && <Area type="monotone" dataKey="churn" stackId="1" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.1} />}
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
                  {(Array.isArray(planDistribution) ? planDistribution : []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" align="center" iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-6 space-y-3">
            {(Array.isArray(planDistribution) ? planDistribution : []).map((plan) => (
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
                value={txnSearch}
                onChange={(e) => setTxnSearch(e.target.value)}
                className="pl-10 pr-4 py-1.5 bg-slate-50 border-transparent focus:bg-white focus:border-emerald-500 rounded-lg text-xs transition-all outline-none"
              />
            </div>
            <select
              value={txnStatusFilter}
              onChange={(e) => setTxnStatusFilter(e.target.value)}
              className="bg-slate-50 border-transparent rounded-lg text-xs px-3 py-1.5 outline-none"
            >
              <option value="all">全部狀態</option>
              <option value="success">交易成功</option>
              <option value="failed">交易失敗</option>
              <option value="refunded">已退款</option>
            </select>
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
              {filteredTransactions.map((txn) => (
                <React.Fragment key={txn.id}>
                <tr className="hover:bg-slate-50/50 transition-colors">
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
                    <button
                      onClick={() => setSelectedTxnId(selectedTxnId === txn.id ? null : txn.id)}
                      className="text-xs font-bold text-emerald-600 hover:text-emerald-700 transition-all"
                    >
                      {selectedTxnId === txn.id ? '收合' : '詳情'}
                    </button>
                  </td>
                </tr>
                {selectedTxnId === txn.id && (
                  <tr className="bg-slate-50">
                    <td colSpan={7} className="px-6 py-4">
                      <div className="grid grid-cols-3 gap-4 text-xs">
                        <div><span className="text-slate-500">交易 ID：</span><span className="font-mono font-bold">{txn.id}</span></div>
                        <div><span className="text-slate-500">用戶：</span><span className="font-bold">{txn.user}</span></div>
                        <div><span className="text-slate-500">金額：</span><span className="font-bold">{txn.amount}</span></div>
                        <div><span className="text-slate-500">方案：</span><span className="font-bold">{txn.plan}</span></div>
                        <div><span className="text-slate-500">狀態：</span><span className="font-bold">{txn.status === 'success' ? '交易成功' : txn.status === 'failed' ? '交易失敗' : '已退款'}</span></div>
                        <div><span className="text-slate-500">時間：</span><span className="font-bold">{txn.time}</span></div>
                      </div>
                    </td>
                  </tr>
                )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
