"""
API 路由模块
"""
from fastapi import APIRouter

from .upload import router as upload_router
from .session import router as session_router
from .agent import router as agent_router
from .history import router as history_router

# 创建主路由
router = APIRouter()

# 注册子路由
router.include_router(upload_router, tags=["文件上传"])
router.include_router(session_router, tags=["Session管理"])
router.include_router(agent_router, tags=["Agent分析"])
router.include_router(history_router, tags=["历史记录"])


