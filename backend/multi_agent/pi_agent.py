"""
PI Agent - Principal Investigator Agent
主负责人AI，负责项目总控、任务分配、质量把关
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from multi_agent.base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus
from core.ai_client import ai_client

logger = logging.getLogger(__name__)


class PIAgent(BaseAgent):
    """
    主负责人AI
    
    职责：
    - 理解用户的科研目标
    - 制定研究计划
    - 分解任务并分配给专家Agent
    - 监控任务执行进度
    - 整合各个Agent的结果
    - 在关键节点请求用户决策
    - 生成最终研究报告
    """
    
    def __init__(
        self,
        agent_id: str = "pi_agent",
        agent_name: str = "首席研究员",
        ai_model: str = "gpt-4o-mini"
    ):
        system_prompt = """你是一位经验丰富的首席研究员（Principal Investigator），负责领导科研团队完成数据分析和论文撰写任务。

你的职责：
1. 理解用户的科研目标和需求
2. 制定详细的研究计划
3. 将复杂任务分解为可执行的子任务
4. 合理分配任务给团队成员（数据科学家、统计学家、可视化专家、论文撰写者等）
5. 监控任务执行进度，协调团队成员
6. 在关键决策点咨询用户意见
7. 整合所有结果，生成最终报告

工作原则：
- 严谨：遵循科学研究规范
- 高效：合理安排任务优先级
- 透明：及时汇报进展，主动请示决策
- 质量优先：确保研究结果的准确性和可靠性
"""
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type="pi",
            ai_model=ai_model,
            system_prompt=system_prompt
        )
        
        # 研究计划
        self.research_plan: Optional[Dict[str, Any]] = None
        
        # 任务列表
        self.tasks: List[Dict[str, Any]] = []
        
        # 团队成员Agent ID
        self.team_agents: List[str] = []
        
        # 结果收集
        self.task_results: Dict[str, Any] = {}
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理任务
        
        Args:
            task: 任务内容，包含：
                - type: "start_research" - 启动研究
                - user_input: 用户的研究目标
                - data_info: 数据信息
                
        Returns:
            研究结果
        """
        task_type = task.get("type")
        
        if task_type == "start_research":
            return await self._handle_start_research(task)
        else:
            raise ValueError(f"未知的任务类型: {task_type}")
    
    async def _handle_start_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理研究启动"""
        user_input = task.get("user_input", "")
        data_info = task.get("data_info") or None  # 确保空字典也转为None
        session_id = task.get("session_id")
        
        logger.info(f"[{self.agent_name}] 开始研究项目")
        logger.info(f"  用户目标: {user_input}")
        
        # 向前端广播开始消息
        await self._send_message_to_frontend(
            f"大家好！我是首席研究员。我已经收到研究课题：「{user_input}」"
        )
        
        # 向前端发送开始消息
        await self.send_message(
            to_agent="frontend",
            message_type=MessageType.STATUS_UPDATE,
            content={
                "message": f"收到研究课题：{user_input}。我将组织团队开始分析...",
                "description": f"收到研究课题：{user_input}。我将组织团队开始分析..."
            }
        )
        
        # 步骤1：理解需求并制定研究计划
        self.status = AgentStatus.THINKING
        await self._broadcast_status_update()
        
        await self._send_message_to_frontend(
            "让我先分析一下这个研究课题，制定详细的研究计划..."
        )
        
        research_plan = await self._create_research_plan(user_input, data_info)
        self.research_plan = research_plan
        
        await self._send_message_to_frontend(
            f"我已经制定好研究计划了！\n\n"
            f"📋 研究目标：{research_plan.get('goal', 'N/A')}\n"
            f"🎯 预期成果：{research_plan.get('expected_outcomes', 'N/A')}\n\n"
            f"现在开始分配任务给团队成员..."
        )
        
        logger.info(f"[{self.agent_name}] 研究计划已制定")
        
        # 向前端发送计划消息
        plan_summary = f"""我已经制定了研究计划：

📋 研究目标：{research_plan.get('goal', 'N/A')}

📝 研究假设：{research_plan.get('hypothesis', 'N/A')}

🔬 研究步骤：
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(research_plan.get('steps', []))])}

🎯 预期成果：{research_plan.get('expected_outcomes', 'N/A')}

