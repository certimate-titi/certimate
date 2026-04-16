"""Prompt 模板 Seed 腳本 — 從檔案系統同步至 DB (Feature 30).

執行方式：
    cd backend
    python -m app.scripts.seed_prompts

Seed 邏輯：
  1. 掃描 project/03_Research_and_Development/03_Prompt_Templates/ 下所有 .md 檔
  2. 解析 YAML frontmatter + prompt 內容
  3. DB 中不存在 → INSERT（建立模板 + 版本 1）
  4. DB 中已存在但檔案 version > DB version → UPDATE（建立新版本）
  5. DB 中已存在且版本相同 → SKIP
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Optional

# 添加 backend 目錄至 path
_backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_backend_dir))

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.prompt_template import PromptTemplateV2, PromptTemplateVersion, PromptCategory
from app.repositories.prompt_template_repository import PromptTemplateRepository

# 模板檔案所在目錄 — 支援自定義路徑（CI/CD 從 GCS 下載到 /tmp）
_DEFAULT_TEMPLATES_DIR = (
    _backend_dir.parent
    / "project"
    / "03_Research_and_Development"
    / "03_Prompt_Templates"
)

# Allow override via env var or CLI (for GCS-synced prompts in production)
import os as _os
_TEMPLATES_DIR = Path(_os.environ.get("PROMPT_TEMPLATES_DIR", str(_DEFAULT_TEMPLATES_DIR)))


def _parse_md_file(filepath: Path) -> Optional[dict]:
    """解析 Markdown 檔案的 YAML frontmatter + prompt 內容。"""
    content = filepath.read_text(encoding="utf-8")

    # 解析 YAML frontmatter（--- ... ---）
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not match:
        print(f"  ⚠️  跳過（無 frontmatter）: {filepath.name}")
        return None

    frontmatter_str = match.group(1)
    body = match.group(2)

    try:
        meta = yaml.safe_load(frontmatter_str)
    except yaml.YAMLError as e:
        print(f"  ⚠️  YAML 解析失敗 {filepath.name}: {e}")
        return None

    # 解析 System Prompt
    system_match = re.search(
        r"##\s+System Prompt\s*\n```\n(.*?)\n```", body, re.DOTALL
    )
    system_prompt = system_match.group(1).strip() if system_match else ""

    # 解析 User Prompt
    user_match = re.search(
        r"##\s+User Prompt\s*\n```\n(.*?)\n```", body, re.DOTALL
    )
    user_prompt = user_match.group(1).strip() if user_match else "{user_input}"

    return {
        "template_id": meta.get("id", ""),
        "name": meta.get("name", ""),
        "display_name": meta.get("display_name", ""),
        "category": meta.get("category", "safety"),
        "model": meta.get("model", "gemini-flash"),
        "max_tokens": int(meta.get("max_tokens", 1024)),
        "max_tokens_by_plan": meta.get("max_tokens_by_plan"),
        "temperature": float(meta.get("temperature", 0.5)),
        "variables": meta.get("variables", []),
        "feature_refs": meta.get("feature_refs", []),
        "file_version": int(meta.get("version", 1)),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def _scan_templates() -> list[dict]:
    """掃描所有模板 .md 檔案。"""
    templates = []
    for md_file in sorted(_TEMPLATES_DIR.rglob("*.md")):
        if md_file.name == "README.md":
            continue
        data = _parse_md_file(md_file)
        if data and data["template_id"]:
            templates.append(data)
    return templates


def run_seed(db_url: Optional[str] = None):
    """執行 seed 同步。"""
    settings = get_settings()
    url = db_url or settings.DATABASE_URL

    engine = create_engine(url)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo = PromptTemplateRepository(session)

    print(f"📂 掃描模板目錄：{_TEMPLATES_DIR}")
    file_templates = _scan_templates()
    print(f"   找到 {len(file_templates)} 個模板檔案")

    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    for data in file_templates:
        tid = data["template_id"]
        file_version = data["file_version"]

        try:
            existing = repo.find_by_template_id(tid)

            if not existing:
                # INSERT
                template = PromptTemplateV2(
                    template_id=tid,
                    name=data["name"],
                    display_name=data["display_name"],
                    category=data["category"],
                    model=data["model"],
                    max_tokens=data["max_tokens"],
                    max_tokens_by_plan=data.get("max_tokens_by_plan"),
                    temperature=data["temperature"],
                    system_prompt=data["system_prompt"],
                    user_prompt=data["user_prompt"],
                    variables=data.get("variables", []),
                    feature_refs=data.get("feature_refs", []),
                    current_version=file_version,
                    is_active=True,
                )
                saved = repo.save(template)

                # 建立版本 1
                version_obj = PromptTemplateVersion(
                    template_id=saved.id,
                    version=file_version,
                    model=saved.model,
                    max_tokens=saved.max_tokens,
                    max_tokens_by_plan=saved.max_tokens_by_plan,
                    temperature=float(saved.temperature),
                    system_prompt=saved.system_prompt,
                    user_prompt=saved.user_prompt,
                    variables=saved.variables or [],
                    change_note="Seeded from file system",
                )
                repo.save_version(version_obj)

                print(f"  ✅ 新增：{tid} {data['name']} (v{file_version})")
                stats["created"] += 1

            elif existing.current_version < file_version:
                # UPDATE
                old_version = existing.current_version
                existing.system_prompt = data["system_prompt"]
                existing.user_prompt = data["user_prompt"]
                existing.model = data["model"]
                existing.max_tokens = data["max_tokens"]
                existing.temperature = data["temperature"]
                existing.variables = data.get("variables", [])
                existing.current_version = file_version
                session.commit()

                version_obj = PromptTemplateVersion(
                    template_id=existing.id,
                    version=file_version,
                    model=existing.model,
                    max_tokens=existing.max_tokens,
                    max_tokens_by_plan=existing.max_tokens_by_plan,
                    temperature=float(existing.temperature),
                    system_prompt=existing.system_prompt,
                    user_prompt=existing.user_prompt,
                    variables=existing.variables or [],
                    change_note=f"Updated from file system v{old_version}→v{file_version}",
                )
                repo.save_version(version_obj)

                print(f"  🔄 更新：{tid} {data['name']} (v{old_version}→v{file_version})")
                stats["updated"] += 1

            else:
                print(f"  ⏭️  跳過：{tid} {data['name']} (v{existing.current_version} = file v{file_version})")
                stats["skipped"] += 1

        except Exception as e:
            print(f"  ❌ 錯誤：{tid} — {e}")
            session.rollback()
            stats["errors"] += 1

    # 清理孤兒：DB 中存在但檔案已刪除的模板 → 停用
    file_ids = {d["template_id"] for d in file_templates}
    all_db_templates = repo.find_all()
    orphan_count = 0
    for t in all_db_templates:
        if t.template_id not in file_ids and t.is_active:
            t.is_active = False
            session.commit()
            print(f"  🗑️  停用孤兒：{t.template_id} {t.name}")
            orphan_count += 1
    stats["deactivated"] = orphan_count

    session.close()

    print("\n📊 Seed 結果：")
    print(f"   ✅ 新增：{stats['created']} 個")
    print(f"   🔄 更新：{stats['updated']} 個")
    print(f"   ⏭️  跳過：{stats['skipped']} 個")
    if stats.get("deactivated"):
        print(f"   🗑️  停用：{stats['deactivated']} 個")
    if stats["errors"]:
        print(f"   ❌ 錯誤：{stats['errors']} 個")

    return stats


# Alias for sync_prompts_from_gcs.py to call
seed_all = run_seed


if __name__ == "__main__":
    run_seed()
