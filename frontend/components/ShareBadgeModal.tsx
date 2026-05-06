/**
 * @file ShareBadgeModal.tsx — 考後分享徽章彈窗
 *
 * 功能：
 * - 預覽 1080×1080 / 1080×1920 兩種尺寸切換
 * - 4 個平台分享按鈕（LinkedIn / IG / LINE / FB）
 * - 下載 PNG（萬用 fallback）
 * - 手機優先 Web Share API
 */
'use client';

import { useState, useRef } from 'react';
import { X, Linkedin, Instagram, Download, MessageCircle, Facebook, Loader2 } from 'lucide-react';
import ShareBadgeCard from './ShareBadgeCard';
import type { ShareBadgeResponse } from '@/types/api';

export interface ShareBadgeModalProps {
  data: ShareBadgeResponse;
  onClose: () => void;
}

const SHARE_TEXT = '我在 TiTi 智慧備考完成了一份挑戰，分享我的學習徽章！';

export default function ShareBadgeModal({ data, onClose }: ShareBadgeModalProps) {
  const [variant, setVariant] = useState<'square' | 'story'>('square');
  const [busy, setBusy] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  /** 將卡片轉為 PNG dataURL */
  async function captureToDataUrl(): Promise<string | null> {
    const target = document.getElementById(`badge-${variant}`);
    if (!target) return null;
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(target, {
        backgroundColor: '#ffffff',
        scale: 3, // 1080+ px 輸出
        logging: false,
        useCORS: true,
      });
      return canvas.toDataURL('image/png');
    } catch (e) {
      console.warn('Capture failed:', e);
      return null;
    }
  }

  async function handleDownload() {
    setBusy('download');
    try {
      const url = await captureToDataUrl();
      if (!url) { alert('截圖失敗，請重試'); return; }
      const a = document.createElement('a');
      a.href = url;
      a.download = `TiTi_Badge_${data.learning_style.type_id}_${new Date().toISOString().slice(0, 10)}.png`;
      a.click();
    } finally {
      setBusy(null);
    }
  }

  async function handleNativeShare() {
    setBusy('native');
    try {
      const url = await captureToDataUrl();
      if (!url) return;
      // Convert dataURL → File for Web Share Level 2
      const blob = await (await fetch(url)).blob();
      const file = new File([blob], `TiTi_Badge.png`, { type: 'image/png' });
      // Web Share API（手機原生分享）
      if (navigator.share && (navigator.canShare?.({ files: [file] }) ?? false)) {
        await navigator.share({
          title: '我的 TiTi 學習徽章',
          text: SHARE_TEXT,
          files: [file],
        });
      } else {
        // 桌機 fallback：直接下載
        await handleDownload();
      }
    } catch (e) {
      // 使用者取消分享屬正常
      if (e instanceof Error && e.name !== 'AbortError') {
        console.warn('Share failed:', e);
      }
    } finally {
      setBusy(null);
    }
  }

  function handleLinkedIn() {
    const shareUrl = encodeURIComponent('https://certimate-titi.web.app');
    window.open(
      `https://www.linkedin.com/sharing/share-offsite/?url=${shareUrl}`,
      '_blank',
      'width=600,height=500',
    );
  }

  function handleFacebook() {
    const shareUrl = encodeURIComponent('https://certimate-titi.web.app');
    window.open(
      `https://www.facebook.com/sharer/sharer.php?u=${shareUrl}`,
      '_blank',
      'width=600,height=500',
    );
  }

  function handleLine() {
    const text = encodeURIComponent(SHARE_TEXT + ' https://certimate-titi.web.app');
    window.open(`https://line.me/R/share?text=${text}`, '_blank');
  }

  function handleInstagram() {
    // IG 不支援程式化分享網頁，引導用戶下載 + 手動上傳 Story
    handleDownload();
    setTimeout(() => {
      alert('圖卡已下載！請打開 Instagram → 限時動態 → 從相簿上傳剛下載的圖檔 ✨');
    }, 500);
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto" onClick={onClose}>
      <div
        className="bg-slate-50 rounded-3xl shadow-2xl max-w-2xl w-full max-h-[95vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">分享你的學習徽章</h2>
            <p className="text-xs text-slate-500 mt-0.5">不揭露分數，只展現成長與堅持</p>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100 text-slate-500" aria-label="關閉">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Variant 切換 */}
        <div className="flex justify-center gap-2 pt-6">
          <button
            onClick={() => setVariant('square')}
            className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
              variant === 'square' ? 'bg-emerald-500 text-white' : 'bg-white text-slate-600 border border-slate-200'
            }`}
          >
            1:1 方形（LinkedIn / FB / IG Post / LINE）
          </button>
          <button
            onClick={() => setVariant('story')}
            className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
              variant === 'story' ? 'bg-emerald-500 text-white' : 'bg-white text-slate-600 border border-slate-200'
            }`}
          >
            9:16 直式（IG Story）
          </button>
        </div>

        {/* Card preview */}
        <div className="p-6 flex justify-center" ref={cardRef}>
          <ShareBadgeCard data={data} variant={variant} domId={`badge-${variant}`} />
        </div>

        {/* Action buttons */}
        <div className="bg-white border-t border-slate-200 px-6 py-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <button
              onClick={handleLinkedIn}
              className="flex items-center justify-center gap-2 bg-[#0077B5] hover:bg-[#005f8d] text-white px-3 py-2.5 rounded-xl text-sm font-medium transition-colors"
            >
              <Linkedin className="h-4 w-4" /> LinkedIn
            </button>
            <button
              onClick={handleInstagram}
              className="flex items-center justify-center gap-2 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 hover:opacity-90 text-white px-3 py-2.5 rounded-xl text-sm font-medium transition-colors"
            >
              <Instagram className="h-4 w-4" /> Instagram
            </button>
            <button
              onClick={handleLine}
              className="flex items-center justify-center gap-2 bg-[#06C755] hover:bg-[#05a648] text-white px-3 py-2.5 rounded-xl text-sm font-medium transition-colors"
            >
              <MessageCircle className="h-4 w-4" /> LINE
            </button>
            <button
              onClick={handleFacebook}
              className="flex items-center justify-center gap-2 bg-[#1877F2] hover:bg-[#1466d4] text-white px-3 py-2.5 rounded-xl text-sm font-medium transition-colors"
            >
              <Facebook className="h-4 w-4" /> Facebook
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-2">
            <button
              onClick={handleNativeShare}
              disabled={busy === 'native'}
              className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
            >
              {busy === 'native' ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              手機原生分享
            </button>
            <button
              onClick={handleDownload}
              disabled={busy === 'download'}
              className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
            >
              {busy === 'download' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              下載 PNG
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