现在我需要您确认这个计划是否可行。"""
        
        await self.send_message(
            to_agent="frontend",
            message_type=MessageType.STATUS_UPDATE,
            content={
                "message": plan_summary,
                "description": plan_summary
            }
        )
        
        # 步骤2：请求用户确认研究计划
        user_decision = await self.request_user_decision(
            question="请确认研究计划",
            context={
                "research_goal": research_plan["goal"],
                "hypothesis": research_plan["hypothesis"],
                "steps": research_plan["steps"],
                "expected_outcomes": research_plan["expected_outcomes"]
            },
            options=[
                {
                    "value": "confirm",
                    "label": "确认，继续执行",
                    "explanation": "研究计划符合预期，开始执行"
                },
                {
                    "value": "modify",
                    "label": "需要修改",
                    "explanation": "研究计划需要调整"
                },
                {
                    "value": "cancel",
                    "label": "取消研究",
                    "explanation": "不执行此研究"
                }
            ]
        )
        
        if user_decision.get("choice") == "cancel":
            return {
                "status": "cancelled",
                "message": "用户取消了研究"
            }
        
        if user_decision.get("choice") == "modify":
            # TODO: 根据用户反馈修改计划
            user_feedback = user_decision.get("feedback", "")
            logger.info(f"[{self.agent_name}] 用户要求修改计划: {user_feedback}")
            # 这里可以重新调用AI修改计划
        
        # 向前端发送开始执行的消息
        await self.send_message(
            to_agent="frontend",
            message_type=MessageType.STATUS_UPDATE,
            content={
                "message": "好的，计划已确认！现在开始分配任务给团队成员...",
                "description": "好的，计划已确认！现在开始分配任务给团队成员..."
            }
        )
        
        # 步骤3：分解任务并分配
        self.status = AgentStatus.WORKING
        await self._broadcast_status_update()
        
        tasks = self._decompose_tasks(research_plan)
        self.tasks = tasks
        
        logger.info(f"[{self.agent_name}] 任务已分解，共{len(tasks)}个任务")
        
        # 向前端发送任务分解消息
        task_list = "\n".join([f"{i+1}. {t['name']} → {t['assigned_to']}" for i, t in enumerate(tasks)])
        await self.send_message(
            to_agent="frontend",
            message_type=MessageType.STATUS_UPDATE,
            content={
                "message": f"任务已分解为{len(tasks)}个子任务：\n{task_list}",
                "description": f"任务已分解为{len(tasks)}个子任务：\n{task_list}"
            }
        )
        
        # 步骤4：依次执行任务（简化版，实际可以并行）
        for idx, task_item in enumerate(tasks):
            logger.info(
                f"[{self.agent_name}] 执行任务 {idx+1}/{len(tasks)}: "
                f"{task_item['name']}"
            )
            
            # 分配给对应的Agent
            target_agent_id = task_item["assigned_to"]
            
            # 发送任务
            await self.send_message(
                to_agent=target_agent_id,
                message_type=MessageType.TASK_ASSIGNMENT,
                content={
                    "task_id": task_item["task_id"],
                    "task_name": task_item["name"],
                    "description": task_item["description"],
                    "session_id": session_id,
                    "data_info": data_info,
                    "requirements": task_item.get("requirements", {}),
                    "context": {
                        "research_goal": research_plan["goal"],
                        "previous_results": self.task_results
                    }
                }
            )
            
            # 等待结果（简化实现，实际应该用异步回调）
            # 这里暂时用一个简单的轮询等待
            result = await self._wait_for_task_result(task_item["task_id"])
            
            if result.get("status") == "failed":
                logger.error(f"[{self.agent_name}] 任务失败: {result.get('error')}")
                # 决定是否继续或重试
                # ...
            else:
                logger.info(f"[{self.agent_name}] 任务完成")
                self.task_results[task_item["task_id"]] = result
        
        # 步骤5：整合结果
        final_result = await self._integrate_results()
        
        logger.info(f"[{self.agent_name}] 研究完成")
        
        return {
            "status": "completed",
            "research_plan": research_plan,
            "task_results": self.task_results,
            "final_result": final_result
        }
    
    async def _create_research_plan(
        self,
        user_input: str,
        data_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """创建研究计划"""
        
        # 构建提示词
        # 处理数据信息
        if data_info:
            data_desc = f"""
数据信息：
- 数据行数：{data_info.get('total_rows', 'N/A')}
- 字段数量：{data_info.get('total_columns', 'N/A')}
- 字段列表：{', '.join(data_info.get('columns', [])[:10])}...
"""
        else:
            data_desc = """
数据信息：暂无数据文件，这是一个理论研究或方案设计任务。
"""
        
        prompt = f"""根据用户的研究目标和数据信息，制定一个详细的研究计划。

用户研究目标：
{user_input}
{data_desc}

请输出JSON格式的研究计划，包含：
1. goal: 研究目标（清晰明确的描述）
2. hypothesis: 研究假设（如果适用）
3. steps: 研究步骤列表
4. expected_outcomes: 预期成果
5. required_analyses: 需要的分析类型（如描述性统计、相关性分析、可视化等）

