/**
 * Playwright Global Setup — Cleans stale data + seeds test accounts via backend API.
 *
 * Accounts seeded:
 *  - newbie@example.com  (FREE, ACTIVE, onboarding_completed=false)
 *  - carol@example.com   (ULTRA_1599, ACTIVE)
 *  - admin@example.com   (ADMIN role, ACTIVE)
 *
 * Accounts cleaned up (must NOT exist for other tests):
 *  - newuser@example.com (signup test needs it unregistered)
 *  - pending@example.com (pending-login test needs specific backend-seeded state)
 */

const API = 'http://localhost:8000/api/v1';

async function jsonPost(url: string, data: Record<string, unknown>, token?: string) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(url, { method: 'POST', headers, body: JSON.stringify(data) });
}

async function jsonGet(url: string, token: string) {
  return fetch(url, { headers: { Authorization: `Bearer ${token}` } });
}

/** Delete a user by logging in as them and calling the self-service delete endpoint */
async function selfServiceDelete(email: string, password: string) {
  try {
    const loginRes = await jsonPost(`${API}/auth/login`, { email, password });
    if (!loginRes.ok) return false;
    const { access_token } = await loginRes.json();
    const delRes = await fetch(`${API}/auth/delete-account`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${access_token}` },
    });
    return delRes.ok;
  } catch {
    return false;
  }
}

async function globalSetup() {
  console.log('[E2E Setup] Starting test account seed...');

  // 1. Login as super admin
  let adminToken: string;
  try {
    const res = await jsonPost(`${API}/auth/login`, {
      email: 'admin@certimate.com',
      password: 'admin123',
    });
    if (!res.ok) {
      console.warn('[E2E Setup] Admin login failed — backend may not be running. Skipping seed.');
      return;
    }
    const body = await res.json();
    adminToken = body.access_token;
  } catch {
    console.warn('[E2E Setup] Cannot reach backend. Skipping seed.');
    return;
  }

  // ── Cleanup: delete accounts that tests expect to NOT exist ──

  // newuser@example.com — signup test needs it to be unregistered.
  // After signup test creates it, it's in PENDING state (can't login for self-delete).
  // So: activate first via admin, then self-service delete.
  {
    let users: Array<{ id: string; email: string; status: string }> = [];
    try {
      const res = await jsonGet(`${API}/admin/users`, adminToken);
      if (res.ok) {
        const body = await res.json();
        users = body.users || body.items || body || [];
      }
    } catch {}
    const newuser = users.find((u) => u.email === 'newuser@example.com');
    if (newuser) {
      // Activate if needed so we can login
      if (newuser.status !== 'ACTIVE') {
        await jsonPost(
          `${API}/admin/users/activate`,
          { target_user_id: newuser.id },
          adminToken,
        ).catch(() => {});
      }
      // Now login and self-delete
      for (const pw of ['CertiMate#2024', 'Password1!']) {
        if (await selfServiceDelete('newuser@example.com', pw)) {
          console.log('[E2E Setup] Cleaned up newuser@example.com');
          break;
        }
      }
    }
  }

  // pending@example.com — the pending-login test expects login to fail with
  // "帳號尚未驗證" error. We need it in PENDING state with password "Pending1!".
  // Delete any stale version first, then re-register (it stays PENDING by default).
  for (const pw of ['Password1!', 'Pending1!']) {
    if (await selfServiceDelete('pending@example.com', pw)) {
      console.log('[E2E Setup] Cleaned up stale pending@example.com');
      break;
    }
  }

  // ── Seed: register accounts needed for tests ──

  const testUsers = [
    { email: 'newbie@example.com', password: 'Password1!', agreed_to_terms: true },
    { email: 'carol@example.com', password: 'Password1!', agreed_to_terms: true },
    { email: 'admin@example.com', password: 'Password1!', agreed_to_terms: true },
    // pending@example.com: re-register with correct test password, stays PENDING (not activated)
    { email: 'pending@example.com', password: 'Pending1!', agreed_to_terms: true },
  ];

  for (const user of testUsers) {
    const res = await jsonPost(`${API}/auth/register`, user).catch(() => null);
    if (res?.ok) {
      console.log(`[E2E Setup] Registered ${user.email}`);
    }
    // 409 or 400 = already exists, that's fine
  }

  // Fetch user list for activation and role setup
  let users: Array<{ id: string; email: string; status: string }> = [];
  try {
    const res = await jsonGet(`${API}/admin/users`, adminToken);
    if (res.ok) {
      const body = await res.json();
      users = body.users || body.items || body || [];
    }
  } catch {}

  const findUser = (email: string) => users.find((u) => u.email === email);

  // Activate accounts that need to be ACTIVE
  for (const email of ['newbie@example.com', 'carol@example.com', 'admin@example.com']) {
    const user = findUser(email);
    if (user && user.status !== 'ACTIVE') {
      await jsonPost(`${API}/admin/users/activate`, { target_user_id: user.id }, adminToken).catch(
        () => {},
      );
      console.log(`[E2E Setup] Activated ${email}`);
    }
  }

  // Set carol's subscription to ULTRA_1599
  const carol = findUser('carol@example.com');
  if (carol) {
    await jsonPost(
      `${API}/admin/users/${carol.id}/adjust-subscription`,
      { plan: 'ULTRA_1599' },
      adminToken,
    ).catch(() => {});
    console.log('[E2E Setup] Set carol → ULTRA_1599');
  }

  // Set admin@example.com role to ADMIN
  await jsonPost(
    `${API}/admin/users/adjust-role`,
    { target_email: 'admin@example.com', role: 'admin' },
    adminToken,
  ).catch(() => {});
  console.log('[E2E Setup] Set admin@example.com → ADMIN role');

  // ── Seed: subject categories and subjects matching feature spec ──

  const subjectCategories = [
    { name: 'IT', subjects: ['AWS SAA', 'Azure AZ-900', 'CCNA'] },
    { name: '金融', subjects: ['CFA Level 1', 'FRM', '證券分析師'] },
    { name: '語言', subjects: ['TOEIC', 'JLPT N1', 'IELTS'] },
    { name: '醫療', subjects: ['護理師', '藥師', '醫檢師'] },
  ];

  await jsonPost(
    `${API}/admin/seed-subjects`,
    { categories: subjectCategories },
    adminToken,
  ).catch(() => {
    console.warn('[E2E Setup] Could not seed subjects — endpoint may not exist');
  });
  console.log('[E2E Setup] Seeded subject categories & subjects');

  console.log('[E2E Setup] Seed complete.');
}

export default globalSetup;
