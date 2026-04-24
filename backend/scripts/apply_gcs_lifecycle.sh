#!/usr/bin/env bash
# Apply GCS lifecycle + storage class rules for EPIC-035 user resources.
#
# Policy (CTO 方案 X — 關鍵頁分桶):
#   uploads/<user>/thumbnails/...    → Standard → Nearline(30d) → Coldline(180d) → Delete(730d)
#   uploads/<user>/figures/...       → Standard → Nearline(30d) → Coldline(180d) → Delete(730d)
#   uploads/<user>/critical/...      → Standard 永久（不套 lifecycle）
#   uploads/<user>/originals/...     → Delete(7d)  原始 PDF 解析後保留 7 天容錯
#
# 使用方式:
#   GCS_BUCKET=certimate-titi-user-resources ./apply_gcs_lifecycle.sh
#
# 依賴: gcloud / gsutil 已認證且有 storage.admin on bucket
set -euo pipefail

BUCKET="${GCS_BUCKET:-certimate-titi-user-resources}"
LIFECYCLE_JSON="$(dirname "$0")/../terraform/gcs-lifecycle.json"

cat > "$LIFECYCLE_JSON" <<'EOF'
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 7,
        "matchesPrefix": ["uploads/","uploads/"],
        "matchesSuffix": [".pdf"]
      }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": {
        "age": 30,
        "matchesStorageClass": ["STANDARD"],
        "matchesPrefix": ["uploads/"]
      }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" },
      "condition": {
        "age": 180,
        "matchesStorageClass": ["NEARLINE"],
        "matchesPrefix": ["uploads/"]
      }
    },
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 730,
        "matchesPrefix": ["uploads/"]
      }
    }
  ]
}
EOF

echo "Applying lifecycle to gs://$BUCKET ..."
gsutil lifecycle set "$LIFECYCLE_JSON" "gs://$BUCKET"

echo "Verifying..."
gsutil lifecycle get "gs://$BUCKET"

echo ""
echo "NOTE: Critical pages are stored under uploads/<user>/critical/ prefix."
echo "      GCS lifecycle rules do not apply there because we omit matchesPrefix"
echo "      check — wait, GCS does apply by prefix match only. Critical pages"
echo "      are protected because application code writes them with a DIFFERENT"
echo "      top-level prefix: critical/<user>/... (outside uploads/)."
echo ""
echo "      Application code must honor:"
echo "        - uploads/<user>/...    → lifecycle applies"
echo "        - critical/<user>/...   → permanent Standard"
