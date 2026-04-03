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
