'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { MessageSquarePlus, Upload, CheckCircle2, ArrowLeft, Image as ImageIcon, X } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

type FeedbackType = 'BUG' | 'FEATURE_REQUEST' | 'CONTENT_ERROR' | 'OTHER';

const FEEDBACK_TYPES: { value: FeedbackType; label: string; emoji: string }[] = [
  { value: 'BUG', label: '錯誤回報', emoji: '🐛' },
  { value: 'FEATURE_REQUEST', label: '功能建議', emoji: '💡' },
  { value: 'CONTENT_ERROR', label: '內容勘誤', emoji: '📝' },
  { value: 'OTHER', label: '其他', emoji: '💬' },
];

export default function FeedbackPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [type, setType] = useState<FeedbackType | null>(null);
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace('/login?redirect=/feedback');
    }
  }, [authLoading, user, router]);

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleAttachmentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (attachments.length + files.length > 3) {
      setError('最多只能上傳 3 張截圖');
      return;
    }
    for (const file of files) {
      if (file.size > 5 * 1024 * 1024) {
        setError('附件大小不得超過 5 MB');
        return;
      }
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        setError('僅支援 JPG / PNG 格式');
        return;
      }
    }
    setError(null);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!type) { setError('請選擇反饋類型'); return; }
    if (!subject.trim()) { setError('必要欄位未填寫'); return; }
    if (subject.length > 100) { setError('主旨不得超過 100 個字元'); return; }
    if (!content.trim()) { setError('必要欄位未填寫'); return; }
    if (content.length > 2000) { setError('內容不得超過 2000 個字元'); return; }

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('type', type);
      formData.append('subject', subject.trim());
      formData.append('content', content.trim());
      attachments.forEach(file => formData.append('attachments', file));
      const { apiClient } = await import('@/lib/api/client');
      await apiClient.upload('/feedback', formData);
      setSubmitted(true);
    } catch (err) {
      setError('提交失敗，請稍後再試。');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50 py-12 px-4">
        <div className="max-w-md w-full text-center space-y-6 bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
          <div className="mx-auto h-16 w-16 bg-emerald-100 rounded-full flex items-center justify-center">
            <CheckCircle2 className="h-10 w-10 text-emerald-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900">感謝您的反饋！</h2>
          <p className="text-slate-600">我們已收到您的意見，將盡快處理並回覆您。</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => { setSubmitted(false); setType(null); setSubject(''); setContent(''); setAttachments([]); }} className="px-4 py-2 rounded-xl border border-slate-200 text-sm font-medium text-slate-700 hover:bg-slate-50">
              再提交一則
            </button>
            <Link href="/dashboard" className="px-4 py-2 rounded-xl bg-slate-900 text-white text-sm font-medium hover:bg-slate-800">
              返回首頁
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700 mb-6">
          <ArrowLeft className="h-4 w-4" /> 返回
        </button>

        <div className="bg-white rounded-3xl shadow-xl border border-slate-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 bg-emerald-100 rounded-full flex items-center justify-center">
              <MessageSquarePlus className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">意見反饋</h1>
              <p className="text-sm text-slate-500">你的每一則反饋都會讓 CertiMate 變得更好</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Feedback type */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">反饋類型</label>
              <div className="grid grid-cols-2 gap-2">
                {FEEDBACK_TYPES.map(ft => (
                  <button
                    key={ft.value}
                    type="button"
                    onClick={() => setType(ft.value)}
                    className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium transition-colors ${
                      type === ft.value
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                        : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <span>{ft.emoji}</span>
                    <span>{ft.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Subject */}
            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-slate-700 mb-1">
                主旨 <span className="text-slate-400">({subject.length}/100)</span>
              </label>
              <input
                id="subject"
                type="text"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                maxLength={100}
                placeholder="簡述你遇到的問題或建議"
                className="w-full px-4 py-3 rounded-xl border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm"
              />
            </div>

            {/* Content */}
            <div>
              <label htmlFor="content" className="block text-sm font-medium text-slate-700 mb-1">
                詳細說明 <span className="text-slate-400">({content.length}/2000)</span>
              </label>
              <textarea
                id="content"
                value={content}
                onChange={e => setContent(e.target.value)}
                maxLength={2000}
                rows={6}
                placeholder="請詳細描述問題或建議，包含重現步驟、裝置環境等資訊"
                className="w-full px-4 py-3 rounded-xl border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent sm:text-sm resize-none"
              />
            </div>

            {/* Attachments */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                截圖附件 <span className="text-slate-400">(選填，最多 3 張，每張 ≤ 5 MB)</span>
              </label>
              {attachments.length > 0 && (
                <div className="flex gap-2 mb-2 flex-wrap">
                  {attachments.map((file, i) => (
                    <div key={i} className="relative group flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg text-xs text-slate-600">
                      <ImageIcon className="h-3.5 w-3.5" />
                      <span className="truncate max-w-[120px]">{file.name}</span>
                      <button type="button" onClick={() => removeAttachment(i)} className="text-slate-400 hover:text-rose-500">
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {attachments.length < 3 && (
                <label className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-dashed border-slate-300 text-sm text-slate-500 hover:bg-slate-50 cursor-pointer">
                  <Upload className="h-4 w-4" />
                  上傳截圖
                  <input type="file" accept="image/jpeg,image/png" multiple onChange={handleAttachmentChange} className="hidden" />
                </label>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="p-3 bg-rose-50 text-rose-600 text-sm rounded-xl border border-rose-100">
                {error}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 px-4 rounded-xl bg-slate-900 text-white text-sm font-bold hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors disabled:opacity-50"
            >
              {isSubmitting ? '提交中...' : '提交意見'}
            </button>
          </form>
        </div>

        {/* My feedback history — loaded from API */}
        <div className="mt-8 bg-white rounded-3xl shadow-xl border border-slate-100 p-8">
          <h2 className="text-lg font-bold text-slate-900 mb-4">我的反饋紀錄</h2>
          <div className="text-center py-8 text-slate-400 text-sm">
            尚無反饋紀錄
          </div>
        </div>
      </div>
    </div>
  );
}
