"""
FastAPI 应用主入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware  # 新增
from contextlib import asynccontextmanager
import os
import secrets  # 新增

from config import settings
from api import router
from core.database import init_db
from core.feishu_db import db as feishu_db  # 新增


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 创建必要的目录
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    
    # 初始化数据库
    await init_db()
    
    # 初始化飞书数据库 ⭐ 新增
    feishu_db.init_database()
    print("✓ 飞书数据库初始化完成")
    
    yield


# 创建FastAPI应用
app = FastAPI(
    title="智能数据分析工具 API",
    description="基于 Jupyter Kernel 的智能数据分析后端",
    version="1.0.0",
    lifespan=lifespan,
)

# Session 中间件 ⭐ 新增（必须在 CORS 之前）
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key or secrets.token_hex(32),
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=False,
)

# CORS中间件
# ⚠️ 重要：allow_origins 不能设置为 ["*"] 当 allow_credentials=True 时
# 必须明确指定允许的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://0a431d28c27a.ngrok-free.app",  # ngrok 域名
    ],
    allow_credentials=True,  # 允许携带 cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(router, prefix="/api")

# 健康检查接口（API）
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}

# 配置静态文件服务（前端构建产物）
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    # 静态资源（CSS, JS, 图片等）
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # SPA 路由：所有非 API 路由都返回 index.html（让 React Router 处理）
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """提供 SPA 应用（所有路由都返回 index.html）"""
        # API 路由已经被 /api 前缀处理，这里不会匹配到
        # 其他所有路由都返回 index.html
        index_path = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Frontend not built. Run 'npm run build' in frontend directory."}
else:
    @app.get("/")
    async def root():
        """根路由（开发模式）"""
        return {
            "message": "智能数据分析工具 API",
            "version": "1.0.0",
            "status": "running",
            "note": "Frontend not built. Run 'npm run build' in frontend directory, or use Vite dev server on port 3000."
        }


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

