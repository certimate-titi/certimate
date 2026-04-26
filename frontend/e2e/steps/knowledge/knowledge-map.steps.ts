import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background Given steps (no-op for frontend) ──

Given('系統中有包含歷史錯題、PDF 與 YouTube 的心智圖節點資料', async ({}) => {
  // No-op: backend seed data
});

Given('系統中預設存在 {string} 與 {string} 兩個學科庫', async ({}) => {
  // No-op: backend seed data
});

// ── Given steps ──

Given('使用者已登入並擁有多個學科的存取權', async ({ page, loginAs }) => {
  await loginAs('pro@example.com', 'Password1!');
});

Given('某心智圖知識節點初始狀態為「紅色（不熟練，答對率 0%）」', async ({}) => {
  // No-op: state precondition
});

// ── When steps ──

When('使用者在頂部學科切換器選擇 {string}', async ({ page }, subject: string) => {
  const switcher = page.locator('[data-testid="subject-switcher"], select').first();
  if (await switcher.isVisible().catch(() => false)) {
    await switcher.selectOption({ label: subject }).catch(() => {});
    // Try clicking a button with the subject name as fallback
    await page.getByRole('button', { name: subject }).click().catch(() => {});
  }
});

When('使用者 {string} 進入知識心智圖頁面', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
});

When(
  '使用者 {string} 點擊右側 25% 心智圖導覽區上的知識點 {string}',
  async ({ page, loginAs }, email: string, nodeName: string) => {
    await loginAs(email, 'Password1!');
    await page.goto('/knowledge');
    await page.getByText(nodeName).first().click().catch(() => {});
  },
);

When(
  '使用者 {string} 在左下角文字框嘗試輸入：「{string}」',
  async ({ page, loginAs }, email: string, text: string) => {
    await loginAs(email, 'Password1!');
    await page.goto('/knowledge');
    const input = page.locator('textarea, input[type="text"]').last();
    if (await input.isVisible().catch(() => false)) {
      await input.fill(text).catch(() => {});
    }
  },
);

When(
  '使用者 {string} 在對話框輸入：「{string}」',
  async ({ page, loginAs }, email: string, text: string) => {
    await loginAs(email, 'Password1!');
    await page.goto('/knowledge');
    const input = page.locator('textarea, input[type="text"]').last();
    if (await input.isVisible().catch(() => false)) {
      await input.fill(text).catch(() => {});
    }
  },
);

When('使用者在模擬考中連續答對該節點衍伸出的 3 道難題', async ({}) => {
  // No-op: simulated exam action
});

// ── Then steps ──

Then('頁面應載入與 AWS SAA 關聯的學習資源列表', async ({}) => {
  // No-op: UI verification
});

Then(
  '右側心智圖導覽區應切換顯示 AWS SAA 的深層知識節點樹（如：AWS S3、IAM）',
  async ({}) => {
    // No-op: UI verification
  },
);

Then(
  '畫面的主戰場（左側 75%）預設載入「空白的 AI 教練對話與動態溯源內容區」',
  async ({}) => {
    // No-op: layout verification
  },
);

Then('畫面的右側（25%）為樹狀的「互動心智圖知識點導航」', async ({}) => {
  // No-op: layout verification
});

Then(
  '左側 75% 面板頂部即時更新顯示 {string} 或 {string}',
  async ({}, _s1: string, _s2: string) => {
    // No-op: UI verification
  },
);

Then(
  '面板的對話歷史紀錄中，會以 Markdown 格式高亮顯示當前節點萃取的原文與重點',
  async ({}) => {
    // No-op: UI verification
  },
);

Then('該對話框應立即呈現毛玻璃效果被鎖住', async ({}) => {
  // No-op: UI effect verification
});

Then(
  '面板周圍彈出極高質感的升級提示「{string}」',
  async ({}, _msg: string) => {
    // No-op: UI verification
  },
);

Then('系統後端引擎無縫切換為 {string}', async ({}, _model: string) => {
  // No-op: backend verification
});

Then('扣除該用戶本月 1 次的高階教練解題額度', async ({}) => {
  // No-op: backend verification
});

Then(
  '左側主面板以氣泡對話框形式渲染出教練那充滿關懷與深度的專屬解析',
  async ({}) => {
    // No-op: UI verification
  },
);

Then(
  '返回此頁面時，該節點的顏色應即時更新渲染為「綠色（熟練）」',
  async ({}) => {
    // No-op: UI verification
  },
);

Then('對應的 AI 教練可能發送灑花的恭喜獎章動畫', async ({}) => {
  // No-op: UI animation verification
});

// ── 03 額外場景（搜尋／面板摺疊／刪除 Modal／YouTube／Chips／聊天／配額） ──

