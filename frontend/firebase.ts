import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore, collection, addDoc, serverTimestamp, doc, getDocFromServer } from 'firebase/firestore';

// Firebase config from environment variables (not hardcoded in git)
const config = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "dummy-api-key-for-build",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "certimate-titi.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "certimate-titi",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "certimate-titi.firebasestorage.app",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || "",
};
const firestoreDatabaseId = process.env.NEXT_PUBLIC_FIRESTORE_DATABASE_ID || "";

const app = initializeApp(config);
export const db = getFirestore(app, firestoreDatabaseId);
export const auth = getAuth();
export const googleProvider = new GoogleAuthProvider();

// Test Connection (only when Firebase is properly configured)
async function testConnection() {
  if (!config.apiKey || config.apiKey === 'dummy-api-key-for-build') {
    // Firebase not configured — skip connection test (using JWT auth instead)
    return;
  }
  try {
    await getDocFromServer(doc(db, 'test', 'connection'));
  } catch (error) {
    if (error instanceof Error && error.message.includes('the client is offline')) {
      console.warn("Firebase connection unavailable. JWT auth is unaffected.");
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
