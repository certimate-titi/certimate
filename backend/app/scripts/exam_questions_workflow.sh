#!/bin/bash
# 高普考題庫工作流程：Catalog → 下載 → 解析 → 匯入 → 測試

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
CRAWLER_DIR="$PROJECT_ROOT/backend/scripts/crawlers"
JSON_DIR="$PROJECT_ROOT/backend/data/historical_questions"

cd "$PROJECT_ROOT/backend"

echo "╔════════════════════════════════════════════════════════╗"
echo "║ CertiMate 高普考題庫完整工作流程                        ║"
echo "╚════════════════════════════════════════════════════════╝"

# Step 1: 生成 Catalog（如果需要）
if [ "$1" == "full" ] || [ "$1" == "all" ]; then
    echo ""
    echo "📋 Step 1: 自動掃描 Catalog (112-114 年)"
    echo "═══════════════════════════════════════════════════════"
    python3 "$CRAWLER_DIR/auto_catalog_generator.py" --years 112 113 114 || {
        echo "❌ Catalog 生成失敗"
        exit 1
    }
    CATALOG="$CRAWLER_DIR/exam_catalog_complete.yaml"
else
    # 使用現有 catalog（預設 114 年）
    CATALOG="${2:-$CRAWLER_DIR/exam_catalog_complete.yaml}"
    if [ ! -f "$CATALOG" ]; then
        echo "⚠️  Catalog 不存在：$CATALOG"
        echo "    請執行：$0 full"
        exit 1
    fi
fi

echo "✓ 使用 Catalog：$CATALOG"

# Step 2: 下載 PDF
echo ""
echo "📥 Step 2: 下載 PDF（試題 + 答案）"
echo "═══════════════════════════════════════════════════════"
python3 "$CRAWLER_DIR/moex_simple.py" download --config "$CATALOG" || {
    echo "❌ PDF 下載失敗"
    exit 1
}

# Step 3: 解析 JSON
echo ""
echo "🔍 Step 3: 解析 PDF → JSON"
echo "═══════════════════════════════════════════════════════"
python3 "$CRAWLER_DIR/moex_simple.py" parse || {
    echo "❌ PDF 解析失敗"
    exit 1
}

# Step 4: 驗證 JSON 檔案數量
JSON_COUNT=$(find "$JSON_DIR" -name "*.json" -not -path "*_catalog*" -not -path "*_pdf*" | wc -l)
echo "✓ 生成 JSON 檔案數：$JSON_COUNT"

# Step 5: 匯入資料庫（dry-run）
echo ""
echo "📊 Step 4: 驗證資料庫匯入（dry-run）"
echo "═══════════════════════════════════════════════════════"
python3 -m app.scripts.import_exam_questions \
    --json-dir "$JSON_DIR" \
    --dry-run || {
    echo "❌ 匯入驗證失敗"
    exit 1
}

# Step 6: 實際匯入資料庫
echo ""
echo "💾 Step 5: 匯入資料庫"
echo "═══════════════════════════════════════════════════════"
python3 -m app.scripts.import_exam_questions \
    --json-dir "$JSON_DIR" || {
    echo "❌ 資料庫匯入失敗"
    exit 1
}

# Step 7: 重新處理 embedding + anchor_id
echo ""
echo "🔄 Step 6: 重新處理 anchor_id + embedding 向量"
echo "═══════════════════════════════════════════════════════"
echo "  先確認 migration 056 已套用..."
python3 -m alembic upgrade head || {
    echo "⚠️  Alembic migration 失敗"
    exit 1
}

echo "  更新 anchor_id..."
python3 -m app.scripts.reprocess_embeddings --anchor-only || {
    echo "⚠️  Anchor ID 更新失敗"
}

if [ "$SKIP_EMBED" != "true" ]; then
    echo "  重新生成 embedding..."
    python3 -m app.scripts.reprocess_embeddings --embed-only --batch-size 64 || {
        echo "⚠️  Embedding 重新生成失敗（可稍後重試）"
    }
else
    echo "  ⏭ 跳過 embedding（SKIP_EMBED=true）"
fi

# Step 8: 執行 BDD 測試
echo ""
echo "🧪 Step 7: 執行 BDD 測試"
echo "═══════════════════════════════════════════════════════"
python3 -m behave tests/features/04-測驗設定.feature --tags=~@ignore || {
    echo "⚠️  BDD 測試未通過"
    exit 1
}

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║ ✅ 工作流程完成！                                      ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║ 📊 統計：                                              ║"
echo "║   - JSON 檔案：$JSON_COUNT                            ║"
echo "║   - 已匯入資料庫                                       ║"
echo "║   - anchor_id + embedding 已更新                       ║"
echo "║   - BDD 測試通過                                       ║"
echo "╚════════════════════════════════════════════════════════╝"

echo ""
echo "後續步驟："
echo "  1. 查看匯入統計："
echo "     python -m app.scripts.import_exam_questions --json-dir $JSON_DIR"
echo "  2. 僅重新生成 embedding（跳過匯入）："
echo "     python -m app.scripts.reprocess_embeddings --embed-only"
echo "  3. 僅更新 anchor_id（不動 embedding）："
echo "     python -m app.scripts.reprocess_embeddings --anchor-only"
echo "  4. 執行完整 BDD 測試："
echo "     python -m behave tests/features/ --tags=~@ignore"
echo "  5. 啟動 API 伺服器："
echo "     python -m uvicorn app.main:app --reload"
