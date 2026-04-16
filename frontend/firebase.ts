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
  CREATE_ADMIN = 'CREATE_ADMIN',
  EDIT_ADMIN = 'EDIT_ADMIN',
  DELETE_ADMIN = 'DELETE_ADMIN',
  UPDATE_SETTINGS = 'UPDATE_SETTINGS',
  SUSPEND_USER = 'SUSPEND_USER',
  ACTIVATE_USER = 'ACTIVATE_USER',
  ADJUST_SUBSCRIPTION = 'ADJUST_SUBSCRIPTION',
  ADJUST_ROLE = 'adjust_role',
  UPDATE_PLAN_QUOTA = 'update_plan_quota',
  BUDGET_ALERT = 'budget_alert',
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
