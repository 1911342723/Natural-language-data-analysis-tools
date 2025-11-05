"""
工作流API - 科学家团队协作
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from multi_agent import MessageBroker
from multi_agent.base_agent import AgentMessage, MessageType
from smart_agent_team import SmartScientistTeam  # 使用新的智能团队
from smart_agent_team.decision_manager import decision_manager  # 决策管理器
from core.jupyter_manager import jupyter_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])

# 全局MessageBroker实例
message_broker = MessageBroker()

# 用户决策等待队列
user_decision_queues: Dict[str, asyncio.Queue] = {}


class StartResearchRequest(BaseModel):
    """启动研究请求"""
    session_id: str
    user_input: str
    data_info: Optional[Dict[str, Any]] = None


class UserDecisionResponse(BaseModel):
    """用户决策响应"""
    decision_id: str
    choice: str
    feedback: Optional[str] = None


# 别名，保持兼容性
SubmitUserDecisionRequest = UserDecisionResponse


@router.post("/start_research")
async def start_research(request: StartResearchRequest):
    """
    启动科学家团队研究 - 使用LangChain实现，支持真正的流式输出
    """
    try:
        logger.info(f"🚀 收到研究请求: {request.user_input}")
        
        # 创建科学家团队
        # 传入message_broker的broadcast函数作为回调
        async def broadcast_callback(data):
            await message_broker.broadcast_to_frontend(data)
        
        team = SmartScientistTeam(message_callback=broadcast_callback)
        
        logger.info(f"✅ 智能科研团队已就绪")
        
        # 在后台执行研究
        task_id = f"research_{asyncio.get_event_loop().time()}"
        asyncio.create_task(_execute_smart_research(
            team,
            request.user_input,
            request.data_info,
            task_id
        ))
        
        return {
            "success": True,
            "message": "智能科研团队已启动",
            "data": {
                "task_id": task_id,
                "status": "running",
                "framework": "SmartAgentTeam (LangChain + Tools)"
            }
        }
        
    except Exception as e:
        logger.error(f"启动研究失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_smart_research(
    team: SmartScientistTeam,
    user_input: str,
    data_info: Optional[Dict[str, Any]],
    task_id: str
):
    """使用智能团队执行研究任务 - 支持工具调用和动态决策"""
    try:
        logger.info(f"🚀 智能科研团队开始执行研究: {task_id}")
        logger.info(f"📋 研究课题: {user_input}")
        
        # 执行研究（PI会自主决策、调用工具、咨询团队成员）
        result = await team.conduct_research(user_input, data_info)
        
        logger.info(f"✅ 研究完成: {task_id}")
        
        # 广播完成消息
        await message_broker.broadcast_to_frontend({
            "type": "research_completed",
            "data": {
                "task_id": task_id,
                "result": result,
                "framework": "SmartAgentTeam"
            }
        })
        
    except Exception as e:
        logger.error(f"研究失败: {e}", exc_info=True)
        
        # 广播错误消息
        await message_broker.broadcast_to_frontend({
            "type": "research_failed",
            "data": {
                "task_id": task_id,
                "error": str(e)
            }
        })


async def _handle_user_decision_request(
    decision_request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    处理用户决策请求
    
    这个函数会被PI Agent调用，当需要用户决策时
    它会通过WebSocket发送请求到前端，然后等待用户响应
    """
    decision_id = f"decision_{asyncio.get_event_loop().time()}"
    decision_request["decision_id"] = decision_id
    
    # 创建等待队列
    decision_queue = asyncio.Queue()
    user_decision_queues[decision_id] = decision_queue
    
    # 发送决策请求到前端
    await message_broker.broadcast_to_frontend({
        "type": "user_decision_required",
        "data": decision_request
    })
    
    logger.info(f"等待用户决策: {decision_id}")
    
    # 等待用户响应（带超时）
    try:
        timeout = decision_request.get("timeout", 300)  # 默认5分钟
        decision = await asyncio.wait_for(
            decision_queue.get(),
            timeout=timeout
        )
        logger.info(f"收到用户决策: {decision}")
        return decision
        
    except asyncio.TimeoutError:
        logger.warning(f"用户决策超时: {decision_id}")
        return {
            "choice": "timeout",
            "feedback": "用户未在规定时间内响应"
        }
    finally:
        # 清理队列
        if decision_id in user_decision_queues:
            del user_decision_queues[decision_id]


@router.post("/user_decision")
async def submit_user_decision(request: SubmitUserDecisionRequest):
    """
    提交用户决策（使用新的DecisionManager）
    
    前端调用此接口来响应决策请求
    """
    try:
        decision_id = request.decision_id
        choice = request.choice
        feedback = request.feedback
        
        logger.info(f"📝 收到用户决策: {decision_id} -> {choice}")
        
        # 使用DecisionManager处理决策
        success = decision_manager.submit_user_decision(
            decision_id=decision_id,
            choice=choice,
            feedback=feedback
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="决策请求不存在或已过期")
        
        # 广播用户决策到前端
        await message_broker.broadcast_to_frontend({
            "type": "user_decision_submitted",
            "data": {
                "decision_id": decision_id,
                "choice": choice,
                "feedback": feedback
            }
        })
        
        return {
            "success": True,
            "message": "决策已提交并处理"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交决策失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending_decisions")
async def get_pending_decisions():
    """
    获取所有待决策的请求
    """
    try:
        pending = decision_manager.get_pending_decisions()
        return {
            "success": True,
            "data": pending
        }
    except Exception as e:
        logger.error(f"获取待决策请求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket连接 - 用于实时推送Agent状态和消息
    """
    await websocket.accept()
    message_broker.add_websocket_connection(websocket)
    
    logger.info("WebSocket连接已建立")
    
    try:
        while True:
            # 保持连接，接收客户端消息（如果有）
            data = await websocket.receive_text()
            logger.debug(f"收到WebSocket消息: {data}")
            
            # 可以处理客户端发来的消息
            # ...
            
    except WebSocketDisconnect:
        logger.info("WebSocket连接已断开")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}", exc_info=True)
    finally:
        message_broker.remove_websocket_connection(websocket)


@router.get("/agents")
async def get_agents():
    """获取所有Agent信息"""
    try:
        agents = message_broker.get_all_agents()
        return {
            "success": True,
            "data": {
                "agents": [agent.get_info() for agent in agents]
            }
        }
    except Exception as e:
        logger.error(f"获取Agent列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages")
async def get_messages(agent_id: Optional[str] = None, limit: int = 100):
    """获取消息历史"""
    try:
        messages = message_broker.get_message_history(agent_id, limit)
        return {
            "success": True,
            "data": {
                "messages": messages
            }
        }
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """获取系统统计信息"""
    try:
        stats = message_broker.get_statistics()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

