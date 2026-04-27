/**
 * @file 全螢幕慶祝彩帶動畫元件，於成就達成等情境觸發。
 */
'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

/**
 * Confetti 的 props。
 */
interface ConfettiProps {
  /** 由 false 轉 true 時觸發一次彩帶動畫 */
  trigger: boolean;
  /** 動畫持續毫秒數（預設 3000） */
  duration?: number;
}

/**
 * 單一彩帶粒子的內部資料結構。
 */
interface Particle {
  /** 粒子 ID（在批次內唯一） */
  id: number;
  /** 起始水平位置（vw 百分比） */
  x: number;
  /** 顯示色票 */
  color: string;
  /** 動畫延遲秒數 */
  delay: number;
  /** 粒子大小（px） */
  size: number;
  /** 旋轉角度（deg） */
  rotation: number;
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

/**
 * 全螢幕彩帶動畫。
 *
 * 收到 `trigger=true` 時生成 40 顆粒子由螢幕上方落下並淡出，動畫結束後自動隱藏。
 *
 * @param props.trigger - 觸發旗標
 * @param props.duration - 動畫持續毫秒數
 */
export default function Confetti({ trigger, duration = 3000 }: ConfettiProps) {
  const [particles, setParticles] = useState<Particle[]>([]);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!trigger) return;

    const newParticles: Particle[] = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      delay: Math.random() * 0.5,
      size: 4 + Math.random() * 8,
      rotation: Math.random() * 360,
    }));

    setParticles(newParticles);
    setVisible(true);

    const timer = setTimeout(() => setVisible(false), duration);
    return () => clearTimeout(timer);
  }, [trigger, duration]);

  return (
    <AnimatePresence>
      {visible && (
        <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
          {particles.map((p) => (
            <motion.div
              key={p.id}
              initial={{
                x: `${p.x}vw`,
                y: -20,
                rotate: 0,
                opacity: 1,
              }}
              animate={{
                y: '110vh',
                rotate: p.rotation + 720,
                opacity: [1, 1, 0],
              }}
              transition={{
                duration: 2 + Math.random(),
                delay: p.delay,
                ease: 'easeIn',
              }}
              style={{
                position: 'absolute',
                width: p.size,
                height: p.size,
                backgroundColor: p.color,
                borderRadius: Math.random() > 0.5 ? '50%' : '2px',
              }}
            />
          ))}
        </div>
      )}
    </AnimatePresence>
  );
}
