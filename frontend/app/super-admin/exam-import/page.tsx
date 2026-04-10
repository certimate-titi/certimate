'use client';

import React, { useState, useEffect } from 'react';
import { Upload, Zap, BarChart3, AlertTriangle } from 'lucide-react';
import { motion } from 'motion/react';
import ExamImportForm from '@/components/ExamImportForm';
import ImportDashboardStats from '@/components/ImportDashboardStats';
import ImportJobsList from '@/components/ImportJobsList';
import { importService } from '@/lib/api/services';
import type { ImportDashboardStats as IDashboardStats, RecentJob, FailedJob, ImportPerformanceMetrics } from '@/types/models';

type TabType = 'submit' | 'monitoring' | 'recent' | 'failed' | 'performance';

export default function ExamImportPage() {
  const [activeTab, setActiveTab] = useState<TabType>('monitoring');
  const [stats, setStats] = useState<IDashboardStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<RecentJob[]>([]);
  const [failedJobs, setFailedJobs] = useState<FailedJob[]>([]);
  const [metrics, setMetrics] = useState<ImportPerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [submittingTaskId, setSubmittingTaskId] = useState<string | null>(null);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [statsData, recentJobsData, failedJobsData, metricsData] = await Promise.all([
        importService.getDashboardStats(),
        importService.getRecentJobs(10),
        importService.getFailedJobs(10),
        importService.getPerformanceMetrics(7),
      ]);

      setStats(statsData);
      setRecentJobs(recentJobsData);
      setFailedJobs(failedJobsData);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
    // Set up auto-refresh every 5 seconds
    const interval = setInterval(loadDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  const tabs: Array<{ id: TabType; label: string; icon: React.ReactNode }> = [
    { id: 'submit', label: '提交匯入', icon: <Upload className="h-4 w-4" /> },
    { id: 'monitoring', label: '監控儀表板', icon: <Zap className="h-4 w-4" /> },
    { id: 'recent', label: '最近工作', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'failed', label: '失敗工作', icon: <AlertTriangle className="h-4 w-4" /> },
    { id: 'performance', label: '效能指標', icon: <BarChart3 className="h-4 w-4" /> },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">考古題非同步匯入</h1>
        <p className="text-slate-600 mt-2">Phase 3: 後台管理與監控儀表板</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-slate-200 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Submit Tab */}
        {activeTab === 'submit' && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                ℹ️ 上傳考古題 PDF 檔案。系統將在背景進行異步處理，包括驗證、品質檢查與入庫。
              </p>
            </div>
            <ExamImportForm
              onSuccess={(taskId) => {
                setSubmittingTaskId(taskId);
                setActiveTab('monitoring');
                setTimeout(() => loadDashboard(), 1000);
              }}
            />
            {submittingTaskId && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm text-green-800">
                  ✓ 任務已提交！任務 ID: <code className="font-mono">{submittingTaskId}</code>
                </p>
              </div>
            )}
          </div>
        )}

        {/* Monitoring Tab */}
        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-slate-800">實時統計</h2>
              <button
                onClick={loadDashboard}
                disabled={loading}
                className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '更新中...' : '重新整理'}
              </button>
            </div>
            <ImportDashboardStats stats={stats} loading={loading} />

            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Job Queue Breakdown */}
                <div className="bg-white border border-slate-200 rounded-lg p-4">
                  <h3 className="font-semibold text-slate-800 mb-4">工作佇列狀態</h3>
                  <div className="space-y-2 text-sm">
                    {Object.entries(stats.jobQueue).map(([key, value]) => {
                      if (key === 'totalJobs') return null;
                      return (
                        <div key={key} className="flex justify-between">
                          <span className="text-slate-600 capitalize">
                            {key.replace(/([A-Z])/g, ' $1').trim()}
                          </span>
                          <span className="font-medium text-slate-800">{value}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Success Metrics */}
                <div className="bg-white border border-slate-200 rounded-lg p-4">
                  <h3 className="font-semibold text-slate-800 mb-4">成功指標</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">成功率</span>
                      <span className="font-medium text-green-600">
                        {stats.successMetrics.successRate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">平均耗時</span>
                      <span className="font-medium text-slate-800">
                        {stats.successMetrics.averageDurationSeconds}s
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">平均題數</span>
                      <span className="font-medium text-slate-800">
                        {stats.importVolume.averageQuestionsPerJob} 題/工作
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Recent Jobs Tab */}
        {activeTab === 'recent' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-slate-800">最近 10 個工作</h2>
              <button
                onClick={loadDashboard}
                disabled={loading}
                className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '更新中...' : '重新整理'}
              </button>
            </div>
            <ImportJobsList jobs={recentJobs} type="recent" loading={loading} />
          </div>
        )}

        {/* Failed Jobs Tab */}
        {activeTab === 'failed' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-slate-800">失敗工作列表</h2>
              <button
                onClick={loadDashboard}
                disabled={loading}
                className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? '更新中...' : '重新整理'}
              </button>
            </div>
            <ImportJobsList jobs={failedJobs} type="failed" loading={loading} />
          </div>
        )}

        {/* Performance Metrics Tab */}
        {activeTab === 'performance' && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-800">過去 7 天效能指標</h2>
            {metrics ? (
              <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <MetricItem
                    label="總工作數"
                    value={metrics.metrics.totalJobs}
                  />
                  <MetricItem
                    label="成功工作"
                    value={metrics.metrics.successful}
                  />
                  <MetricItem
                    label="失敗工作"
                    value={metrics.metrics.failed}
                  />
                  <MetricItem
                    label="成功率"
                    value={`${metrics.metrics.successRate.toFixed(1)}%`}
                  />
                  <MetricItem
                    label="平均耗時"
                    value={`${metrics.metrics.averageDurationSeconds}s`}
                  />
                  <MetricItem
                    label="總匯入題目"
                    value={metrics.metrics.totalQuestionsImported}
                  />
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                無法載入效能指標
              </div>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}

interface MetricItemProps {
  label: string;
  value: string | number;
}

function MetricItem({ label, value }: MetricItemProps) {
  return (
    <div className="bg-slate-50 rounded p-3">
      <p className="text-xs text-slate-600">{label}</p>
      <p className="text-lg font-semibold text-slate-800 mt-1">{value}</p>
    </div>
  );
}
