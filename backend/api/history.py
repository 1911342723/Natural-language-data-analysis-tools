"""
历史记录 API
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional
import logging

from core.database import get_db, AnalysisHistory

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history/list")
async def get_history_list(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    获取历史记录列表
    
    参数：
    - page: 页码（从1开始）
    - page_size: 每页数量
    
    返回：
    {
        "success": true,
        "data": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "items": [...]
        }
    }
    """
    try:
        # 查询总数
        count_query = select(AnalysisHistory)
        result = await db.execute(count_query)
        total = len(result.scalars().all())
        
        # 分页查询
        offset = (page - 1) * page_size
        query = (
            select(AnalysisHistory)
            .order_by(AnalysisHistory.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return JSONResponse({
            "success": True,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [item.to_dict() for item in items]
            }
        })
    
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{history_id}")
async def get_history_detail(
    history_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取历史记录详情"""
    try:
        query = select(AnalysisHistory).where(AnalysisHistory.id == history_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        return JSONResponse({
            "success": True,
            "data": item.to_dict()
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史记录详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{history_id}")
async def delete_history_record(
    history_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除历史记录"""
    try:
        query = delete(AnalysisHistory).where(AnalysisHistory.id == history_id)
        await db.execute(query)
        await db.commit()
        
        return JSONResponse({
            "success": True,
            "message": "删除成功"
        })
    
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


