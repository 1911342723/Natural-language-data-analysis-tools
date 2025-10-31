"""
数据库模型和操作
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Text, DateTime, JSON
from datetime import datetime
from typing import Optional
from config import settings


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """基础模型类"""
    pass


class AnalysisHistory(Base):
    """分析历史记录"""
    __tablename__ = "analysis_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # 文件信息
    file_id: Mapped[str] = mapped_column(String(50), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)
    
    # 分析信息
    session_id: Mapped[str] = mapped_column(String(50), index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    user_request: Mapped[str] = mapped_column(Text)
    selected_columns: Mapped[str] = mapped_column(JSON)  # JSON格式存储字段列表
    
    # 执行结果
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    steps: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # Agent执行步骤
    result: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # 分析结果
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "user_request": self.user_request,
            "selected_columns": self.selected_columns,
            "success": self.success,
            "steps": self.steps,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        yield session