输出格式示例：
{{
    "goal": "分析销售数据，找出影响销售额的关键因素",
    "hypothesis": "产品价格与销售额呈负相关",
    "steps": [
        "数据清洗和探索性分析",
        "描述性统计",
        "相关性分析",
        "可视化展示",
        "撰写分析报告"
    ],
    "expected_outcomes": "识别关键影响因素，提供优化建议",
    "required_analyses": ["descriptive_stats", "correlation", "visualization"]
}}
"""
        
        try:
            # 调用AI（流式）
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # 创建流式消息ID
            stream_message_id = f"stream_{datetime.now().timestamp()}"
            
            # 向前端发送开始流式输出的通知
            if self.message_broker:
                await self.message_broker.broadcast_to_frontend({
                    "type": "agent_stream_start",
                    "data": {
                        "agent_id": self.agent_id,
                        "message_id": stream_message_id,
                        "stage": "thinking"
                    }
                })
            
            # 流式调用AI
            response_chunks = []
            for chunk in ai_client.chat_stream(messages, temperature=0.3):
                response_chunks.append(chunk)
                # 实时发送到前端
                if self.message_broker:
                    await self.message_broker.broadcast_to_frontend({
                        "type": "agent_stream_chunk",
                        "data": {
                            "agent_id": self.agent_id,
                            "message_id": stream_message_id,
                            "chunk": chunk
                        }
                    })
            
            response = ''.join(response_chunks)
            
            # 流式结束通知
            if self.message_broker:
                await self.message_broker.broadcast_to_frontend({
                    "type": "agent_stream_end",
                    "data": {
                        "agent_id": self.agent_id,
                        "message_id": stream_message_id
                    }
                })
            
            # 解析JSON
            import json
            import re
            
            # 提取JSON（可能包含在```json```代码块中）
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            plan = json.loads(json_str)
            
            return plan
            
        except Exception as e:
            logger.error(f"创建研究计划失败: {e}", exc_info=True)
            # 返回默认计划
            return {
                "goal": user_input,
                "hypothesis": "待确定",
                "steps": ["数据分析", "生成报告"],
                "expected_outcomes": "数据洞察和可视化结果",
                "required_analyses": ["descriptive_stats", "visualization"]
            }
    
    def _decompose_tasks(self, research_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分解任务"""
        tasks = []
        
        required_analyses = research_plan.get("required_analyses", [])
        
        # 根据需要的分析类型生成任务
        task_id = 1
        
        if "descriptive_stats" in required_analyses or "data_cleaning" in required_analyses:
            tasks.append({
                "task_id": f"task_{task_id}",
                "name": "数据清洗和探索性分析",
                "description": "检查数据质量，进行描述性统计",
                "assigned_to": "data_scientist_agent",
                "requirements": {
                    "check_missing": True,
                    "check_outliers": True,
                    "descriptive_stats": True
                }
            })
            task_id += 1
        
        if "visualization" in required_analyses:
            tasks.append({
                "task_id": f"task_{task_id}",
                "name": "数据可视化",
                "description": "生成关键指标的可视化图表",
                "assigned_to": "data_scientist_agent",  # 暂时还是数据科学家
                "requirements": {
                    "chart_types": ["histogram", "scatter", "bar"]
                }
            })
            task_id += 1
        
        return tasks
    
    async def _wait_for_task_result(
        self,
        task_id: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """等待任务结果"""
        # 简化实现：等待消息队列中的任务结果
        # 实际应该用更优雅的异步回调机制
        
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # 检查是否超时
            if asyncio.get_event_loop().time() - start_time > timeout:
                return {
                    "status": "failed",
                    "error": "任务超时"
                }
            
            # 检查结果是否已收到
            if task_id in self.task_results:
                return self.task_results[task_id]
            
            # 等待一小段时间
            await asyncio.sleep(1)
    
    async def _integrate_results(self) -> Dict[str, Any]:
        """整合所有任务的结果"""
        
        # 简化实现：直接返回所有结果
        return {
            "summary": "研究已完成，所有任务执行成功",
            "task_results": self.task_results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _send_message_to_frontend(self, content: str):
        """向前端发送可读消息"""
        if self.message_broker:
            await self.message_broker.broadcast_to_frontend({
                "type": "agent_message",
                "data": {
                    "from_agent": self.agent_id,
                    "to_agent": "user",
                    "message_type": "chat",
                    "content": {
                        "message": content
                    },
                    "timestamp": datetime.now().isoformat()
                }
            })
    
    async def _handle_query(self, message: AgentMessage):
        """处理其他Agent的查询"""
        logger.info(f"[{self.agent_name}] 收到查询: {message.content}")
        # TODO: 实现查询处理逻辑

