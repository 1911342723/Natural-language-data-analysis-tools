"""
Session 管理 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging

from core.jupyter_manager import jupyter_manager
from core.cache import file_cache, session_cache

logger = logging.getLogger(__name__)

router = APIRouter()


class TableSource(BaseModel):
    """表格数据源"""
    file_id: str
    sheet_name: str
    alias: str  # 在 Jupyter 中的变量名，如 df1, df2
    selected_columns: Optional[List[str]] = []  # 用户选择的字段


class CreateSessionRequest(BaseModel):
    """创建 Session 请求（单文件模式，向后兼容）"""
    file_id: str
    sheet_name: str  # 选择的工作表名称
    selected_columns: List[str]


class CreateMultiSessionRequest(BaseModel):
    """创建多文件 Session 请求"""
    group_id: str
    tables: List[TableSource]  # 要加载的表格列表
    selected_columns: Optional[List[str]] = []  # 可选，多文件分析可能不需要


@router.post("/session/create")
async def create_session(request: CreateSessionRequest):
    """
    创建 Jupyter Session
    
    流程：
    1. 从内存缓存获取文件信息（包含 data_json）
    2. 创建 Jupyter Kernel Session
    3. 将 Session 信息缓存到内存
    
    请求：
    {
        "file_id": "xxx",
        "sheet_name": "Sheet1",
        "selected_columns": ["col1", "col2"]
    }
    
    返回：
    {
        "success": true,
        "message": "Session 创建成功",
        "data": {
            "session_id": "xxx"
        }
    }
    """
    try:
        logger.info(f"创建 Session: file_id={request.file_id}, sheet={request.sheet_name}, columns={request.selected_columns}")
        
        # 1. 从缓存获取文件信息
        file_info = file_cache.get(request.file_id)
        
        if not file_info:
            logger.error(f"文件信息未找到: {request.file_id}")
            raise HTTPException(
                status_code=404,
                detail=f"文件信息未找到，请重新上传文件"
            )
        
        # 2. 找到指定的工作表
        target_sheet = None
        for sheet in file_info['sheets']:
            if sheet['sheet_name'] == request.sheet_name:
                target_sheet = sheet
                break
        
        if not target_sheet:
            logger.error(f"工作表未找到: {request.sheet_name}")
            raise HTTPException(
                status_code=404,
                detail=f"工作表 '{request.sheet_name}' 未找到"
            )
        
        data_json = target_sheet['data_json']
        logger.info(f"✅ 从缓存获取工作表 '{request.sheet_name}' 数据成功")
        
        # 2. 创建 Jupyter Session
        session_id = await jupyter_manager.create_session(data_json)
        logger.info(f"✅ Jupyter Session 创建成功: {session_id}")
        
        # 3. 缓存 Session 信息
        session_info = {
            "session_id": session_id,
            "file_id": request.file_id,
            "file_name": file_info['file_name'],
            "sheet_name": request.sheet_name,
            "selected_columns": request.selected_columns,
            "created_at": datetime.now()
        }
        session_cache.set(session_id, session_info)
        logger.info(f"✅ Session 信息已缓存")
        
        return JSONResponse({
            "success": True,
            "message": "Session 创建成功",
            "data": {
                "session_id": session_id
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session 创建失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session 创建失败: {str(e)}")


@router.post("/session/create-multi")
async def create_multi_session(request: CreateMultiSessionRequest):
    """
    创建多文件 Jupyter Session（用于跨表格一致性分析）
    
    流程：
    1. 从内存缓存获取文件组信息
    2. 为每个表格获取 data_json
    3. 创建 Jupyter Kernel Session，加载多个 DataFrame (df1, df2, ...)
    4. 将 Session 信息缓存到内存
    
    请求：
    {
        "group_id": "xxx",
        "tables": [
            {"file_id": "file1", "sheet_name": "Sheet1", "alias": "df1", "selected_columns": []},
            {"file_id": "file2", "sheet_name": "Sheet1", "alias": "df2", "selected_columns": []}
        ],
        "selected_columns": []
    }
    
    返回：
    {
        "success": true,
        "message": "多文件 Session 创建成功",
        "data": {
            "session_id": "xxx",
            "loaded_tables": ["df1", "df2"]
        }
    }
    """
    try:
        logger.info(f"🔵 收到创建多文件 Session 请求")
        logger.info(f"  group_id: {request.group_id}")
        logger.info(f"  tables 数量: {len(request.tables)}")
        for i, table in enumerate(request.tables):
            logger.info(f"  table[{i}]: file_id={table.file_id}, sheet={table.sheet_name}, alias={table.alias}, selected_columns={table.selected_columns}")
        
        logger.info(f"创建多文件 Session: group_id={request.group_id}, tables={len(request.tables)}")
        
        # 1. 从缓存获取文件组信息
        file_group = file_cache.get(f"group_{request.group_id}")
        
        if not file_group:
            logger.error(f"文件组未找到: {request.group_id}")
            raise HTTPException(
                status_code=404,
                detail=f"文件组未找到，请重新上传文件"
            )
        
        # 2. 收集所有表格的 data_json
        tables_data = []
        for table_req in request.tables:
            # 找到对应的文件
            target_file = None
            for file_info in file_group['files']:
                if file_info['file_id'] == table_req.file_id:
                    target_file = file_info
                    break
            
            if not target_file:
                raise HTTPException(
                    status_code=404,
                    detail=f"文件 '{table_req.file_id}' 未找到"
                )
            
            # 找到对应的工作表
            target_sheet = None
            for sheet in target_file['sheets']:
                if sheet['sheet_name'] == table_req.sheet_name:
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                raise HTTPException(
                    status_code=404,
                    detail=f"工作表 '{table_req.sheet_name}' 未找到（文件: {target_file['file_name']}）"
                )
            
            tables_data.append({
                'alias': table_req.alias,
                'data_json': target_sheet['data_json'],
                'file_name': target_file['file_name'],
                'sheet_name': target_sheet['sheet_name'],
                'file_id': table_req.file_id,
                'selected_columns': table_req.selected_columns  # 添加用户选择的字段
            })
            
            logger.info(f"  ✅ 表格 '{table_req.alias}': {target_file['file_name']} / {target_sheet['sheet_name']} (选中字段: {len(table_req.selected_columns)})")
        
        # 3. 创建多表格 Jupyter Session
        session_id = await jupyter_manager.create_multi_session(tables_data)
        logger.info(f"✅ 多文件 Jupyter Session 创建成功: {session_id}")
        
        # 4. 缓存 Session 信息
        session_info = {
            "session_id": session_id,
            "group_id": request.group_id,
            "tables": tables_data,
            "selected_columns": request.selected_columns,
            "is_multi": True,  # 标记为多文件模式
            "created_at": datetime.now()
        }
        session_cache.set(session_id, session_info)
        logger.info(f"✅ 多文件 Session 信息已缓存")
        
        return JSONResponse({
            "success": True,
            "message": f"多文件 Session 创建成功",
            "data": {
                "session_id": session_id,
                "loaded_tables": [t['alias'] for t in tables_data]
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多文件 Session 创建失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"多文件 Session 创建失败: {str(e)}")


class ExecuteCodeRequest(BaseModel):
    """执行代码请求"""
    session_id: str
    code: str
    timeout: int = 60


@router.post("/session/execute")
async def execute_code(request: ExecuteCodeRequest):
    """
    在指定 Session 中执行代码
    
    请求：
    {
        "session_id": "xxx",
        "code": "print('hello')",
        "timeout": 60
    }
    
    返回：
    {
        "success": true,
        "data": {
            "stdout": ["hello\\n"],
            "stderr": [],
            "data": [],
            "error": null,
            "execution_count": 1
        }
    }
    """
    try:
        logger.info(f"执行代码: session_id={request.session_id}, code_length={len(request.code)}")
        
        # 获取 Session
        session_info = session_cache.get(request.session_id)
        if not session_info:
            raise HTTPException(
                status_code=404,
                detail="Session 不存在，请重新创建"
            )
        
        # 获取 Jupyter Session
        jupyter_session = jupyter_manager.get_session(request.session_id)
        if not jupyter_session:
            raise HTTPException(
                status_code=404,
                detail="Jupyter Session 不存在"
            )
        
        # 执行代码
        result = await jupyter_session.execute_code(request.code, timeout=request.timeout)
        logger.info(f"✅ 代码执行完成")
        
        return JSONResponse({
            "success": True,
            "data": result
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代码执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"代码执行失败: {str(e)}")


@router.delete("/session/{session_id}")
async def close_session(session_id: str):
    """关闭 Session"""
    try:
        # 关闭 Jupyter Kernel
        await jupyter_manager.close_session(session_id)
        logger.info(f"✅ Jupyter Session 已关闭: {session_id}")
        
        # 删除缓存信息
        session_cache.delete(session_id)
        logger.info(f"✅ Session 缓存已清理")
        
        return JSONResponse({
            "success": True,
            "message": "Session 已关闭"
        })
    
    except Exception as e:
        logger.error(f"Session 关闭失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

