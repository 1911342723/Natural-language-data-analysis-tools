"""
历史记录 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional
import logging

from core.database import get_db, AnalysisHistory
from core.feishu_auth import get_current_user
from core.feishu_db import db as feishu_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history/list")
async def get_history_list(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user)
):
    """
    获取当前用户的历史记录列表（从飞书数据库）
    
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
        user_id = user["open_id"]
        
        # 从飞书数据库获取用户历史记录（异步）
        history_list = await feishu_db.get_user_analysis_history_async(
            user_id=user_id,
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        # 获取总数（异步）
        total = await feishu_db.get_user_analysis_count_async(user_id)
        
        return JSONResponse({
            "success": True,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": history_list
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
    user: dict = Depends(get_current_user)
):
    """删除历史记录（仅删除当前用户的记录）"""
    try:
        user_id = user["open_id"]
        
        # 从飞书数据库删除记录（异步，会验证是否属于当前用户）
        success = await feishu_db.delete_analysis_record_async(history_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="记录不存在或无权删除")
        
        return JSONResponse({
            "success": True,
            "message": "删除成功"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


