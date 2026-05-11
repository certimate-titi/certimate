"""Given Resource stub — Feature 38 prompt routing BDD."""

from behave import given, use_step_matcher


class _ResourceStub:
    """輕量 stub，避免 SQLAlchemy instrumentation。"""

    def __init__(self, gcs_path, youtube_url, detected_content_type, name="virtual"):
        self.gcs_path = gcs_path
        self.youtube_url = youtube_url
        self.detected_content_type = detected_content_type
        self.name = name


use_step_matcher("re")


@given(
    r'resource gcs_path="(?P<gcs>[^"]*)" 並 detected_content_type="(?P<dct>[^"]*)" '
    r'並 youtube_url="(?P<yt>[^"]*)"'
)
def step_resource_routing_with_zh_separator(context, gcs, dct, yt):
    """F38 路由 stub（中文「並」分隔欄位，支援空字串）。"""
    r = _ResourceStub(
        gcs_path=gcs if gcs else None,
        youtube_url=yt if yt else None,
        detected_content_type=dct if dct else None,
        name=gcs or "virtual.pdf",
    )
    context.memo["routing_resource"] = r


use_step_matcher("parse")


@given('resource gcs_path="{gcs}"')
def step_resource_gcs_only(context, gcs):
    """單一 gcs_path 欄位設定（其餘 None）。"""
    r = _ResourceStub(gcs_path=gcs, youtube_url=None, detected_content_type=None, name=gcs)
    context.memo["routing_resource"] = r


@given('DB 中無 \'{template_name}\' 模板')
def step_db_without_template(context, template_name):
    """確認 DB 中該模板不存在（不主動刪除，僅斷言狀態）。"""
    from app.models.prompt_template import PromptTemplateV2

    db = context.db_session
    existing = (
        db.query(PromptTemplateV2)
        .filter(PromptTemplateV2.name == template_name)
        .first()
    )
    assert existing is None, (
        f"預期 DB 無 '{template_name}' 模板，但找到 id={existing.template_id}"
    )
    context.memo["missing_template_name"] = template_name
