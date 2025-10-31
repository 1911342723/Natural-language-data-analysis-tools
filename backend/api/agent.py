"""
Agent 分析 API
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, AsyncGenerator
import asyncio
import uuid
import json
import logging

from core.agent import AnalysisAgent
from core.file_handler import file_handler

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局任务存储（生产环境应使用 Redis）
tasks: Dict[str, Dict[str, Any]] = {}


class AnalyzeRequest(BaseModel):
    """分析请求"""
    session_id: str
    user_request: str
    selected_columns: List[str]


async def run_agent_task(
    task_id: str,
    session_id: str,
    user_request: str,
    selected_columns: List[str],
    data_schema: Dict
):
    """后台运行 Agent 任务"""
    try:
        logger.info(f"开始执行 Agent 任务: {task_id}")
        
        # 创建 Agent
        agent = AnalysisAgent(
            session_id=session_id,
            user_request=user_request,
            selected_columns=selected_columns,
            data_schema=data_schema
        )
        
        # 更新任务状态
        tasks[task_id]["agent"] = agent
        tasks[task_id]["status"] = "running"
        
        # 执行 Agent
        result = await agent.run()
        
        # 更新任务结果
        tasks[task_id]["status"] = result["status"]
        tasks[task_id]["result"] = result
        
        logger.info(f"Agent 任务完成: {task_id}, status={result['status']}")
    
    except Exception as e:
        logger.error(f"Agent 任务异常: {e}", exc_info=True)
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["result"] = {
            "status": "failed",
            "data": {
                "error": str(e)
            }
        }


@router.post("/agent/analyze")
async def submit_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks
):
    """
    提交分析请求
    
    请求：
    {
        "session_id": "xxx",
        "user_request": "计算销售额平均值",
        "selected_columns": ["销售额", "地区"]
    }
    
    返回：
    {
        "success": true,
        "message": "任务已提交",
        "data": {
            "task_id": "xxx"
        }
    }
    """
    try:
        # 生成任务 ID
        task_id = str(uuid.uuid4())
        
        logger.info(f"接收分析请求: task_id={task_id}, session={request.session_id}")
        
        # 从缓存中获取 Session 信息
        from core.cache import session_cache, file_cache
        
        session_info = session_cache.get(request.session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session 不存在，请重新创建")
        
        # 从缓存中获取文件信息
        file_info = file_cache.get(session_info['file_id'])
        if not file_info:
            raise HTTPException(status_code=404, detail="文件信息不存在，请重新上传")
        
        # 从 session 中获取工作表名称
        sheet_name = session_info.get('sheet_name')
        if not sheet_name:
            raise HTTPException(status_code=400, detail="Session 中没有工作表信息")
        
        # 找到对应的工作表
        target_sheet = None
        for sheet in file_info['sheets']:
            if sheet['sheet_name'] == sheet_name:
                target_sheet = sheet
                break
        
        if not target_sheet:
            raise HTTPException(status_code=404, detail=f"工作表 '{sheet_name}' 不存在")
        
        # 构建 data_schema（使用工作表的信息）
        data_schema = {
            "sheet_name": sheet_name,
            "total_rows": target_sheet['total_rows'],
            "total_columns": target_sheet['total_columns'],
            "columns": {col['name']: col for col in target_sheet['columns']}
        }
        
        logger.info(f"✅ 从缓存获取数据信息成功: 工作表={sheet_name}, 行数={target_sheet['total_rows']}")
        
        # 初始化任务
        tasks[task_id] = {
            "task_id": task_id,
            "session_id": request.session_id,
            "status": "pending",
            "agent": None,
            "result": None
        }
        
        # 后台执行 Agent
        background_tasks.add_task(
            run_agent_task,
            task_id,
            request.session_id,
            request.user_request,
            request.selected_columns,
            data_schema
        )
        
        return JSONResponse({
            "success": True,
            "message": "任务已提交",
            "data": {
                "task_id": task_id
            }
        })
    
    except Exception as e:
        logger.error(f"提交分析请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/status/{task_id}")
async def get_agent_status(task_id: str):
    """
    获取 Agent 执行状态（轮询）
    
    返回：
    {
        "success": true,
        "status": "running",  # pending | running | completed | failed
        "data": {
            "steps": [...],
            "result": {...}
        }
    }
    """
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 获取最新状态
    agent = task.get("agent")
    if agent:
        state = agent.get_state()
        return JSONResponse({
            "success": True,
            "status": state["status"],
            "data": state["data"]
        })
    else:
        return JSONResponse({
            "success": True,
            "status": task["status"],
            "data": {
                "steps": [],
                "result": task.get("result")
            }
        })


@router.post("/agent/stop/{task_id}")
async def stop_agent(task_id: str):
    """停止 Agent 执行"""
    task = tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # TODO: 实现停止逻辑
    task["status"] = "cancelled"
    
    return JSONResponse({
        "success": True,
        "message": "任务已停止"
    })


@router.post("/agent/analyze-stream")
async def analyze_stream(request: AnalyzeRequest):
    """
    流式分析（SSE）- 实时推送 Agent 执行状态
    
    返回 SSE 流，客户端可实时接收：
    - 代码生成进度
    - 代码执行输出
    - 结果提取
    - AI 总结
    """
    try:
        logger.info(f"接收流式分析请求: session={request.session_id}")
        
        # 从缓存中获取 Session 信息
        from core.cache import session_cache, file_cache
        
        session_info = session_cache.get(request.session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="Session 不存在，请重新创建")
        
        # 判断是单文件还是多文件模式
        is_multi = session_info.get('is_multi', False)
        
        if is_multi:
            # 多文件模式：构建多表格的 data_schema
            logger.info(f"多文件模式分析: group_id={session_info.get('group_id')}")
            
            tables_info = []
            for table in session_info.get('tables', []):
                # 从缓存获取文件信息
                file_info = file_cache.get(table['file_id'])
                if file_info:
                    # 找到对应的工作表
                    for sheet in file_info['sheets']:
                        if sheet['sheet_name'] == table['sheet_name']:
                            # 从 table 中获取用户选择的字段
                            selected_columns = table.get('selected_columns', [])
                            
                            tables_info.append({
                                'alias': table['alias'],
                                'file_name': table['file_name'],
                                'sheet_name': table['sheet_name'],
                                'total_rows': sheet['total_rows'],
                                'total_columns': sheet['total_columns'],
                                'columns': sheet['columns'],
                                'selected_columns': selected_columns  # 添加用户选择的字段
                            })
                            
                            logger.info(f"  - 表格 {table['alias']}: {len(selected_columns)} 个选中字段")
                            break
            
            data_schema = {
                'is_multi': True,
                'tables': tables_info
            }
            logger.info(f"✅ 多表格 data_schema 构建完成: {len(tables_info)} 个表格")
        else:
            # 单文件模式：原有逻辑
            file_info = file_cache.get(session_info['file_id'])
            if not file_info:
                raise HTTPException(status_code=404, detail="文件信息不存在，请重新上传")
            
            # 从 session 中获取工作表名称
            sheet_name = session_info.get('sheet_name')
            if not sheet_name:
                raise HTTPException(status_code=400, detail="Session 中没有工作表信息")
            
            # 找到对应的工作表
            target_sheet = None
            for sheet in file_info['sheets']:
                if sheet['sheet_name'] == sheet_name:
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                raise HTTPException(status_code=404, detail=f"工作表 '{sheet_name}' 不存在")
            
            # 构建 data_schema
            data_schema = {
                "sheet_name": sheet_name,
                "total_rows": target_sheet['total_rows'],
                "total_columns": target_sheet['total_columns'],
                "columns": {col['name']: col for col in target_sheet['columns']}
            }
        
        # 生成任务 ID
        task_id = str(uuid.uuid4())
        logger.info(f"创建流式任务: {task_id}")
        
        # 创建流式响应
        def safe_json_dumps(data: dict) -> str:
            """安全的 JSON 序列化，处理特殊字符"""
            try:
                return json.dumps(data, ensure_ascii=False, default=str)
            except Exception as e:
                logger.error(f"JSON 序列化失败: {e}")
                # 尝试简化数据
                simplified = {
                    'event': data.get('event', 'error'),
                    'message': 'JSON 序列化失败，数据已简化'
                }
                return json.dumps(simplified, ensure_ascii=False)
        
        async def event_generator() -> AsyncGenerator[str, None]:
            """SSE 事件生成器"""
            try:
                # 发送任务开始事件
                start_event = safe_json_dumps({'event': 'start', 'task_id': task_id})
                yield f"data: {start_event}\n\n"
                
                # 创建 Agent
                agent = AnalysisAgent(
                    session_id=request.session_id,
                    user_request=request.user_request,
                    selected_columns=request.selected_columns,
                    data_schema=data_schema
                )
                
                # 监听 Agent 的步骤变化
                last_step_count = 0
                last_step_outputs = {}  # 记录每个步骤的最后输出，用于检测变化
                
                # 启动 Agent 任务
                agent_task = asyncio.create_task(agent.run())
                
                try:
                    # 轮询 Agent 状态并推送
                    while not agent_task.done():
                        state = agent.get_state()
                        current_steps = state['data']['steps']
                        current_step_count = len(current_steps)
                        
                        # 检查是否有新步骤或步骤内容变化
                        for i, step in enumerate(current_steps):
                            step_key = f"{i}"
                            current_output = step.get('output', '')
                            
                            # 新步骤或输出内容变化
                            if i >= last_step_count or last_step_outputs.get(step_key) != current_output:
                                # 限制输出长度，避免数据过大
                                step_copy = step.copy()
                                if step_copy.get('output') and len(step_copy['output']) > 10000:
                                    step_copy['output'] = step_copy['output'][:10000] + '\n... (输出过长，已截断)'
                                
                                # 限制代码长度
                                if step_copy.get('code') and len(step_copy['code']) > 50000:
                                    step_copy['code'] = step_copy['code'][:50000] + '\n# ... (代码过长，已截断)'
                                
                                # 调试输出
                                logger.info(f"📤 推送步骤更新 #{i}: {step.get('title')}, status={step.get('status')}, output_len={len(current_output)}")
                                
                                step_event = safe_json_dumps({'event': 'step', 'data': step_copy, 'step_index': i})
                                yield f"data: {step_event}\n\n"
                                
                                # 更新记录
                                last_step_outputs[step_key] = current_output
                        
                        last_step_count = current_step_count
                        await asyncio.sleep(0.03)  # 每30ms检查一次（更实时）
                
                except (asyncio.CancelledError, GeneratorExit) as e:
                    # 客户端断开连接或取消请求
                    logger.info(f"⚠️ 客户端断开连接，取消任务: {task_id}")
                    agent_task.cancel()
                    try:
                        await agent_task
                    except asyncio.CancelledError:
                        logger.info(f"✅ Agent 任务已成功取消: {task_id}")
                    raise  # 重新抛出异常，结束生成器
                
                # Agent 执行完成
                result = await agent_task
                
                # 限制结果数据大小
                if result.get('data', {}).get('result'):
                    result_data = result['data']['result']
                    # 限制文本输出
                    if 'text' in result_data and isinstance(result_data['text'], list):
                        result_data['text'] = [
                            t[:5000] + '...(已截断)' if len(t) > 5000 else t
                            for t in result_data['text']
                        ]
                
                # 推送完成事件
                complete_event = safe_json_dumps({'event': 'complete', 'data': result})
                yield f"data: {complete_event}\n\n"
                
                logger.info(f"流式任务完成: {task_id}")
                
            except Exception as e:
                logger.error(f"流式任务失败: {e}", exc_info=True)
                error_event = safe_json_dumps({'event': 'error', 'message': str(e)})
                yield f"data: {error_event}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"流式分析请求失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

