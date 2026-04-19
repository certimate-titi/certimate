/**
 * Firebase utilities — DEPRECATED for Auth, kept only for:
 * 1. AdminAction enum (used by super-admin audit log UI)
 * 2. logAdminAction() — writes to backend API (was Firestore, migrated 2026-04-16)
 *
 * Google SSO now uses @react-oauth/google (Google Identity Services) directly,
 * not Firebase Auth SDK. See lib/google-oauth-wrapper.tsx + lib/auth-context.tsx.
 */

import { apiClient } from '@/lib/api/client';

export enum AdminAction {
  // 使用者管理
  CREATE_ADMIN = 'create_admin',
  EDIT_ADMIN = 'EDIT_ADMIN',
  DELETE_USER = 'delete_user',
  DELETE_ADMIN = 'delete_user', // backward compat alias
  SUSPEND_USER = 'suspend_user',
  ACTIVATE_USER = 'activate_user',
  ADJUST_ROLE = 'adjust_role',
  NOTIFY_USER = 'notify_user',
  // 訂閱 & 財務
  ADJUST_SUBSCRIPTION = 'adjust_subscription',
  SUBSCRIPTION_UPGRADE = 'subscription_upgrade',
  APPROVE_REFUND = 'approve_refund',
  REJECT_REFUND = 'reject_refund',
  // 系統設定
  UPDATE_SETTINGS = 'UPDATE_SETTINGS',
  UPDATE_MODEL_ROUTING = 'update_model_routing',
  RESET_AI_LIMITS = 'reset_ai_limits',
  CLEAR_CACHE = 'clear_cache',
  // 成本監控
  COST_MONITOR_VIEWED = 'COST_MONITOR_VIEWED',
  BUDGET_UPDATED = 'BUDGET_UPDATED',
  BUDGET_OVERRIDE = 'BUDGET_OVERRIDE',
  // 內容審核
  RESOLVE_REPORT = 'resolve_report',
  UNLOCK_COOLDOWN = 'unlock_cooldown',
  APPROVE_CONTENT = 'approve',
  REJECT_CONTENT = 'reject',
  UPDATE_FEEDBACK = 'update_feedback_status',
  UPDATE_ANOMALY = 'update_anomaly_status',
  // AI & Prompt
  CREATE_PROMPT = 'create_prompt_template',
  UPDATE_PROMPT = 'update_prompt_template',
  DEACTIVATE_PROMPT = 'deactivate_prompt_template',
  ROLLBACK_PROMPT = 'rollback_prompt_template',
  CREATE_AB_TEST = 'create_ab_test',
  COMPLETE_AB_TEST = 'complete_ab_test',
  FUP_SOFT_CAP = 'fup_soft_cap_triggered',
  // 知識庫
  EXTRACT_KNOWLEDGE = 'extract_knowledge',
}

export async function logAdminAction(
  action: AdminAction,
  targetId: string,
  details: string,
  metadata: Record<string, unknown> = {}
) {
  try {
    await apiClient.post('/admin/audit-log', {
      action,
      target_id: targetId,
      details,
      metadata: {
        ...metadata,
        userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'server',
        url: typeof window !== 'undefined' ? window.location.href : 'server'
      }
    });
  } catch (error) {
    console.error('Failed to log admin action:', error);
  }
}
