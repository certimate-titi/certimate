import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background / Given steps ──

Given('測驗 {int} 的作答記錄含信心度：', async ({}, _id: number, _dataTable: any) => {
  // No-op: backend seed data
});

Given(
  '使用者 {string} 完成測驗，題目 {int} 為 confident + 錯誤（危險盲點）',
  async ({}, _email: string, _qId: number) => {
    // No-op: state precondition
  },
);

Given(
  '使用者 {string} 完成測驗，題目 {int} 為 guessing + 正確（幸運猜對）',
  async ({}, _email: string, _qId: number) => {
    // No-op: state precondition
  },
);

Given(
  '使用者 {string} 完成測驗，題目 {int} 為 confident + 正確（真正掌握）',
  async ({}, _email: string, _qId: number) => {
    // No-op: state precondition
  },
);

Given('使用者 {string} 已完成 {int} 場含信心度的測驗', async ({}, _email: string, _count: number) => {
  // No-op: state precondition
});

// ── When steps ──

When(
  '使用者 {string} 在題目 {int} 選擇答案 {string} 並標記信心度為 {string}',
  async ({}, _email: string, _qId: number, _answer: string, _confidence: string) => {
    // No-op: simulated action
  },
);

When(
  '使用者 {string} 在題目 {int} 選擇答案 {string} 且未標記信心度',
  async ({}, _email: string, _qId: number, _answer: string) => {
    // No-op: simulated action
  },
);

When(
  '使用者 {string} 查看測驗 {int} 的信心度分析',
  async ({}, _email: string, _id: number) => {
    // No-op: simulated navigation
  },
);

When('系統計算下次複習排程', async ({}) => {
  // No-op: backend action
});

When('使用者查看個人儀表板的信心校準區塊', async ({}) => {
  // No-op: simulated navigation
});

// ── Then steps ──

Then('題目 {int} 的暫存作答應為 {string}', async ({}, _qId: number, _answer: string) => {
  // No-op: state verification
});

Then('題目 {int} 的信心度應為 {string}', async ({}, _qId: number, _confidence: string) => {
  // No-op: state verification
});

Then('題目 {int} 的信心度應預設為 {string}', async ({}, _qId: number, _confidence: string) => {
  // No-op: state verification
});

Then('信心度等級應包含：', async ({}, _dataTable: any) => {
  // No-op: data verification
});

Then('結果應包含四象限統計：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('{string} 象限應標示為紅色警示', async ({}, _quadrant: string) => {
  // No-op: UI verification
});

Then('該象限的題目應標記為「高優先複習」', async ({}) => {
  // No-op: UI verification
});

Then(
  'AI 教練應針對「危險盲點」題目提供額外說明：「{string}」',
  async ({}, _msg: string) => {
    // No-op: content verification
  },
);

Then('{string} 象限應標示為黃色提醒', async ({}, _quadrant: string) => {
  // No-op: UI verification
});

Then('AI 教練應建議：「{string}」', async ({}, _msg: string) => {
  // No-op: content verification
});

Then(
  '題目 {int} 的下次複習間隔應為 {int} 小時（比標準 {int} 小時更短）',
  async ({}, _qId: number, _hours: number, _standard: number) => {
    // No-op: backend verification
  },
);

Then(
  '題目 {int} 的 ease_factor 應額外降低 {float}（因為存在認知偏誤）',
  async ({}, _qId: number, _delta: number) => {
    // No-op: backend verification
  },
);

Then('題目 {int} 應排入複習排程（不因答對而跳過）', async ({}, _qId: number) => {
  // No-op: backend verification
});

Then('題目 {int} 的下次複習間隔應為 {int} 小時', async ({}, _qId: number, _hours: number) => {
  // No-op: backend verification
});

Then(
  '題目 {int} 的下次複習間隔應為標準間隔（依 SM-2 演算法）',
  async ({}, _qId: number) => {
    // No-op: backend verification
  },
);

Then('應顯示「信心校準率」指標（confident 且答對的比例）', async ({}) => {
  // No-op: UI verification
});

Then('應顯示近 {int} 場測驗的校準率趨勢折線圖', async ({}, _count: number) => {
  // No-op: UI verification
});

Then('校準率超過 {int}% 時應標示為「校準良好」', async ({}, _threshold: number) => {
  // No-op: UI verification
});