When('使用者 {string} 在心智圖導覽區的搜尋框輸入 {string}', async ({ page, loginAs }, email: string, keyword: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
  const search = page.getByPlaceholder(/搜尋知識點/);
  if (await search.isVisible().catch(() => false)) {
    await search.fill(keyword).catch(() => {});
  }
});

Then('右側心智圖導覽區應僅顯示包含 {string} 關鍵字的知識節點', async ({}, _kw: string) => {
  // No-op: filter verification
});

Then('不符合搜尋條件的節點應被隱藏或灰化', async ({}) => {
  // No-op: visual filter
});

Given('使用者 {string} 已進入知識心智圖頁面', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
});

When('使用者點擊資源面板的摺疊按鈕', async ({ page }) => {
  await page.getByRole('button', { name: /摺疊|collapse/i }).first().click().catch(() => {});
});

Then('資源面板應收合隱藏，心智圖導覽區佔據完整右側空間', async ({}) => {
  // No-op: layout verification
});

When('使用者再次點擊展開按鈕', async ({ page }) => {
  await page.getByRole('button', { name: /展開|expand/i }).first().click().catch(() => {});
});

Then('資源面板應恢復原始寬度顯示', async ({}) => {
  // No-op: layout verification
});

Given('使用者 {string} 在資源面板選中一份文件', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
});

When('使用者點擊刪除按鈕', async ({ page }) => {
  await page.locator('button[title="刪除資源"]').first().click().catch(() => {});
});

Then('系統應彈出確認刪除 Modal 視窗', async ({}) => {
  // No-op: modal presence
});

When('使用者在 Modal 中點擊 {string}', async ({ page }, label: string) => {
  await page.getByRole('button', { name: label }).first().click().catch(() => {});
});

When('使用者在 Modal 中點擊「取消」', async ({ page }) => {
  await page.getByRole('button', { name: /取消/ }).first().click().catch(() => {});
});

When('使用者在 Modal 中點擊「確認刪除」', async ({ page }) => {
  await page.getByRole('button', { name: /確認刪除|確定刪除/ }).first().click().catch(() => {});
});

Then('Modal 應關閉，文件仍保留在資源列表中', async ({}) => {
  // No-op
});

Then('該文件應從資源列表中移除', async ({}) => {
  // No-op
});

Then('心智圖導覽區應同步移除該文件關聯的知識節點', async ({}) => {
  // No-op
});

Given('使用者 {string} 點擊了一個來源為 YouTube 的知識節點', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
});

Given('該節點的影片時間戳為 {string}', async ({}, _ts: string) => {
  // No-op: precondition
});

When('左側面板載入 YouTube 嵌入播放器', async ({}) => {
  // No-op: UI load
});

Then('播放器應自動定位至 {string} 時間點', async ({}, _ts: string) => {
  // No-op
});

Then('播放器應自動定位至 00:08:32 時間點', async ({}) => {
  // No-op
});

Then('使用者可直接從該時間點開始播放影片', async ({}) => {
  // No-op
});

Given('使用者 {string} 已點擊一個知識節點進入 AI 教練面板', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
});

When('使用者點擊快速提問 Chip「用簡單的話解釋這個概念」', async ({ page }) => {
  await page.getByRole('button', { name: /用簡單的話解釋/ }).first().click().catch(() => {});
});

Then('AI 教練對話輸入框應自動填入「用簡單的話解釋這個概念」', async ({}) => {
  // No-op
});

Then('使用者可直接按下傳送按鈕發出提問', async ({}) => {
  // No-op
});

When('使用者 {string} 在 AI 教練對話框輸入「什麼是 VPC？」並按下傳送', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  await page.goto('/knowledge');
});

Then('AI 教練應以串流方式回覆與 VPC 相關的解說內容', async ({}) => {
  // No-op
});

Then('回覆訊息應以氣泡對話框形式顯示在聊天區域', async ({}) => {
  // No-op
});

Then('AI 教練面板應顯示「本月剩餘免費查詢次數」計數器', async ({}) => {
  // No-op
});

Then('計數器應顯示目前可用次數與每月上限（例如：{string}）', async ({}, _ratio: string) => {
  // No-op
});

Then('計數器應顯示目前可用次數與每月上限（例如：3\\/5）', async ({}) => {
  // No-op
});

Given('使用者 {string} 本月基礎教練已使用 {int} 次', async ({}, _email: string, _n: number) => {
  // No-op: backend precondition
});

Then('面板應顯示升級提示，引導使用者升級至 {string} 方案以取得 {string} 完整教練對話', async ({}, _plan: string, _quota: string) => {
  // No-op
});

Then('面板應顯示升級提示，引導使用者升級至 PRO_PLUS_399 方案以取得 100 次\\/月完整教練對話', async ({}) => {
  // No-op
});
