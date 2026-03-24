"""API 路由註冊。"""

from fastapi import APIRouter

router = APIRouter()

# 在此 include 各 domain 的 sub-router
# from {{PY_APP_MODULE}}.api.some_domain import router as some_domain_router
# router.include_router(some_domain_router, prefix="/some-domain", tags=["some-domain"])
