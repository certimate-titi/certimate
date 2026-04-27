/**
 * @file 考古題匯入任務輪詢 hook。週期性向後端拉取 task 狀態，
 * 進入終態（completed / failed / cancelled）後自動停止 polling 並觸發 callback。
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { importService } from '@/lib/api/services';
import type { ImportTask } from '@/types/models';

/**
 * `useImportTaskPolling` 的設定參數。
 */
interface UseImportTaskPollingOptions {
  /** 要輪詢的匯入任務 ID。 */
  taskId: string;
  /** 是否啟用輪詢；`false` 時不會發出任何請求。預設 `true`。 */
  enabled?: boolean;
  /** 輪詢間隔（毫秒）。預設 2000。 */
  intervalMs?: number;
  /** 任務進入終態時呼叫一次。 */
  onComplete?: (task: ImportTask) => void;
  /** 拉取失敗時呼叫，error 為標準 Error 物件。 */
  onError?: (error: Error) => void;
}

/**
 * 即時輪詢考古題匯入任務狀態。
 *
 * 每 `intervalMs` 毫秒（預設 2 秒）向後端拉一次狀態，直到任務 `completed`、
 * `failed` 或 `cancelled` 才停止；同時暴露衍生的布林旗標供 UI 直接渲染。
 *
 * @param options - 詳見 {@link UseImportTaskPollingOptions}。
 * @returns 物件含 `task`、`loading`、`error` 與四個狀態旗標
 *          (`isCompleted` / `isFailed` / `isCancelled` / `isInProgress`)。
 *
 * @example
 * const { task, isInProgress } = useImportTaskPolling({
 *   taskId,
 *   onComplete: (t) => toast.success(`匯入完成：${t.imported_count}`),
 * });
 */
export function useImportTaskPolling({
  taskId,
  enabled = true,
  intervalMs = 2000,
  onComplete,
  onError,
}: UseImportTaskPollingOptions) {
  const [task, setTask] = useState<ImportTask | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchTask = async () => {
    try {
      const result = await importService.getTaskStatus(taskId);
      if (result) {
        setTask(result);
        setError(null);

        // Check if task is in a terminal state
        if (['completed', 'failed', 'cancelled'].includes(result.status)) {
          // Stop polling
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onComplete?.(result);
        }
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      onError?.(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!enabled || !taskId) return;

    // Fetch immediately
    fetchTask();

    // Set up polling
    intervalRef.current = setInterval(fetchTask, intervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, taskId, intervalMs]);

  return {
    task,
    loading,
    error,
    isCompleted: task?.status === 'completed',
    isFailed: task?.status === 'failed',
    isCancelled: task?.status === 'cancelled',
    isInProgress: ['pending', 'processing', 'validating', 'importing'].includes(task?.status || ''),
  };
}
