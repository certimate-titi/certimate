#!/bin/sh

echo "=== CertiMate Backend Startup ==="

# Run Alembic migrations (retry up to 3 times, non-fatal)
echo "Running database migrations..."
RETRY=0
MAX_RETRY=3
while [ $RETRY -lt $MAX_RETRY ]; do
    if python -m alembic upgrade head 2>&1; then
        echo "Migrations complete."
        break
    else
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRY ]; then
            echo "Migration attempt $RETRY failed, retrying in 5s..."
            sleep 5
        else
            echo "WARNING: Migrations failed after $MAX_RETRY attempts. Starting server anyway..."
        fi
    fi
done

# Download historical questions from GCS + import to DB (idempotent, non-fatal)
echo "Syncing historical questions from GCS + importing to DB..."
python -c "
from app.scripts.sync_from_gcs import sync_and_import
result = sync_and_import()
sr = result.get('sync_result', {})
ir = result.get('import_result', {})
print(f'  GCS: {sr.get(\"downloaded\",0)} downloaded, {sr.get(\"skipped\",0)} skipped, {len(sr.get(\"errors\",[]))} errors')
if ir:
    print(f'  DB: {ir.get(\"imported\",0)} imported, {ir.get(\"skipped\",0)} skipped, {ir.get(\"errors\",0)} errors')
" 2>&1 || echo "WARNING: GCS sync+import failed (non-fatal)"

# Seed prompt templates from GCS (if available, non-fatal)
echo "Syncing prompt templates from GCS..."
python -c "
from app.scripts.sync_prompts_from_gcs import sync_and_seed_prompts
result = sync_and_seed_prompts()
print(f'  Prompts: {result}')
" 2>&1 || echo "WARNING: Prompt sync failed (non-fatal, templates may not be in GCS yet)"

# Seed exam_subject_codes (idempotent, retry up to 3 times)
echo "Seeding exam_subject_codes..."
SEED_RETRY=0
while [ $SEED_RETRY -lt 3 ]; do
    if python -c "
from app.scripts.seed_exam_codes import seed_exam_codes
result = seed_exam_codes()
print(f'  Seed: {result}')
if 'error' in result:
    raise SystemExit(1)
" 2>&1; then
        echo "Exam codes seeded."
        break
    else
        SEED_RETRY=$((SEED_RETRY + 1))
        if [ $SEED_RETRY -lt 3 ]; then
            echo "Seed attempt $SEED_RETRY failed, retrying in 3s..."
            sleep 3
        else
            echo "WARNING: exam_subject_codes seed failed after 3 attempts."
        fi
    fi
done

# Start the server
echo "Starting Uvicorn on port ${PORT:-8080}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}" --workers 1
