/**
 * @file 考古題匯入儀表板統計卡片群——進行中、成功率、失敗、總匯入題數。
 */
'use client';

import { motion } from 'motion/react';
import { TrendingUp, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import type { ImportDashboardStats } from '@/types/models';

/**
 * ImportDashboardStatsCard 的 props。
 */
interface ImportDashboardStatsProps {
  /** 後端聚合統計資料；null 表示 API 失敗 */
  stats: ImportDashboardStats | null;
  /** 是否載入中（顯示骨架圖） */
  loading?: boolean;
}

/**
 * 考古題匯入儀表板統計卡片群。
 *
 * 以 4 張卡片呈現工作佇列狀態與匯入量；loading 時顯示灰色骨架，stats=null 顯示提示文字。
 *
 * @param props.stats - 統計資料
 * @param props.loading - 載入狀態
 */
export default function ImportDashboardStatsCard({
  stats,
  loading = false,
}: ImportDashboardStatsProps) {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-slate-200 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-8 text-slate-500">
        無法載入統計資訊
      </div>
    );
  }

  return (
    <motion.div
      className="grid grid-cols-1 md:grid-cols-4 gap-4"
      variants={container}
      initial="hidden"
      animate="show"
    >
      <StatsCard
        icon={<Clock className="h-5 w-5" />}
        label="進行中"
        value={stats.jobQueue.inProgress}
        change={`${stats.jobQueue.processing} 處理中`}
        variant="blue"
      />

      <StatsCard
        icon={<CheckCircle className="h-5 w-5" />}
        label="成功率"
        value={`${stats.successMetrics.successRate.toFixed(1)}%`}
        change={`${stats.successMetrics.successfulJobs} 個完成`}
        variant="green"
      />

      <StatsCard
        icon={<AlertCircle className="h-5 w-5" />}
        label="失敗任務"
        value={stats.jobQueue.failed}
        change={`${stats.successMetrics.failedJobs} 失敗`}
        variant="red"
      />

      <StatsCard
        icon={<TrendingUp className="h-5 w-5" />}
        label="已匯入題目"
        value={stats.importVolume.totalQuestionsImported}
        change={`平均 ${stats.importVolume.averageQuestionsPerJob} 題/工作`}
        variant="purple"
      />
    </motion.div>
  );
}

/**
 * 內部 StatsCard 的 props。
 */
interface StatsCardProps {
  /** 卡片圖示 */
  icon: React.ReactNode;
  /** 指標名稱 */
  label: string;
  /** 主數值 */
  value: string | number;
  /** 副說明（如變化量、組成） */
  change: string;
  /** 卡片色調 */
  variant: 'blue' | 'green' | 'red' | 'purple';
}

const variantStyles: Record<string, { bg: string; text: string; icon: string }> = {
  blue: {
    bg: 'bg-blue-50',
    text: 'text-blue-700',
    icon: 'text-blue-500',
  },
  green: {
    bg: 'bg-green-50',
    text: 'text-green-700',
    icon: 'text-green-500',
  },
  red: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    icon: 'text-red-500',
  },
  purple: {
    bg: 'bg-purple-50',
    text: 'text-purple-700',
    icon: 'text-purple-500',
  },
};

/**
 * 單張統計卡片（內部子元件）。
 *
 * @param props.icon - 卡片圖示
 * @param props.label - 指標名稱
 * @param props.value - 主數值
 * @param props.change - 副說明
 * @param props.variant - 色調
 */
function StatsCard({ icon, label, value, change, variant }: StatsCardProps) {
  const styles = variantStyles[variant];

  return (
    <motion.div
      className={`p-4 rounded-lg border ${styles.bg}`}
      variants={{
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0 },
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <span className={`text-sm font-medium ${styles.text}`}>{label}</span>
        <div className={`${styles.icon}`}>{icon}</div>
      </div>

      <div className="space-y-1">
        <p className="text-2xl font-bold text-slate-800">{value}</p>
        <p className="text-xs text-slate-600">{change}</p>
      </div>
    </motion.div>
  );
}
