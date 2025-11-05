"""
Agent基类 - 所有科学家Agent的基础
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    TASK_ASSIGNMENT = "task_assignment"      # 任务分配
    TASK_RESULT = "task_result"              # 任务结果
    QUERY = "query"                          # 查询/请求
    RESPONSE = "response"                    # 响应
    STATUS_UPDATE = "status_update"          # 状态更新
    USER_DECISION_REQUEST = "user_decision_request"  # 请求用户决策
    USER_DECISION_RESPONSE = "user_decision_response"  # 用户决策响应
    ERROR = "error"                          # 错误


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"              # 空闲
    THINKING = "thinking"      # 思考中
    WORKING = "working"        # 工作中
    WAITING = "waiting"        # 等待中（等待其他Agent或用户）
    COMPLETED = "completed"    # 已完成
    ERROR = "error"            # 错误


@dataclass
class AgentMessage:
    """Agent间消息结构"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: str
    priority: str = "normal"  # low, normal, high, urgent
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['message_type'] = self.message_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """从字典创建"""
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)


class BaseAgent(ABC):
    """
    Agent基类
    
    所有科学家Agent都继承此基类，提供：
    - 消息收发能力
    - 状态管理
    - 任务执行框架
    - 与用户交互能力
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        agent_type: str,
        ai_model: str = "gpt-4o-mini",
        system_prompt: str = "",
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.ai_model = ai_model
        self.system_prompt = system_prompt
        
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Dict[str, Any]] = None
        self.task_history: List[Dict[str, Any]] = []
        
        # 消息代理（由外部注入）
        self.message_broker: Optional[Any] = None
        
        # 用户交互回调（由外部注入）
        self.user_interaction_callback: Optional[Callable] = None
        
        # 内部消息队列
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None
        
        logger.info(f"[{self.agent_name}] Agent初始化完成")
    
    def set_message_broker(self, broker: Any):
        """设置消息代理"""
        self.message_broker = broker
    
    def set_user_interaction_callback(self, callback: Callable):
        """设置用户交互回调"""
        self.user_interaction_callback = callback
    
    async def start(self):
        """启动Agent，开始监听消息"""
        if self._running:
            logger.warning(f"[{self.agent_name}] Agent已在运行")
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._message_loop())
        logger.info(f"[{self.agent_name}] Agent已启动")
    
    async def stop(self):
        """停止Agent"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        logger.info(f"[{self.agent_name}] Agent已停止")
    
    async def _message_loop(self):
        """消息处理循环"""
        logger.info(f"[{self.agent_name}] 开始消息循环")
        
        while self._running:
            try:
                # 从消息队列获取消息（超时1秒，避免阻塞）
                try:
                    message = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                logger.info(
                    f"[{self.agent_name}] 收到消息: "
                    f"{message.message_type.value} from {message.from_agent}"
                )
                
                # 处理消息
                await self._handle_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_name}] 消息处理错误: {e}", exc_info=True)
    
    async def _handle_message(self, message: AgentMessage):
        """处理收到的消息"""
        try:
            if message.message_type == MessageType.TASK_ASSIGNMENT:
                await self._handle_task_assignment(message)
            elif message.message_type == MessageType.QUERY:
                await self._handle_query(message)
            elif message.message_type == MessageType.USER_DECISION_RESPONSE:
                await self._handle_user_decision_response(message)
            else:
                logger.warning(
                    f"[{self.agent_name}] 未处理的消息类型: {message.message_type}"
                )
        except Exception as e:
            logger.error(f"[{self.agent_name}] 处理消息失败: {e}", exc_info=True)
            # 发送错误消息给发送者
            await self.send_message(
                to_agent=message.from_agent,
                message_type=MessageType.ERROR,
                content={
                    "error": str(e),
                    "original_message_id": message.message_id
                }
            )
    
    async def _handle_task_assignment(self, message: AgentMessage):
        """处理任务分配"""
        self.current_task = message.content
        self.status = AgentStatus.WORKING
        
        # 发送状态更新
        await self._broadcast_status_update()
        
        try:
            # 执行任务（由子类实现）
            result = await self.process_task(message.content)
            
            # 记录任务历史
            self.task_history.append({
                "task": message.content,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            # 发送结果
            await self.send_message(
                to_agent=message.from_agent,
                message_type=MessageType.TASK_RESULT,
                content={
                    "task_id": message.content.get("task_id"),
                    "result": result,
                    "status": "success"
                }
            )
            
            self.status = AgentStatus.IDLE
            await self._broadcast_status_update()
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] 任务执行失败: {e}", exc_info=True)
            
            # 记录失败
            self.task_history.append({
                "task": message.content,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            })
            
            # 发送错误结果
            await self.send_message(
                to_agent=message.from_agent,
                message_type=MessageType.TASK_RESULT,
                content={
                    "task_id": message.content.get("task_id"),
                    "status": "failed",
                    "error": str(e)
                }
            )
            
            self.status = AgentStatus.ERROR
            await self._broadcast_status_update()
    
    async def _handle_query(self, message: AgentMessage):
        """处理查询请求"""
        # 子类可以重写此方法
        pass
    
    async def _handle_user_decision_response(self, message: AgentMessage):
        """处理用户决策响应"""
        # 子类可以重写此方法
        pass
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务（子类必须实现）
        
        Args:
            task: 任务内容
            
        Returns:
            任务结果
        """
        pass
    
    async def send_message(
        self,
        to_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: str = "normal"
    ):
        """发送消息到其他Agent"""
        if not self.message_broker:
            logger.error(f"[{self.agent_name}] MessageBroker未设置")
            return
        
        message = AgentMessage(
            message_id=f"msg_{datetime.now().timestamp()}",
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            priority=priority
        )
        
        await self.message_broker.send_message(message)
    
    async def receive_message(self, message: AgentMessage):
        """接收消息（由MessageBroker调用）"""
        await self._message_queue.put(message)
    
    async def request_user_decision(
        self,
        question: str,
        context: Any,
        options: List[Dict[str, Any]],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        请求用户决策
        
        Args:
            question: 问题描述
            context: 决策上下文
            options: 选项列表
            timeout: 超时时间（秒）
            
        Returns:
            用户决策结果
        """
        if not self.user_interaction_callback:
            logger.error(f"[{self.agent_name}] 用户交互回调未设置")
            raise RuntimeError("用户交互回调未设置")
        
        self.status = AgentStatus.WAITING
        await self._broadcast_status_update()
        
        # 调用回调函数，等待用户响应
        decision = await self.user_interaction_callback({
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "question": question,
            "context": context,
            "options": options,
            "timeout": timeout
        })
        
        self.status = AgentStatus.WORKING
        await self._broadcast_status_update()
        
        return decision
    
    async def _broadcast_status_update(self):
        """广播状态更新"""
        if not self.message_broker:
            return
        
        await self.message_broker.broadcast_status_update({
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "current_task": self.current_task,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "ai_model": self.ai_model,
            "status": self.status.value,
            "current_task": self.current_task,
            "task_count": len(self.task_history)
        }

