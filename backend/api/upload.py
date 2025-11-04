"""
文件上传 API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from typing import List
import uuid

from core.file_handler import file_handler
from core.cache import file_cache
from core.feishu_auth import get_current_user  # ⭐ 新增：登录验证
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)  # ⭐ 需要登录
):
    """
    上传文件并解析
    
    文件处理流程：
    1. 验证文件类型和大小
    2. 保存文件到本地目录 (./uploads)
    3. 解析文件获取元信息
    4. 将元信息缓存到内存（包含 data_json）
    5. 返回前端需要的信息（不含 data_json）
    
    返回：
    {
        "success": true,
        "message": "文件上传成功",
        "data": {
            "file_id": "xxx",
            "file_name": "data.csv",
            "file_size": 12345,
            "sheets": [
                {
                    "sheet_name": "Sheet1",
                    "total_rows": 1000,
                    "total_columns": 10,
                    "columns": [...],
                    "preview": [...]
                }
            ]
        }
    }
    """
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名无效")
        
        file_ext = file.filename.split('.')[-1].lower()
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=400,
                detail="只支持 CSV 和 Excel 文件"
            )
        
        # 读取文件内容
        content = await file.read()
        
        # 验证文件大小
        if len(content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大 {settings.max_file_size / 1024 / 1024}MB）"
            )
        
        logger.info(f"接收到文件上传: {file.filename}, 大小: {len(content)} 字节")
        
        # 1. 保存文件到本地目录
        file_id = await file_handler.save_uploaded_file(content, file.filename)
        logger.info(f"✅ 文件已保存到本地: ./uploads/{file_id}")
        
        # 2. 解析文件（支持多工作表）
        file_info = file_handler.parse_file(file_id, file.filename)
        total_sheets = len(file_info['sheets'])
        logger.info(f"✅ 文件解析完成: 共 {total_sheets} 个工作表")
        
        # 3. 将完整信息（包含每个 sheet 的 data_json）缓存到内存
        file_cache.set(file_id, file_info)
        logger.info(f"✅ 文件信息已缓存到内存")
        
        # 4. 返回前端需要的信息（移除每个 sheet 的 data_json，减少传输量）
        response_data = {
            'file_id': file_info['file_id'],
            'file_name': file_info['file_name'],
            'file_size': file_info['file_size'],
            'sheets': [
                {k: v for k, v in sheet.items() if k != 'data_json'}
                for sheet in file_info['sheets']
            ]
        }
        
        return JSONResponse({
            "success": True,
            "message": "文件上传成功",
            "data": response_data
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    上传多个文件并解析（用于跨表格一致性分析）
    
    文件处理流程：
    1. 验证每个文件的类型和大小
    2. 保存所有文件到本地目录
    3. 解析所有文件获取元信息
    4. 创建文件组（File Group），生成 group_id
    5. 将文件组信息缓存到内存
    6. 返回文件组信息
    
    返回：
    {
        "success": true,
        "message": "成功上传 N 个文件",
        "data": {
            "group_id": "xxx",
            "files": [
                {
                    "file_id": "xxx",
                    "file_name": "data1.csv",
                    "file_size": 12345,
                    "sheets": [...]
                },
                {
                    "file_id": "yyy",
                    "file_name": "data2.xlsx",
                    "file_size": 23456,
                    "sheets": [...]
                }
            ]
        }
    }
    """
    try:
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="请至少上传一个文件")
        
        if len(files) > 10:  # 限制最多10个文件
            raise HTTPException(status_code=400, detail="最多支持同时上传10个文件")
        
        logger.info(f"接收到多文件上传请求: {len(files)} 个文件")
        
        # 生成文件组 ID
        group_id = str(uuid.uuid4())
        uploaded_files = []
        
        # 处理每个文件
        for idx, file in enumerate(files):
            try:
                # 验证文件名
                if not file.filename:
                    raise HTTPException(status_code=400, detail=f"第 {idx + 1} 个文件名无效")
                
                file_ext = file.filename.split('.')[-1].lower()
                if file_ext not in ['csv', 'xlsx', 'xls']:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件 '{file.filename}' 格式不支持，只支持 CSV 和 Excel 文件"
                    )
                
                # 读取文件内容
                content = await file.read()
                
                # 验证文件大小
                if len(content) > settings.max_file_size:
                    raise HTTPException(
                        status_code=400,
                        detail=f"文件 '{file.filename}' 大小超过限制（最大 {settings.max_file_size / 1024 / 1024}MB）"
                    )
                
                logger.info(f"  [{idx + 1}/{len(files)}] 处理文件: {file.filename}, 大小: {len(content)} 字节")
                
                # 保存文件
                file_id = await file_handler.save_uploaded_file(content, file.filename)
                logger.info(f"    ✅ 文件已保存: ./uploads/{file_id}")
                
                # 解析文件
                file_info = file_handler.parse_file(file_id, file.filename)
                total_sheets = len(file_info['sheets'])
                logger.info(f"    ✅ 文件解析完成: {total_sheets} 个工作表")
                
                # 缓存单个文件信息（保持单文件上传兼容性）
                file_cache.set(file_id, file_info)
                
                # 添加到文件组
                uploaded_files.append(file_info)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"处理文件 '{file.filename}' 失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"处理文件 '{file.filename}' 失败: {str(e)}")
        
        # 创建文件组
        file_group = {
            'group_id': group_id,
            'files': uploaded_files
        }
        
        # 缓存文件组（使用特殊前缀 "group_" 区分）
        file_cache.set(f"group_{group_id}", file_group)
        logger.info(f"✅ 文件组已创建并缓存: group_id={group_id}, 文件数={len(uploaded_files)}")
        
        # 返回响应（移除 data_json 减少传输量）
        response_data = {
            'group_id': group_id,
            'files': [
                {
                    'file_id': f['file_id'],
                    'file_name': f['file_name'],
                    'file_size': f['file_size'],
                    'sheets': [
                        {k: v for k, v in sheet.items() if k != 'data_json'}
                        for sheet in f['sheets']
                    ]
                }
                for f in uploaded_files
            ]
        }
        
        return JSONResponse({
            "success": True,
            "message": f"成功上传 {len(files)} 个文件",
            "data": response_data
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多文件上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"多文件上传失败: {str(e)}")

