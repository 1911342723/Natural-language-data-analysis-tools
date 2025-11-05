"""
用户决策管理器 - 处理Agent与用户的交互决策
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DecisionManager:
    """管理用户决策请求和响应"""
    
    def __init__(self):
        # 待决策队列：decision_id -> {question, options, future}
        self.pending_decisions: Dict[str, Dict[str, Any]] = {}
        
        # 决策超时（秒）
        self.timeout = 300  # 5分钟
        
        logger.info("决策管理器初始化完成")
    
    async def request_user_decision(
        self,
        question: str,
        options: list,
        context: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        请求用户做决策，并等待响应
        
        Args:
            question: 要问用户的问题
            options: 选项列表
            context: 上下文信息
            timeout: 超时时间（秒）
            
        Returns:
            用户的选择 {"choice": "...", "feedback": "..."}
        """
        # 生成唯一决策ID
        decision_id = f"decision_{uuid.uuid4().hex[:8]}"
        
        # 创建Future对象用于等待
        decision_future = asyncio.Future()
        
        # 存储待决策信息
        self.pending_decisions[decision_id] = {
            "question": question,
            "options": options,
            "context": context or {},
            "future": decision_future,
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"❓ 创建用户决策请求: {decision_id}")
        logger.info(f"   问题: {question}")
        logger.info(f"   选项: {options}")
        
        try:
            # 等待用户响应（带超时）
            actual_timeout = timeout or self.timeout
            result = await asyncio.wait_for(
                decision_future,
                timeout=actual_timeout
            )
            
            logger.info(f"✅ 收到用户决策: {decision_id} -> {result}")
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ 用户决策超时: {decision_id}")
            # 清理
            self.pending_decisions.pop(decision_id, None)
            # 返回默认选择
            return {
                "choice": options[0] if options else "继续",
                "feedback": "（超时，使用默认选项）",
                "timeout": True
            }
        
        except Exception as e:
            logger.error(f"决策请求失败: {e}")
            self.pending_decisions.pop(decision_id, None)
            return {
                "choice": options[0] if options else "继续",
                "feedback": f"（发生错误：{str(e)}）",
                "error": True
            }
    
    def submit_user_decision(
        self,
        decision_id: str,
        choice: str,
        feedback: Optional[str] = None
    ) -> bool:
        """
        提交用户的决策
        
        Args:
            decision_id: 决策ID
            choice: 用户选择
            feedback: 用户反馈
            
        Returns:
            是否成功提交
        """
        if decision_id not in self.pending_decisions:
            logger.warning(f"决策ID不存在: {decision_id}")
            return False
        
        decision_info = self.pending_decisions[decision_id]
        future = decision_info["future"]
        
        if future.done():
            logger.warning(f"决策已完成: {decision_id}")
            return False
        
        # 设置Future结果
        result = {
            "choice": choice,
            "feedback": feedback or "",
            "decision_id": decision_id
        }
        future.set_result(result)
        
        # 清理
        self.pending_decisions.pop(decision_id)
        
        logger.info(f"✅ 用户决策已提交: {decision_id}")
        return True
    
    def get_pending_decisions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有待决策的请求"""
        return {
            decision_id: {
                "question": info["question"],
                "options": info["options"],
                "context": info["context"],
                "created_at": info["created_at"]
            }
            for decision_id, info in self.pending_decisions.items()
        }
    
    def cancel_decision(self, decision_id: str) -> bool:
        """取消一个决策请求"""
        if decision_id not in self.pending_decisions:
            return False
        
        decision_info = self.pending_decisions[decision_id]
        future = decision_info["future"]
        
        if not future.done():
            future.cancel()
        
        self.pending_decisions.pop(decision_id)
        logger.info(f"❌ 决策已取消: {decision_id}")
        return True


# 全局决策管理器实例
decision_manager = DecisionManager()

