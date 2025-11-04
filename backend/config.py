"""
配置文件
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """应用配置"""
    
    # API配置
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # 数据库
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/analysis.db",
        alias="DATABASE_URL"
    )
    
    # 文件上传
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_file_size: int = Field(default=104857600, alias="MAX_FILE_SIZE")  # 100MB
    
    # Jupyter配置
    jupyter_timeout: int = Field(default=300, alias="JUPYTER_TIMEOUT")
    kernel_startup_timeout: int = Field(default=30, alias="KERNEL_STARTUP_TIMEOUT")
    
    # AI模型配置
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL"
    )
    
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        alias="ANTHROPIC_MODEL"
    )
    
    ai_provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        alias="AI_PROVIDER"
    )
    
    # Agent模式配置
    agent_mode: Literal["classic", "smart"] = Field(
        default="smart",  # 默认使用智能模式
        alias="AGENT_MODE"
    )
    
    # 代码执行安全
    enable_code_sandbox: bool = Field(default=False, alias="ENABLE_CODE_SANDBOX")
    docker_image: str = Field(default="python:3.11-slim", alias="DOCKER_IMAGE")
    
    # 飞书配置 ⭐ 新增
    feishu_app_id: str = Field(default="", alias="FEISHU_APP_ID")
    feishu_app_secret: str = Field(default="", alias="FEISHU_APP_SECRET")
    feishu_host: str = Field(default="https://open.feishu.cn", alias="FEISHU_HOST")
    
    # Session 配置 ⭐ 新增
    session_secret_key: str = Field(default="your-secret-key-change-this", alias="SESSION_SECRET_KEY")
    session_max_age: int = Field(default=86400, alias="SESSION_MAX_AGE")  # 24小时
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()

