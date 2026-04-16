'use client';

import { GoogleOAuthProvider } from '@react-oauth/google';

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

export function GoogleOAuthWrapper({ children }: { children: React.ReactNode }) {
  if (!GOOGLE_CLIENT_ID) {
    // No Google Client ID configured — skip provider, Google SSO button will be hidden
    return <>{children}</>;
  }
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      {children}
    </GoogleOAuthProvider>
  );
}
