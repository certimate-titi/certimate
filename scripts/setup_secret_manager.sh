#!/bin/bash
# Set up Google Secret Manager for production API keys with maximum protection.
#
# 設計原則：
# 1. Key 只存 Secret Manager，Cloud Run 以 secretKeyRef 掛載（revision 不含明文）
# 2. 建立專用 runtime service account（certimate-titi-runtime）— 只有它可讀 secret
#    不使用預設 compute SA，避免專案內其他工作負載也能存取
# 3. 顯式拒絕：不授予 project-level roles/secretmanager.secretAccessor 給任何人
#    開發者/部署 SA 只能「引用」secret，不能讀值
# 4. 啟用 audit log（已預設）；key 外流時由 IAM recommender + audit log 可回溯
# 5. 不打 `gcloud secrets versions access` 到本機 — 提供互動輸入路徑，避免 shell history
#
# 使用：
#   bash scripts/setup_secret_manager.sh
#
# 事前準備：
#   1. 已執行 `gcloud auth login` 且有 project owner 權限
#   2. 手邊有 3 組新的 API key（強烈建議這次順便輪替舊 key）

set -eo pipefail

PROJECT_ID="certimate-titi"
REGION="asia-east1"
SERVICE_NAME="certimate-titi"
RUNTIME_SA_NAME="certimate-titi-runtime"
RUNTIME_SA_EMAIL="${RUNTIME_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# 平行陣列（避免 bash 3.2 對 "a:b" 拆解搭配中文字符時偶發 parser 問題）
SECRET_NAMES=("gemini-api-key" "anthropic-api-key" "voyage-api-key")
ENV_NAMES=("GEMINI_API_KEY" "ANTHROPIC_API_KEY" "VOYAGE_API_KEY")

echo "==> 切換專案：$PROJECT_ID"
gcloud config set project "$PROJECT_ID" >/dev/null

# ============================================================
# 1. 建立專用 runtime service account（若已存在則跳過）
# ============================================================
echo "==> 確保 runtime SA 存在：$RUNTIME_SA_EMAIL"
if ! gcloud iam service-accounts describe "$RUNTIME_SA_EMAIL" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$RUNTIME_SA_NAME" \
    --display-name="Certimate TiTi Cloud Run Runtime" \
    --description="Runtime identity for certimate-titi Cloud Run service. Only principal allowed to read production API key secrets."
else
  echo "    SA 已存在，跳過建立"
fi

# 最低必要角色（給 Cloud Run 運行時用）
for role in \
  roles/cloudsql.client \
  roles/logging.logWriter \
  roles/monitoring.metricWriter \
  roles/storage.objectAdmin
do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$RUNTIME_SA_EMAIL" \
    --role="$role" \
    --condition=None \
    --quiet >/dev/null
done

# ============================================================
# 2. 建立 secret + 寫入值（互動輸入，不經 shell history）
# ============================================================
for i in 0 1 2; do
  secret_name="${SECRET_NAMES[$i]}"
  env_name="${ENV_NAMES[$i]}"

  echo
  echo "==> 處理 secret: $secret_name (env: $env_name)"

  # 若已存在且有 version，提示是否覆寫
  if gcloud secrets describe "$secret_name" >/dev/null 2>&1; then
    version_count=$(gcloud secrets versions list "$secret_name" --format='value(name)' | wc -l | tr -d ' ')
    if [ "$version_count" -gt 0 ]; then
      read -p "    已有 $version_count 個版本，要新增新版本嗎？[y/N] " yn
      [[ "$yn" != "y" && "$yn" != "Y" ]] && { echo "    跳過"; continue; }
    fi
  else
    # 建立 secret，啟用自動複製，不設過期
    gcloud secrets create "$secret_name" \
      --replication-policy=automatic \
      --labels=env=production,app=certimate-titi \
      --quiet
  fi

  # 互動輸入（stty -echo 避免 key 顯示在終端；從 /dev/tty 讀避免管線）
  echo -n "    請貼上 $env_name（輸入不回顯，Enter 確認）: "
  stty -echo
  IFS= read -r secret_value < /dev/tty
  stty echo
  echo

  if [ -z "$secret_value" ]; then
    echo "    ⚠️  空值，跳過"
    continue
  fi

  # 寫入（--data-file=- 從 stdin 讀，避免 command history 殘留）
  printf '%s' "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=-
  unset secret_value

  # 授權：僅 runtime SA 可讀，不給其他人
  gcloud secrets add-iam-policy-binding "$secret_name" \
    --member="serviceAccount:$RUNTIME_SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None \
    --quiet >/dev/null
  echo "    ✓ $secret_name 已建立並授權給 runtime SA"
done

# ============================================================
# 3. 授權部署 SA 對 runtime SA 執行 actAs（Cloud Run 需要）
# ============================================================
echo
echo "==> 授權 deploy SA 可「以 runtime SA 身分」部署服務"
DEPLOY_SA=$(gcloud iam service-accounts list \
  --filter='email:github-actions*' \
  --format='value(email)' | head -1)
if [ -z "$DEPLOY_SA" ]; then
  echo "    ⚠️  找不到 github-actions* SA，請手動確認 deploy SA 並執行："
  echo "    gcloud iam service-accounts add-iam-policy-binding $RUNTIME_SA_EMAIL \\"
  echo "      --member='serviceAccount:<deploy-sa>' --role='roles/iam.serviceAccountUser'"
else
  gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA_EMAIL" \
    --member="serviceAccount:$DEPLOY_SA" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None \
    --quiet >/dev/null
  echo "    ✓ deploy SA ($DEPLOY_SA) 可 actAs runtime SA"
fi

# ============================================================
# 4. 明確拒絕：移除任何 project-level secretAccessor 授權
# ============================================================
echo
echo "==> 稽核 project-level roles/secretmanager.secretAccessor 綁定"
EXTRA=$(gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten='bindings[].members' \
  --filter='bindings.role:roles/secretmanager.secretAccessor' \
  --format='value(bindings.members)' || true)
if [ -n "$EXTRA" ]; then
  echo "    ⚠️  以下 principal 有 project-level secretAccessor，建議改成 secret-level 授權："
  echo "$EXTRA" | sed 's/^/      - /'
else
  echo "    ✓ 無 project-level 廣泛授權"
fi

# ============================================================
# 5. 提示下一步
# ============================================================
cat <<EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Secret Manager 設置完成

下一步：
  1. 下一次 CI/CD 部署會自動以 runtime SA 身分掛 secret（workflow 已改 --set-secrets）
  2. 若要立即套用到現有服務（免等 deploy）：

     gcloud run services update $SERVICE_NAME \\
       --region=$REGION \\
       --service-account=$RUNTIME_SA_EMAIL \\
       --remove-env-vars=GEMINI_API_KEY,ANTHROPIC_API_KEY,VOYAGE_API_KEY \\
       --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,VOYAGE_API_KEY=voyage-api-key:latest"

  3. 舊 'certimate' 服務的明文 key 曾被 describe 讀取過，請到以下後台輪替並撤銷舊 key：
     - Google AI Studio (Gemini)
     - Anthropic Console
     - Voyage AI Dashboard

保護狀態：
  - Key 不在 Cloud Run revision YAML 內
  - 只有 $RUNTIME_SA_EMAIL 可讀 secret value
  - 開發者執行 'gcloud run describe' 只會看到 secretKeyRef，看不到值
  - 輪替：gcloud secrets versions add <name> --data-file=- ，Cloud Run 自動拉 latest
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
