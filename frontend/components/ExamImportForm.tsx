/**
 * @file 考古題匯入表單——上傳試題 / 答案 PDF 並送出非同步匯入任務。
 */
'use client';

import { useState } from 'react';
import { Upload, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { motion } from 'motion/react';
import { importService } from '@/lib/api/services';

/**
 * ExamImportForm 的 props。
 */
interface ExamImportFormProps {
  /** 任務提交成功時回呼，傳回 task_id */
  onSuccess?: (taskId: string) => void;
  /** 任務提交失敗時回呼，傳回錯誤訊息 */
  onError?: (error: string) => void;
}

/**
 * 考古題匯入表單。
 *
 * 收集試題 PDF、答案 PDF 與三個代碼（exam / category / subject），通過驗證後呼叫
 * `importService.submitAsync()`；提交成功會重置表單並觸發 onSuccess。
 *
 * @param props.onSuccess - 成功回呼
 * @param props.onError - 失敗回呼
 */
export default function ExamImportForm({ onSuccess, onError }: ExamImportFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [files, setFiles] = useState<{ question: File | null; answer: File | null }>({
    question: null,
    answer: null,
  });
  const [metadata, setMetadata] = useState({
    examCode: '',
    categoryCode: '',
    subjectCode: '',
  });

  const handleFileSelect = (field: 'question' | 'answer', file: File | null) => {
    setFiles((prev) => ({ ...prev, [field]: file }));
    setError(null);
  };

  const handleMetadataChange = (field: string, value: string) => {
    setMetadata((prev) => ({ ...prev, [field]: value }));
  };

  const validateForm = (): boolean => {
    if (!files.question) {
      setError('請選擇試題 PDF');
      return false;
    }
    if (!files.answer) {
      setError('請選擇答案 PDF');
      return false;
    }
    if (!metadata.examCode.trim()) {
      setError('請輸入考試代碼');
      return false;
    }
    if (!metadata.categoryCode.trim()) {
      setError('請輸入分類代碼');
      return false;
    }
    if (!metadata.subjectCode.trim()) {
      setError('請輸入科目代碼');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await importService.submitAsync({
        questionPdf: files.question!,
        answerPdf: files.answer!,
        examCode: metadata.examCode,
        categoryCode: metadata.categoryCode,
        subjectCode: metadata.subjectCode,
        skipExisting: true,
      });

      setSuccess(`匯入任務已提交！任務 ID: ${result.task_id}`);
      onSuccess?.(result.task_id);

      // Reset form
      setFiles({ question: null, answer: null });
      setMetadata({ examCode: '', categoryCode: '', subjectCode: '' });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '提交失敗，請稍後重試';
      setError(errorMsg);
      onError?.(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6 space-y-6"
      onSubmit={handleSubmit}
    >
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">提交新的考古題匯入</h2>

        {/* File Upload Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">試題 PDF</label>
            <FileInput
              file={files.question}
              onChange={(file) => handleFileSelect('question', file)}
              placeholder="選擇試題 PDF 檔案"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">答案 PDF</label>
            <FileInput
              file={files.answer}
              onChange={(file) => handleFileSelect('answer', file)}
              placeholder="選擇答案 PDF 檔案"
            />
          </div>
        </div>

        {/* Metadata Section */}
        <div className="border-t pt-4 space-y-4">
          <h3 className="text-sm font-medium text-slate-700">考試資訊</h3>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">考試代碼</label>
              <input
                type="text"
                value={metadata.examCode}
                onChange={(e) => handleMetadataChange('examCode', e.target.value)}
                placeholder="例：P"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">分類代碼</label>
              <input
                type="text"
                value={metadata.categoryCode}
                onChange={(e) => handleMetadataChange('categoryCode', e.target.value)}
                placeholder="例：01"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">科目代碼</label>
              <input
                type="text"
                value={metadata.subjectCode}
                onChange={(e) => handleMetadataChange('subjectCode', e.target.value)}
                placeholder="例：0101"
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex gap-2 p-3 bg-red-50 border border-red-200 rounded-md"
          >
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <span className="text-sm text-red-700">{error}</span>
          </motion.div>
        )}

        {success && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex gap-2 p-3 bg-green-50 border border-green-200 rounded-md"
          >
            <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
            <span className="text-sm text-green-700">{success}</span>
          </motion.div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className={`w-full py-2 px-4 rounded-md font-medium transition-all flex items-center justify-center gap-2 ${
            loading
              ? 'bg-blue-300 text-blue-800 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
          }`}
        >
          {loading ? (
            <>
              <Loader className="h-4 w-4 animate-spin" />
              提交中...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              提交匯入任務
            </>
          )}
        </button>
      </div>
    </motion.form>
  );
}

/**
 * 內部 FileInput 的 props。
 */
interface FileInputProps {
  /** 當前選取檔案 */
  file: File | null;
  /** 檔案變更回呼 */
  onChange: (file: File | null) => void;
  /** 未選取時顯示的提示文字 */
  placeholder: string;
}

/**
 * 拖放樣式檔案選擇器（內部子元件，僅接受 .pdf）。
 *
 * @param props.file - 當前檔案
 * @param props.onChange - 檔案變更回呼
 * @param props.placeholder - 提示文字
 */
function FileInput({ file, onChange, placeholder }: FileInputProps) {
  return (
    <label className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-300 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors">
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => onChange(e.target.files?.[0] || null)}
        className="hidden"
      />
      <Upload className="h-4 w-4 text-slate-400" />
      <span className="text-sm text-slate-600">
        {file ? file.name : placeholder}
      </span>
    </label>
  );
}
