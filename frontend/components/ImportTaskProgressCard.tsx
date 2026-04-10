'use client';

import { motion } from 'motion/react';
import { CheckCircle, AlertCircle, Clock, Loader } from 'lucide-react';
import type { ImportTask } from '@/types/models';

interface ImportTaskProgressCardProps {
  task: ImportTask;
}

export default function ImportTaskProgressCard({ task }: ImportTaskProgressCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' };
      case 'failed':
        return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' };
      case 'cancelled':
        return { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' };
      default:
        return { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' };
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'cancelled':
        return <Clock className="h-5 w-5 text-yellow-600" />;
      default:
        return <Loader className="h-5 w-5 text-blue-600 animate-spin" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: '等待中',
      processing: '處理中',
      validating: '驗證中',
      importing: '匯入中',
      completed: '完成',
      failed: '失敗',
      cancelled: '已取消',
    };
    return labels[status] || status;
  };

  const statusColors = getStatusColor(task.status);
  const durationSeconds = task.completedAt && task.startedAt
    ? Math.floor((new Date(task.completedAt).getTime() - new Date(task.startedAt).getTime()) / 1000)
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-lg border p-4 space-y-4 ${statusColors.bg} ${statusColors.border}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {getStatusIcon(task.status)}
          <div>
            <p className="text-sm font-semibold text-slate-800">
              {task.examCode}/{task.categoryCode}/{task.subjectCode}
            </p>
            <p className={`text-xs ${statusColors.text}`}>
              {getStatusLabel(task.status)}
            </p>
          </div>
        </div>
        <span className="text-xs text-slate-500">{task.taskId}</span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-600">
          <span>進度</span>
          <span>{task.progressPercent}%</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${task.progressPercent}%` }}
            transition={{ duration: 0.3 }}
            className={`h-full ${
              task.status === 'failed'
                ? 'bg-red-500'
                : task.status === 'completed'
                  ? 'bg-green-500'
                  : 'bg-blue-500'
            }`}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <StatItem label="已處理" value={`${task.questionsProcessed}/${task.totalQuestions}`} />
        <StatItem label="有效題目" value={task.questionsValid} />
        <StatItem label="已匯入" value={task.questionsImported} />
        {durationSeconds && <StatItem label="耗時" value={`${durationSeconds}s`} />}
      </div>

      {/* Error Message */}
      {task.status === 'failed' && task.errorMessage && (
        <div className="p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
          <p className="font-medium">錯誤</p>
          <p className="mt-1">{task.errorMessage}</p>
          {task.validationErrors && task.validationErrors.length > 0 && (
            <div className="mt-2 space-y-1">
              {task.validationErrors.slice(0, 2).map((err, idx) => (
                <p key={idx} className="text-[11px]">• {err}</p>
              ))}
              {task.validationErrors.length > 2 && (
                <p className="text-[11px]">• 還有 {task.validationErrors.length - 2} 個錯誤...</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Manual Review Flag */}
      {task.requiresManualReview && (
        <div className="p-2 bg-yellow-100 border border-yellow-300 rounded text-xs text-yellow-700">
          ⚠️ 此任務需要人工審查
        </div>
      )}
    </motion.div>
  );
}

interface StatItemProps {
  label: string;
  value: string | number;
}

function StatItem({ label, value }: StatItemProps) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-600">{label}:</span>
      <span className="font-semibold text-slate-800">{value}</span>
    </div>
  );
}
