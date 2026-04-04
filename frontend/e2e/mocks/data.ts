/**
 * Mock data for Playwright E2E tests.
 * Matches the Background users defined in feature files.
 */

export interface MockUser {
  id: string;
  email: string;
  password: string;
  subscription_plan: string;
  role: string;
  status: string;
  onboarding_completed: boolean;
  display_name: string;
}

/** Users from Feature 01 Background + other features */
export const USERS: MockUser[] = [
  { id: '1', email: 'alice@example.com', password: 'Password1!', subscription_plan: 'FREE', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'Alice' },
  { id: '2', email: 'bob@example.com', password: 'Password1!', subscription_plan: 'PRO', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'Bob' },
  { id: '3', email: 'carol@example.com', password: 'Password1!', subscription_plan: 'ULTRA', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'Carol' },
  { id: '4', email: 'pending@example.com', password: 'Pending1!', subscription_plan: 'FREE', role: 'USER', status: '待驗證', onboarding_completed: false, display_name: 'Pending' },
  { id: '5', email: 'admin@example.com', password: 'Password1!', subscription_plan: 'FREE', role: 'ADMIN', status: '已啟用', onboarding_completed: true, display_name: 'Admin' },
  { id: '6', email: 'admin@certimate.com', password: 'admin123', subscription_plan: 'ULTRA', role: 'ADMIN', status: '已啟用', onboarding_completed: true, display_name: 'Super Admin' },
  { id: '7', email: 'free@example.com', password: 'Password1!', subscription_plan: 'FREE', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'FreeUser' },
  { id: '8', email: 'pro@example.com', password: 'Password1!', subscription_plan: 'PRO', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'ProUser' },
  { id: '9', email: 'proplus@example.com', password: 'Password1!', subscription_plan: 'PRO_PLUS', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'ProPlusUser' },
  { id: '10', email: 'ultra@example.com', password: 'Password1!', subscription_plan: 'ULTRA', role: 'USER', status: '已啟用', onboarding_completed: true, display_name: 'UltraUser' },
  { id: '11', email: 'newbie@example.com', password: 'Password1!', subscription_plan: 'FREE', role: 'USER', status: '已啟用', onboarding_completed: false, display_name: 'Newbie' },
  // newuser@example.com and new@example.com NOT pre-seeded — they're "new" registrations in tests
];

/** Runtime overrides applied by Given steps — reset before each test */
const userOverrides = new Map<string, Partial<MockUser>>();

export function setUserOverride(email: string, overrides: Partial<MockUser>) {
  // If user doesn't exist in base data, create them dynamically
  if (!USERS.find((u) => u.email === email)) {
    USERS.push({
      id: String(100 + USERS.length),
      email,
      password: '*', // wildcard — accept any password for dynamically created users
      subscription_plan: 'FREE',
      role: 'USER',
      status: '已啟用',
      onboarding_completed: false,
      display_name: email.split('@')[0],
      ...overrides,
    });
    return;
  }
  userOverrides.set(email, { ...userOverrides.get(email), ...overrides });
}

export function clearOverrides() {
  userOverrides.clear();
  resetExams();
}

export function findUser(email: string): MockUser | undefined {
  const base = USERS.find((u) => u.email === email);
  if (!base) return undefined;
  const overrides = userOverrides.get(email);
  return overrides ? { ...base, ...overrides } : base;
}

export function findUserByToken(token: string): MockUser | undefined {
  // Token is a fake JWT: header.payload.signature
  // Payload contains { sub: userId, email }
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return undefined;
    const payload = JSON.parse(atob(parts[1]));
    const base = USERS.find((u) => u.id === payload.sub);
    if (!base) return undefined;
    const overrides = userOverrides.get(base.email);
    return overrides ? { ...base, ...overrides } : base;
  } catch {
    return undefined;
  }
}

/** Mock exam data keyed by exam ID */
export interface MockExam {
  id: number;
  owner_email: string;
  status: string; // READY | IN_PROGRESS | SUBMITTED
  question_count: number;
}

export const EXAMS: MockExam[] = [
  { id: 1, owner_email: 'alice@example.com', status: 'READY', question_count: 20 },
  { id: 2, owner_email: 'alice@example.com', status: 'SUBMITTED', question_count: 20 },
  { id: 3, owner_email: 'alice@example.com', status: 'IN_PROGRESS', question_count: 20 },
  { id: 4, owner_email: 'alice@example.com', status: 'SUBMITTED', question_count: 20 },
  { id: 5, owner_email: 'bob@example.com', status: 'READY', question_count: 10 },
  { id: 10, owner_email: 'alice@example.com', status: 'IN_PROGRESS', question_count: 20 },
];

/** Override or add an exam entry at runtime (for Given steps) */
export function setExamOverride(exam: MockExam): void {
  const idx = EXAMS.findIndex((e) => e.id === exam.id);
  if (idx >= 0) EXAMS[idx] = exam;
  else EXAMS.push(exam);
}

/** Reset exams to default state (call in beforeEach) */
const DEFAULT_EXAMS: MockExam[] = JSON.parse(JSON.stringify(EXAMS));
export function resetExams(): void {
  EXAMS.length = 0;
  EXAMS.push(...JSON.parse(JSON.stringify(DEFAULT_EXAMS)));
}

/** Onboarding subject catalog */
export const SUBJECT_CATALOG = {
  categories: [
    {
      id: 'cat_finance',
      name: '金融證照',
      subjects: [
        { id: 1, name: '信託業業務人員', exam_count: 5 },
        { id: 2, name: '投信投顧業務人員', exam_count: 3 },
        { id: 3, name: '期貨分析師', exam_count: 4 },
        { id: 8, name: '證券商業務員', exam_count: 6 },
        { id: 9, name: '期貨商業務員', exam_count: 3 },
      ],
    },
    {
      id: 'cat_tech',
      name: 'IT 技術',
      subjects: [
        { id: 4, name: 'AWS SAA', exam_count: 6 },
        { id: 5, name: 'PMP', exam_count: 8 },
        { id: 6, name: 'AI 應用規劃師', exam_count: 3 },
      ],
    },
    {
      id: 'cat_real_estate',
      name: '不動產',
      subjects: [
        { id: 7, name: '不動產經紀人', exam_count: 4 },
      ],
    },
  ],
};
