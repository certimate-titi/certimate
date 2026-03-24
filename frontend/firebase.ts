import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore, collection, addDoc, serverTimestamp, doc, getDocFromServer } from 'firebase/firestore';
import firebaseConfig from './firebase-applet-config.json';

// Initialize Firebase SDK
const config = {
  ...firebaseConfig,
  apiKey: firebaseConfig.apiKey || process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "dummy-api-key-for-build"
};
const app = initializeApp(config);
export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);
export const auth = getAuth();

// Test Connection
async function testConnection() {
  try {
    await getDocFromServer(doc(db, 'test', 'connection'));
  } catch (error) {
    if (error instanceof Error && error.message.includes('the client is offline')) {
      console.error("Please check your Firebase configuration.");
    }
  }
}
testConnection();

// Audit Logging Utility
export enum AdminAction {
  CREATE_ADMIN = 'CREATE_ADMIN',
  EDIT_ADMIN = 'EDIT_ADMIN',
  DELETE_ADMIN = 'DELETE_ADMIN',
  UPDATE_SETTINGS = 'UPDATE_SETTINGS',
  SUSPEND_USER = 'SUSPEND_USER',
  ACTIVATE_USER = 'ACTIVATE_USER',
  ADJUST_SUBSCRIPTION = 'ADJUST_SUBSCRIPTION'
}

export async function logAdminAction(
  action: AdminAction,
  targetId: string,
  details: string,
  metadata: Record<string, any> = {}
) {
  const user = auth.currentUser;
  if (!user) return;

  try {
    await addDoc(collection(db, 'admin_audit_logs'), {
      adminId: user.uid,
      adminEmail: user.email,
      action,
      targetId,
      details,
      timestamp: serverTimestamp(),
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
