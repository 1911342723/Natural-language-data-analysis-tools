"""
Jupyter 代码执行 API
用于直接执行代码（例如重新生成图表）
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging

from core.jupyter_manager import jupyter_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ExecuteRequest(BaseModel):
    """执行代码请求"""
    session_id: str
    code: str


@router.post("/jupyter/execute")
async def execute_code(request: ExecuteRequest):
    """
    直接执行代码
    
    用于重新生成图表等场景
    """
    try:
        logger.info(f"收到代码执行请求: session={request.session_id}")
        
        # 获取 session
        session = jupyter_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session 不存在")
        
        # 执行代码
        result = await session.execute_code(request.code, timeout=120)
        
        logger.info(f"📋 执行结果: stdout={len(result.get('stdout', []))}行, "
                   f"data={len(result.get('data', []))}项, error={bool(result.get('error'))}")
        
        # 提取结果
        output_result = {
            'charts': [],
            'data': [],
            'text': []
        }
        
        # 提取 stdout
        if result.get('stdout'):
            full_text = ''.join(result['stdout'])
            if full_text.strip():
                output_result['text'].append(full_text)
                logger.info(f"✅ 提取了文本输出 ({len(full_text)} 字符)")
        
        # 提取图表和表格
        if result.get('data'):
            for data_item in result['data']:
                data_content = data_item['data']
                
                # 处理 HTML 表格
                if 'text/html' in data_content:
                    output_result['data'].append({
                        'type': 'html',
                        'content': data_content['text/html']
                    })
                    logger.info(f"✅ 提取了HTML表格")
                
                # 处理图片
                if 'image/png' in data_content:
                    output_result['charts'].append({
                        'type': 'image',
                        'format': 'png',
                        'data': data_content['image/png']
                    })
                    logger.info(f"✅ 提取了PNG图表")
        
        logger.info(f"📊 最终输出: {len(output_result['charts'])}个图表, "
                   f"{len(output_result['data'])}个表格, {len(output_result['text'])}条文本")
        
        # 检查是否有错误
        if result.get('error'):
            error_info = result['error']
            error_type = error_info.get('ename', 'Error')
            error_value = error_info.get('evalue', '未知错误')
            error_traceback = error_info.get('traceback', [])
            
            # 构建友好的错误信息
            error_msg = f"{error_type}: {error_value}"
            
            # 如果有堆栈信息，提取最关键的一行
            if error_traceback:
                # 通常最后一行包含最有用的信息
                for line in reversed(error_traceback):
                    if '-->' in line or 'line' in line.lower():
                        error_msg = f"{error_type}: {error_value}"
                        break
            
            return JSONResponse({
                "success": False,
                "message": "代码执行失败",
                "error": error_msg,
                "error_detail": {
                    "type": error_type,
                    "value": error_value,
                    "traceback": error_traceback[-3:] if len(error_traceback) > 3 else error_traceback
                },
                "data": None
            })
        
        return JSONResponse({
            "success": True,
            "message": "代码执行成功",
            "data": {
                "result": output_result
            }
        })
    
    except Exception as e:
        logger.error(f"代码执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

