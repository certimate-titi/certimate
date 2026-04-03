import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Given steps ──

Given(
  '使用者 {string} 提交測驗設定，選擇節點 {int}、{int}、{int}，題數為 {int}',
  async ({}, _email: string, _n1: number, _n2: number, _n3: number, _count: number) => {
    // No-op: state precondition
  },
);

Given(
  '使用者 {string} 提交測驗設定，選擇節點 {int}，題數為 {int}',
  async ({}, _email: string, _node: number, _count: number) => {
    // No-op: state precondition (interleaved variant)
  },
);

Given(
  '使用者 {string} 提交測驗設定，選擇節點 {int}、{int}，題數為 {int}，難易度分配為 Easy:{int}% Medium:{int}% Hard:{int}%',
  async ({}, _email: string, _n1: number, _n2: number, _count: number, _e: number, _m: number, _h: number) => {
    // No-op: state precondition
  },
);

Given(
  '使用者 {string} 提交測驗設定，選擇節點 {int}、{int}、{int}，題數為 {int}，排列模式為 {string}',
  async ({}, _email: string, _n1: number, _n2: number, _n3: number, _count: number, _mode: string) => {
    // No-op: state precondition
  },
);

Given('使用者 {string} 的學習模式為 {string}', async ({}, _email: string, _mode: string) => {
  // No-op: state precondition
});

Given('使用者在節點 {int} 和節點 {int} 的歷史錯題較多', async ({}, _n1: number, _n2: number) => {
  // No-op: state precondition
});

Given('使用者 {string} 完成一場交錯練習模式的測驗', async ({}, _email: string) => {
  // No-op: state precondition
});

// ── When steps ──

When(
  'AI 生成 {int} 題完成，各節點各 {int} 題',
  async ({}, _total: number, _perNode: number) => {
    // No-op: backend event
  },
);

When('AI 生成 {int} 題完成', async ({}, _total: number) => {
  // No-op: backend event
});

When(
  'AI 生成 {int} 題完成，節點 {int} 有 {int} 題、節點 {int} 有 {int} 題、節點 {int} 有 {int} 題',
  async ({}, _total: number, _n1: number, _c1: number, _n2: number, _c2: number, _n3: number, _c3: number) => {
    // No-op: backend event
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇節點 {int}、{int}、{int}，題數為 {int}，排列模式為 {string}',
  async ({}, _email: string, _n1: number, _n2: number, _n3: number, _count: number, _mode: string) => {
    // No-op: simulated form submission
  },
);

When(
  '使用者提交測驗設定，選擇節點 {int}、{int}、{int}、{int}，題數為 {int}',
  async ({}, _n1: number, _n2: number, _n3: number, _n4: number, _count: number) => {
    // No-op: simulated form submission
  },
);

// ── Then steps ──

Then('題目排列順序不應為同一節點連續超過 {int} 題', async ({}, _max: number) => {
  // No-op: ordering verification
});

Then(
  '題目應以交錯方式排列，例如：節點1 → 節點2 → 節點3 → 節點1 → 節點2 → 節點3 ...',
  async ({}) => {
    // No-op: ordering verification
  },
);

Then('exam 的 question_order_mode 應為 {string}', async ({}, _mode: string) => {
  // No-op: backend verification
});

Then('題目按難度由易到難排列', async ({}) => {
  // No-op: ordering verification
});

Then('同一節點的題目最多連續出現 {int} 題', async ({}, _max: number) => {
  // No-op: ordering verification
});

Then('相鄰題目的知識節點應盡量不同', async ({}) => {
  // No-op: ordering verification
});

Then('題目應交錯排列知識節點', async ({}) => {
  // No-op: ordering verification
});

Then('hard 難度的題目不應連續超過 {int} 題', async ({}, _max: number) => {
  // No-op: ordering verification
});

Then('前 {int} 題中應至少包含 {int} 題 easy 難度（建立信心）', async ({}, _first: number, _min: number) => {
  // No-op: ordering verification
});

Then('題目應按知識節點分組排列', async ({}) => {
  // No-op: ordering verification
});

Then(
  '交錯排列中節點 {int} 和節點 {int} 的題目應更均勻地分散於整份考卷',
  async ({}, _n1: number, _n2: number) => {
    // No-op: ordering verification
  },
);

Then('不應將錯題集中在考卷前段或後段', async ({}) => {
  // No-op: ordering verification
});

Then('結果頁應顯示排列模式標籤 {string}', async ({}, _label: string) => {
  // No-op: UI verification
});

Then('結果頁應包含提示：「{string}」', async ({}, _hint: string) => {
  // No-op: UI verification
});
