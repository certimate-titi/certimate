'use client';

import { motion } from 'motion/react';
import { CheckCircle, AlertCircle, Clock, XCircle } from 'lucide-react';
import type { RecentJob, FailedJob } from '@/types/models';

interface ImportJobsListProps {
  jobs: RecentJob[] | FailedJob[];
  type: 'recent' | 'failed';
  loading?: boolean;
}

export default function ImportJobsList({
  jobs,
  type,
  loading = false,
}: ImportJobsListProps) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-slate-200 rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        {type === 'recent' ? '暫無最近的工作' : '暫無失敗的工作'}
      </div>
    );
  }

  return (
    <motion.div
      className="space-y-2"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {jobs.map((job, idx) => (
        <JobRow
          key={`${job.taskId}-${idx}`}
          job={job}
          type={type}
        />
      ))}
    </motion.div>
  );
}

interface JobRowProps {
  job: RecentJob | FailedJob;
  type: 'recent' | 'failed';
}

function JobRow({ job, type }: JobRowProps) {
  const isFailedJob = (job: any): job is FailedJob => 'errorMessage' in job;
  const isRecentJob = (job: any): job is RecentJob => 'progressPercent' in job;

  if (isRecentJob(job)) {
    const getStatusIcon = () => {
      switch (job.status) {
        case 'completed':
          return <CheckCircle className="h-4 w-4 text-green-600" />;
        case 'failed':
          return <AlertCircle className="h-4 w-4 text-red-600" />;
        case 'cancelled':
          return <XCircle className="h-4 w-4 text-yellow-600" />;
        default:
          return <Clock className="h-4 w-4 text-blue-600" />;
      }
    };

    const getStatusLabel = () => {
      const labels: Record<string, string> = {
        pending: '等待中',
        processing: '處理中',
        validating: '驗證中',
        importing: '匯入中',
        completed: '完成',
        failed: '失敗',
        cancelled: '已取消',
      };
      return labels[job.status] || job.status;
    };

    return (
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-lg hover:shadow-md transition-shadow"
      >
        {getStatusIcon()}
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-800">{job.exam}</p>
          <p className="text-xs text-slate-500">
            {job.questionsImported}/{job.totalQuestions} 題 · {getStatusLabel()}
          </p>
        </div>
        <div className="text-right">
          <div className="w-20 h-2 bg-slate-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${job.progressPercent}%` }}
              className={`h-full ${
                job.status === 'completed'
                  ? 'bg-green-500'
                  : job.status === 'failed'
                    ? 'bg-red-500'
                    : 'bg-blue-500'
              }`}
            />
          </div>
          <p className="text-xs text-slate-500 mt-1">{job.progressPercent}%</p>
        </div>
      </motion.div>
    );
  }

  if (isFailedJob(job)) {
    return (
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg"
      >
        <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">{job.exam}</p>
          <p className="text-xs text-red-700 mt-1">
            {job.errorMessage || '未知錯誤'}
          </p>
          <div className="flex gap-2 mt-2 text-xs">
            <span className="text-red-600">重試次數: {job.retryCount}/3</span>
            {job.canRetry && (
              <button className="text-blue-600 hover:underline">
                重新嘗試
              </button>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  return null;
}
