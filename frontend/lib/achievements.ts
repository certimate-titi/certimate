/**
 * Achievement Definitions — 9 種成就徽章
 *
 * 每個徽章依據「情感化設計與鼓勵機制規範」設計，
 * 強調「過程比結果重要」的設計理念。
 */

import type { Achievement } from '@/types';

/**
 * 單一成就徽章的設計定義。
 */
export interface AchievementDefinition {
  /** 成就唯一 ID（以 `ach_` 為前綴） */
  id: string;
  /** 顯示名稱（含 emoji） */
  name: string;
  /** 解鎖條件的人類可讀描述 */
  description: string;
  /** 圖示 emoji */
  iconEmoji: string;
  /** 觸發條件的虛擬碼描述（僅供文件，非實際求值） */
  triggerCondition: string;
  /** 此徽章的情感化設計目的 */
  designPurpose: string;
}

/**
 * 9 種成就徽章的完整定義清單。
 *
 * 順序對應 UI 預設陳列順序；新增徽章請維持向後相容並避免移除既有 id。
 */
export const ACHIEVEMENT_DEFINITIONS: AchievementDefinition[] = [
  {
    id: 'ach_seeder',
    name: '🌱 播種者',
    description: '上傳第一份學習資源',
    iconEmoji: '🌱',
    triggerCondition: 'user.documentsUploaded >= 1',
    designPurpose: '獎勵踏出第一步',
  },
  {
    id: 'ach_streak_3',
    name: '🔥 三日連續',
    description: '連續 3 天登入並做題',
    iconEmoji: '🔥',
    triggerCondition: 'user.currentStreak >= 3',
    designPurpose: '養成每日學習習慣',
  },
  {
    id: 'ach_ironman_7',
    name: '💪 鐵人七日',
    description: '連續 7 天完成至少一回測驗',
    iconEmoji: '💪',
    triggerCondition: 'user.currentStreak >= 7 && user.examsCompletedInStreak >= 7',
    designPurpose: '長期堅持的肯定',
  },
  {
    id: 'ach_weakness_crusher',
    name: '🧠 弱點克星',
    description: '某弱點章節答對率從 <50% 提升至 >80%',
    iconEmoji: '🧠',
    triggerCondition: 'domain.previousAccuracy < 50 && domain.currentAccuracy > 80',
    designPurpose: '獎勵最有價值的進步',
  },
  {
    id: 'ach_perfect_score',
    name: '🎯 滿分時刻',
    description: '任一測驗獲得 100% 正確率',
    iconEmoji: '🎯',
    triggerCondition: 'exam.score === 100',
    designPurpose: '完美表現的即時慶祝',
  },
  {
    id: 'ach_curious_mind',
    name: '📖 求知若渴',
    description: '累計向 AI 教練提問超過 50 次',
    iconEmoji: '📖',
    triggerCondition: 'user.aiQuestionsAsked >= 50',
    designPurpose: '鼓勵主動追問',
  },
  {
    id: 'ach_summit',
    name: '🗻 登頂者',
    description: '累計完成 100 回模擬考',
    iconEmoji: '🗻',
    triggerCondition: 'user.totalExamsCompleted >= 100',
    designPurpose: '超級用戶的榮耀勳章',
  },
  {
    id: 'ach_night_owl',
    name: '🌙 夜貓學霸',
    description: '晚上 11 點後完成一回考卷',
    iconEmoji: '🌙',
    triggerCondition: 'exam.completedAt.getHours() >= 23',
    designPurpose: '幽默化的陪伴感',
  },
  {
    id: 'ach_resilient',
    name: '🔄 不屈不撓',
    description: '同一章節重新挑戰超過 5 次',
    iconEmoji: '🔄',
    triggerCondition: 'domain.retryCount >= 5',
    designPurpose: '鼓勵面對困難不放棄',
  },
];

/**
 * 為新使用者建立初始成就狀態。
 *
 * 全部徽章預設為未解鎖（`unlockedAt = null`）。
 *
 * @returns 與 {@link ACHIEVEMENT_DEFINITIONS} 對齊、皆為鎖定狀態的成就陣列
 */
export function createInitialAchievements(): Achievement[] {
  return ACHIEVEMENT_DEFINITIONS.map(def => ({
    id: def.id,
    name: def.name,
    description: def.description,
    iconEmoji: def.iconEmoji,
    unlockedAt: null,
  }));
}

/**
 * 依使用者統計指標計算應解鎖的成就 ID 清單。
 *
 * 此為純函式；實際生產應以後端 API 取得真實指標後再代入。
 *
 * @param metrics - 使用者各項學習行為指標
 * @returns 已達成解鎖條件的成就 ID 陣列
 */
export function getUnlockedAchievementIds(metrics: {
  documentsUploaded: number;
  currentStreak: number;
  totalExamsCompleted: number;
  aiQuestionsAsked: number;
  hasLateNightExam: boolean;
  hasPerfectScore: boolean;
  hasWeaknessCrushed: boolean;
  maxDomainRetries: number;
}): string[] {
  const unlocked: string[] = [];

  if (metrics.documentsUploaded >= 1) unlocked.push('ach_seeder');
  if (metrics.currentStreak >= 3) unlocked.push('ach_streak_3');
  if (metrics.currentStreak >= 7) unlocked.push('ach_ironman_7');
  if (metrics.hasWeaknessCrushed) unlocked.push('ach_weakness_crusher');
  if (metrics.hasPerfectScore) unlocked.push('ach_perfect_score');
  if (metrics.aiQuestionsAsked >= 50) unlocked.push('ach_curious_mind');
  if (metrics.totalExamsCompleted >= 100) unlocked.push('ach_summit');
  if (metrics.hasLateNightExam) unlocked.push('ach_night_owl');
  if (metrics.maxDomainRetries >= 5) unlocked.push('ach_resilient');

  return unlocked;
}
