# CertiMate Frontend

Next.js 15 + React 19 前端應用，搭配 FastAPI 後端與 Firebase 認證。

## 開發

```bash
npm install
cp .env.example .env.local   # 填入 NEXT_PUBLIC_API_URL 等
npm run dev                   # http://localhost:3005
```

需要後端運行於 `http://localhost:8000/api/v1`。demo 登入：`admin@certimate.com` / `admin123`。

## 指令

```bash
npm run dev     # 開發（使用 .next-dev/）
npm run build   # 正式建置（靜態匯出到 .next/）
npm run lint    # ESLint
npm run clean   # 清 Next.js 快取
```

## 部署

推送 `main` 觸發 GitHub Actions → Firebase Hosting (`certimate-titi.web.app`)。

## 詳細說明

- 架構、頁面、API 服務清單、動態路由陷阱：見 [CLAUDE.md](CLAUDE.md)
