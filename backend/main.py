"""
FastAPI 应用主入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from config import settings
from api import router
from core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 创建必要的目录
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    # 初始化数据库
    await init_db()
    
    yield


# 创建FastAPI应用
app = FastAPI(
    title="智能数据分析工具 API",
    description="基于 Jupyter Kernel 的智能数据分析后端",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "智能数据分析工具 API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 智能数据分析工具后端启动中...")
    print("=" * 60)
    print(f"✅ AI 提供商: {settings.ai_provider}")
    if settings.ai_provider == "openai":
        print(f"✅ AI 模型: {settings.openai_model}")
        print(f"✅ API Base URL: {settings.openai_base_url}")
        print(f"✅ API Key: {settings.openai_api_key[:10]}..." if settings.openai_api_key else "❌ 未设置 API Key")
    elif settings.ai_provider == "anthropic":
        print(f"✅ AI 模型: {settings.anthropic_model}")
        print(f"✅ API Key: {settings.anthropic_api_key[:10]}..." if settings.anthropic_api_key else "❌ 未设置 API Key")
    print(f"✅ 上传目录: {settings.upload_dir}")
    print(f"✅ 数据库: {settings.database_url}")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info",
    )

