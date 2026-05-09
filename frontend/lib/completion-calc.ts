/**
 * @file completion-calc.ts — 完成度框架（Completion Framework）客戶端計算純函式
 *
 * B.2 進度條算法：
 *   S = Σ(node_weight_i × mastery_i) / Σ(node_weight_i)
 *   其中 node_weight_i 由頻率等級決定（1x / 2x / 3x）
 *   mastery_i = mastery_rate / 100（0~1）
 *
 * B.3 徽章里程碑：嚴格依 mastery 加權分數觸發，不允許手動加速。
 *
 * TODO: backend wire-up — 目前全部為 client-side mock 計算；
 *       後端未提供 /api/v1/subjects/{id}/completion 端點，
 *       待後端實作後替換此模組的資料源。
 */

/** 頻率等級 → 權重係數 */
const FREQ_WEIGHT: Record<string, number> = {
  high: 3,
  medium: 2,
  low: 1,
};

/** 節點輸入（對應 MindMapNode + 額外 freq 欄位） */
export interface CompletionNode {
  id: string;
  subject_id: string;
  /** 掌握度 0~100（來自 mastery_rate） */
  mastery_rate: number;
  /** 頻率等級，預設 'medium' */
  frequency?: 'high' | 'medium' | 'low';
  /** 節點是否為孤立節點（尚無學習材料） */
  is_orphan?: boolean;
}

/** 完成度計算結果 */
export interface CompletionResult {
  /** 加權平均掌握度分數，0~1 */
  score: number;
  /** 換算為百分比（0~100，取整） */
  percent: number;
  /** 是否已達甜蜜點（85%） */
  sweetSpotReached: boolean;
  /** 是否全覆蓋（100%） */
  fullCoverage: boolean;
  /** 已解鎖的徽章清單 */
  unlockedBadges: BadgeId[];
  /** 孤立節點數量（無材料節點） */
  orphanCount: number;
  /** 總節點數 */
  totalNodes: number;
  /** 已觸及節點數（mastery_rate > 0） */
  touchedNodes: number;
  /** 邊際效益遞減提示應觸發 */
  showMarginalUtilityNudge: boolean;
}

/** 徽章 ID */
export type BadgeId =
  | 'starter'
  | 'explorer'
  | 'builder'
  | 'sweet_spot'
  | 'high_freq_master'
  | 'complete';

/** 徽章定義（B.3） */
export interface BadgeDefinition {
  id: BadgeId;
  label: string;
  description: string;
  emoji: string;
  /** 觸發條件說明 */
  triggerDesc: string;
}

export const BADGES: BadgeDefinition[] = [
  {
    id: 'starter',
    label: '啟程者',
    description: '踏出第一步',
    emoji: '🌱',
    triggerDesc: '首個節點 mastery > 0',
  },
  {
    id: 'explorer',
    label: '探索者',
    description: '觸及 25% 知識版圖',
    emoji: '🔭',
    triggerDesc: '加權分數達 25%',
  },
  {
    id: 'builder',
    label: '建設者',
    description: '打好一半基礎',
    emoji: '🏗️',
    triggerDesc: '加權分數達 50%',
  },
  {
    id: 'sweet_spot',
    label: '甜蜜點達陣者',
    description: '通過 85% 高效門檻',
    emoji: '🎯',
    triggerDesc: '加權分數達 85%（甜蜜點）',
  },
  {
    id: 'high_freq_master',
    label: '高頻王者',
    description: '所有高頻節點全部精熟',
    emoji: '👑',
    triggerDesc: '所有 frequency=high 節點 mastery_rate ≥ 90',
  },
  {
    id: 'complete',
    label: '知識完整者',
    description: '達成 100% 完整覆蓋',
    emoji: '💎',
    triggerDesc: '加權分數達 100%',
  },
];

/**
 * 計算完成度
 * @param nodes - 當前科目的節點列表（必須已透過 subject_id 過濾）
 */
export function calcCompletion(nodes: CompletionNode[]): CompletionResult {
  if (nodes.length === 0) {
    return {
      score: 0,
      percent: 0,
      sweetSpotReached: false,
      fullCoverage: false,
      unlockedBadges: [],
      orphanCount: 0,
      totalNodes: 0,
      touchedNodes: 0,
      showMarginalUtilityNudge: false,
    };
  }

  let weightedSum = 0;
  let weightTotal = 0;

  for (const node of nodes) {
    const w = FREQ_WEIGHT[node.frequency ?? 'medium'] ?? 2;
    const m = Math.min(Math.max(node.mastery_rate, 0), 100) / 100;
    weightedSum += w * m;
    weightTotal += w;
  }

  const score = weightTotal > 0 ? weightedSum / weightTotal : 0;
  const percent = Math.round(score * 100);
  const touchedNodes = nodes.filter(n => n.mastery_rate > 0).length;
  const orphanCount = nodes.filter(n => n.is_orphan === true).length;

  // 徽章判定（嚴格依 mastery 計算，不允許手動加速）
  const highFreqNodes = nodes.filter(n => n.frequency === 'high');
  const allHighFreqMastered =
    highFreqNodes.length > 0 && highFreqNodes.every(n => n.mastery_rate >= 90);

  const unlockedBadges: BadgeId[] = [];
  if (touchedNodes > 0) unlockedBadges.push('starter');
  if (percent >= 25) unlockedBadges.push('explorer');
  if (percent >= 50) unlockedBadges.push('builder');
  if (percent >= 85) unlockedBadges.push('sweet_spot');
  if (allHighFreqMastered) unlockedBadges.push('high_freq_master');
  if (percent >= 100) unlockedBadges.push('complete');

  // B.4 邊際效益遞減：甜蜜點達陣後進度 85~94 之間，顯示提示
  const showMarginalUtilityNudge = percent >= 85 && percent < 95;

  return {
    score,
    percent,
    sweetSpotReached: percent >= 85,
    fullCoverage: percent >= 100,
    unlockedBadges,
    orphanCount,
    totalNodes: nodes.length,
    touchedNodes,
    showMarginalUtilityNudge,
  };
}

/**
 * 測試用 fixture（dev/test 環境驗證算法正確性）
 *
 * TODO: backend wire-up — 替換為真實 API 資料後移除此 fixture
 */
export const TEST_FIXTURE_NODES: CompletionNode[] = [
  { id: 'n1', subject_id: 'subj_001', mastery_rate: 90, frequency: 'high' },
  { id: 'n2', subject_id: 'subj_001', mastery_rate: 75, frequency: 'high' },
  { id: 'n3', subject_id: 'subj_001', mastery_rate: 60, frequency: 'medium' },
  { id: 'n4', subject_id: 'subj_001', mastery_rate: 30, frequency: 'medium' },
  { id: 'n5', subject_id: 'subj_001', mastery_rate: 0, frequency: 'low', is_orphan: true },
  { id: 'n6', subject_id: 'subj_001', mastery_rate: 0, frequency: 'low', is_orphan: true },
];
// 期望結果：score≈0.633, percent=63, 徽章=[starter,explorer,builder], orphanCount=2
