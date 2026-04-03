import { createHmac } from 'crypto';

const JWT_SECRET = 'certimate-api-test-secret-key-do-not-use-in-production';

function base64url(data: string): string {
  return Buffer.from(data).toString('base64url');
}

export function generateVerificationToken(userId: string): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    sub: userId,
    purpose: 'email_verify',
    exp: now + 86400,
    iat: now,
  };

  const headerB64 = base64url(JSON.stringify(header));
  const payloadB64 = base64url(JSON.stringify(payload));
  const signature = createHmac('sha256', JWT_SECRET)
    .update(`${headerB64}.${payloadB64}`)
    .digest('base64url');

  return `${headerB64}.${payloadB64}.${signature}`;
}

/** Get a user's ID from the admin API */
export async function getUserId(
  request: { post: Function; get: Function },
  email: string,
): Promise<string> {
  const loginRes = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: 'admin@certimate.com', password: 'admin123' },
  });
  const { access_token } = await loginRes.json();

  const usersRes = await request.get('http://localhost:8000/api/v1/admin/users', {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  const { users } = await usersRes.json();
  const user = users.find((u: any) => u.email === email);
  if (!user) throw new Error(`User ${email} not found in admin API`);
  return user.id;
}
