'use client';

import { useEffect, useRef, useState } from 'react';
import { importService } from '@/lib/api/services';
import type { ImportTask } from '@/types/models';

interface UseImportTaskPollingOptions {
  taskId: string;
  enabled?: boolean;
  intervalMs?: number;
  onComplete?: (task: ImportTask) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook to poll import task status in real-time
 * Polls the backend every N milliseconds (default 2s) until task completes or fails
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
