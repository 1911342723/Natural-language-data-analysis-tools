"""
消息代理 - 负责Agent间的消息路由和通信
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from collections import defaultdict

from multi_agent.base_agent import AgentMessage, BaseAgent

logger = logging.getLogger(__name__)


class MessageBroker:
    """
    消息代理
    
    功能：
    - Agent注册和管理
    - 消息路由和分发
    - 消息历史记录
    - 广播消息
    - WebSocket连接管理（用于前端可视化）
    """
    
    def __init__(self):
        # Agent注册表：{agent_id: agent_instance}
        self.agents: Dict[str, BaseAgent] = {}
        
        # 消息历史
        self.message_history: List[AgentMessage] = []
        
        # WebSocket连接（用于前端实时更新）
        self.websocket_connections: List[Any] = []
        
        # 消息统计
        self.message_stats = defaultdict(int)
        
        logger.info("MessageBroker初始化完成")
    
    def register_agent(self, agent: BaseAgent):
        """注册Agent"""
        if agent.agent_id in self.agents:
            logger.warning(f"Agent {agent.agent_id} 已注册")
            return
        
        self.agents[agent.agent_id] = agent
        agent.set_message_broker(self)
        
        logger.info(f"Agent已注册: {agent.agent_name} ({agent.agent_id})")
    
    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent已注销: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent实例"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[BaseAgent]:
        """获取所有Agent"""
        return list(self.agents.values())
    
    async def send_message(self, message: AgentMessage):
        """
        发送消息
        
        Args:
            message: 消息对象
        """
        # 记录消息
        self.message_history.append(message)
        self.message_stats[message.message_type.value] += 1
        
        logger.info(
            f"[MessageBroker] 路由消息: "
            f"{message.from_agent} → {message.to_agent} "
            f"({message.message_type.value})"
        )
        
        # 特殊处理：如果目标是frontend，直接广播到前端
        if message.to_agent == "frontend":
            await self.broadcast_to_frontend({
                "type": "agent_message",
                "data": message.to_dict()
            })
            return
        
        # 查找目标Agent
        target_agent = self.agents.get(message.to_agent)
        
        if not target_agent:
            logger.error(f"目标Agent不存在: {message.to_agent}")
            # 发送错误消息给发送者
            sender_agent = self.agents.get(message.from_agent)
            if sender_agent:
                error_message = AgentMessage(
                    message_id=f"error_{datetime.now().timestamp()}",
                    from_agent="system",
                    to_agent=message.from_agent,
                    message_type=MessageType.ERROR,
                    content={
                        "error": f"目标Agent不存在: {message.to_agent}",
                        "original_message_id": message.message_id
                    },
                    timestamp=datetime.now().isoformat()
                )
                await sender_agent.receive_message(error_message)
            return
        
        # 投递消息
        await target_agent.receive_message(message)
        
        # 广播到前端（用于可视化）
        await self.broadcast_to_frontend({
            "type": "agent_message",
            "data": message.to_dict()
        })
    
    async def broadcast_message(
        self,
        from_agent: str,
        message_type: str,
        content: Dict[str, Any],
        exclude_agents: Optional[List[str]] = None
    ):
        """
        广播消息到所有Agent
        
        Args:
            from_agent: 发送者
            message_type: 消息类型
            content: 消息内容
            exclude_agents: 排除的Agent列表
        """
        exclude_agents = exclude_agents or []
        
        for agent_id, agent in self.agents.items():
            if agent_id == from_agent or agent_id in exclude_agents:
                continue
            
            message = AgentMessage(
                message_id=f"broadcast_{datetime.now().timestamp()}",
                from_agent=from_agent,
                to_agent=agent_id,
                message_type=MessageType(message_type),
                content=content,
                timestamp=datetime.now().isoformat()
            )
            
            await self.send_message(message)
    
    async def broadcast_status_update(self, status_data: Dict[str, Any]):
        """
        广播Agent状态更新（给前端）
        
        Args:
            status_data: 状态数据
        """
        await self.broadcast_to_frontend({
            "type": "agent_status_update",
            "data": status_data
        })
    
    async def broadcast_to_frontend(self, data: Dict[str, Any]):
        """
        广播消息到所有前端WebSocket连接
        
        Args:
            data: 要发送的数据
        """
        if not self.websocket_connections:
            # 只在第一次时警告，避免日志刷屏
            if not hasattr(self, '_ws_warned'):
                logger.warning("⚠️ 没有活跃的WebSocket连接，消息将被缓存")
                self._ws_warned = True
            return
        
        # 重置警告标志
        if hasattr(self, '_ws_warned'):
            delattr(self, '_ws_warned')
        
        logger.debug(f"📤 向前端广播消息: type={data.get('type')}")
        
        # 发送到所有活跃的WebSocket连接
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.debug(f"WebSocket发送失败: {e}")
                disconnected.append(ws)
        
        # 移除断开的连接
        for ws in disconnected:
            self.websocket_connections.remove(ws)
            logger.info(f"⚠️ 移除断开的WebSocket连接，剩余: {len(self.websocket_connections)}")
    
    def add_websocket_connection(self, websocket: Any):
        """添加WebSocket连接"""
        self.websocket_connections.append(websocket)
        logger.info(f"WebSocket连接已添加，当前连接数: {len(self.websocket_connections)}")
    
    def remove_websocket_connection(self, websocket: Any):
        """移除WebSocket连接"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
            logger.info(f"WebSocket连接已移除，当前连接数: {len(self.websocket_connections)}")
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取消息历史
        
        Args:
            agent_id: 筛选特定Agent的消息（None表示所有）
            limit: 返回最近N条消息
            
        Returns:
            消息列表
        """
        messages = self.message_history
        
        if agent_id:
            messages = [
                msg for msg in messages
                if msg.from_agent == agent_id or msg.to_agent == agent_id
            ]
        
        # 返回最近的N条
        return [msg.to_dict() for msg in messages[-limit:]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取消息统计"""
        return {
            "total_agents": len(self.agents),
            "total_messages": len(self.message_history),
            "message_types": dict(self.message_stats),
            "active_websockets": len(self.websocket_connections),
            "agents": [agent.get_info() for agent in self.agents.values()]
        }
    
    async def shutdown(self):
        """关闭MessageBroker，停止所有Agent"""
        logger.info("开始关闭MessageBroker...")
        
        # 停止所有Agent
        for agent in self.agents.values():
            try:
                await agent.stop()
            except Exception as e:
                logger.error(f"停止Agent失败 {agent.agent_id}: {e}")
        
        # 关闭所有WebSocket连接
        for ws in self.websocket_connections:
            try:
                await ws.close()
            except Exception as e:
                logger.error(f"关闭WebSocket失败: {e}")
        
        self.agents.clear()
        self.websocket_connections.clear()
        
        logger.info("MessageBroker已关闭")


# 导入MessageType（避免循环导入）
from multi_agent.base_agent import MessageType

