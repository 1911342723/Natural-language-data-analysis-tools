"""
简洁的科学家团队实现 - 基于LangChain + OpenAI API
支持真正的流式输出和A2A协作
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import settings

logger = logging.getLogger(__name__)


class ScientistAgent:
    """单个科学家Agent"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        expertise: str,
        broadcast_callback: Callable
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.expertise = expertise
        self.broadcast_callback = broadcast_callback
        
        # 创建支持流式输出的LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
            streaming=True
        )
        
        self.system_prompt = f"""你是{self.name}，一位专业的{self.role}。

你的专长：
{self.expertise}

工作风格：
- 回答简洁明了，突出重点
- 提供专业的见解和建议
- 与团队成员协作讨论
- 保持学术严谨性

请用专业但易懂的语言回答问题。"""
    
    async def think_and_respond(self, question: str, context: str = "") -> str:
        """
        思考并回答问题 - 支持流式输出
        
        Args:
            question: 要回答的问题
            context: 上下文信息
            
        Returns:
            完整的回答
        """
        # 生成唯一的消息ID（整个流式过程使用同一个ID）
        message_id = f"stream_{self.agent_id}_{datetime.now().timestamp()}"
        
        # 构建消息
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        if context:
            messages.append(HumanMessage(content=f"背景信息：\n{context}"))
        
        messages.append(HumanMessage(content=question))
        
        # 向前端发送开始思考的信号
        await self._broadcast_stream_start(message_id)
        
        # 流式调用LLM
        full_response = ""
        try:
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    token = chunk.content
                    full_response += token
                    # 实时发送token到前端
                    await self._broadcast_stream_chunk(message_id, token)
            
            # 发送结束信号
            await self._broadcast_stream_end(message_id)
            
            logger.info(f"✅ [{self.name}] 完成回答，共{len(full_response)}字符")
            return full_response
            
        except Exception as e:
            logger.error(f"❌ [{self.name}] 思考失败: {e}")
            await self._broadcast_stream_end(message_id)
            return f"抱歉，我在思考时遇到了问题：{str(e)}"
    
    async def _broadcast_stream_start(self, message_id: str):
        """广播流式输出开始"""
        await self.broadcast_callback({
            "type": "agent_stream_start",
            "data": {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "message_id": message_id,
                "stage": "thinking"
            }
        })
    
    async def _broadcast_stream_chunk(self, message_id: str, chunk: str):
        """广播流式输出的token"""
        await self.broadcast_callback({
            "type": "agent_stream_chunk",
            "data": {
                "agent_id": self.agent_id,
                "message_id": message_id,
                "chunk": chunk
            }
        })
    
    async def _broadcast_stream_end(self, message_id: str):
        """广播流式输出结束"""
        await self.broadcast_callback({
            "type": "agent_stream_end",
            "data": {
                "agent_id": self.agent_id,
                "message_id": message_id
            }
        })


class SimpleScientistTeam:
    """简洁的科学家团队管理器"""
    
    def __init__(self, message_callback: Callable):
        self.message_callback = message_callback
        self.agents: Dict[str, ScientistAgent] = {}
        self._create_team()
    
    def _create_team(self):
        """创建科学家团队"""
        
        # 1. 首席研究员
        self.agents['pi'] = ScientistAgent(
            agent_id="pi_agent",
            name="首席研究员",
            role="项目负责人",
            expertise="""
- 制定研究计划和策略
- 协调团队成员工作
- 把控研究方向和质量
- 做出关键决策
            """,
            broadcast_callback=self.message_callback
        )
        
        # 2. 数据科学家
        self.agents['data_scientist'] = ScientistAgent(
            agent_id="data_scientist_agent",
            name="数据科学家",
            role="数据分析专家",
            expertise="""
- 数据清洗和预处理
- 探索性数据分析（EDA）
- 特征工程
- 识别数据模式
            """,
            broadcast_callback=self.message_callback
        )
        
        # 3. 统计学家
        self.agents['statistician'] = ScientistAgent(
            agent_id="statistician_agent",
            name="统计学家",
            role="统计分析专家",
            expertise="""
- 统计假设检验
- 相关性分析
- 统计建模
- 解释统计显著性
            """,
            broadcast_callback=self.message_callback
        )
        
        # 4. 可视化专家
        self.agents['visualizer'] = ScientistAgent(
            agent_id="visualizer_agent",
            name="可视化专家",
            role="数据可视化专家",
            expertise="""
- 设计合适的图表类型
- 创建美观的可视化
- 突出关键信息
- 制作发表级图表
            """,
            broadcast_callback=self.message_callback
        )
        
        # 5. 论文撰写者
        self.agents['writer'] = ScientistAgent(
            agent_id="writer_agent",
            name="论文撰写者",
            role="科研写作专家",
            expertise="""
- 撰写研究报告
- 组织论文结构
- 学术语言表达
- 引用文献
            """,
            broadcast_callback=self.message_callback
        )
        
        logger.info(f"✅ 科学家团队已组建，共{len(self.agents)}名成员")
    
    async def conduct_research(
        self, 
        user_input: str, 
        data_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行研究任务 - 简化的顺序协作流程
        
        Args:
            user_input: 用户的研究课题
            data_info: 数据信息（可选）
            
        Returns:
            研究结果
        """
        try:
            # 向前端发送开始消息
            await self._send_message("首席研究员", f"收到研究课题：{user_input}")
            await self._send_message("首席研究员", "让我组织团队开始研究...")
            
            # 数据描述
            if data_info:
                data_desc = f"数据规模：{data_info.get('total_rows')}行 × {data_info.get('total_columns')}列"
            else:
                data_desc = "这是理论研究，暂无具体数据"
            
            # 研究流程
            results = {}
            
            # 步骤1：PI制定研究计划
            await self._send_message("首席研究员", "【步骤1】制定研究计划")
            plan_question = f"""
研究课题：{user_input}
数据情况：{data_desc}

请制定详细的研究计划：
1. 研究目标
2. 研究假设
3. 研究方法
4. 预期成果
"""
            results['plan'] = await self.agents['pi'].think_and_respond(plan_question)
            
            # 步骤2：数据科学家分析
            if data_info:
                await self._send_message("数据科学家", "【步骤2】数据分析建议")
                data_question = f"""
基于研究计划：
{results['plan'][:300]}...

请提供数据分析建议：
1. 需要关注哪些数据特征？
2. 如何进行数据预处理？
3. 哪些分析方法最合适？
"""
                results['data_analysis'] = await self.agents['data_scientist'].think_and_respond(
                    data_question, 
                    context=results['plan']
                )
            
            # 步骤3：统计学家验证
            await self._send_message("统计学家", "【步骤3】统计方法建议")
            stat_question = f"""
研究计划：{results['plan'][:200]}...

请提供统计方法建议：
1. 适用的统计检验方法
2. 如何验证假设
3. 如何解释结果
"""
            results['statistics'] = await self.agents['statistician'].think_and_respond(
                stat_question,
                context=results['plan']
            )
            
            # 步骤4：可视化方案
            await self._send_message("可视化专家", "【步骤4】可视化方案设计")
            viz_question = f"""
研究内容：{user_input}

请设计可视化方案：
1. 推荐的图表类型
2. 关键展示内容
3. 设计要点
"""
            results['visualization'] = await self.agents['visualizer'].think_and_respond(
                viz_question,
                context=results['plan']
            )
            
            # 步骤5：撰写报告
            await self._send_message("论文撰写者", "【步骤5】整合研究报告")
            write_question = f"""
基于团队的研究成果，撰写研究报告摘要：

研究计划：{results['plan'][:200]}...
统计方法：{results['statistics'][:200]}...
可视化方案：{results['visualization'][:200]}...

请撰写一份简明的研究报告摘要。
"""
            results['report'] = await self.agents['writer'].think_and_respond(
                write_question,
                context=results['plan']
            )
            
            await self._send_message("首席研究员", "✅ 研究完成！团队已完成所有工作。")
            
            return {
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"研究执行失败: {e}", exc_info=True)
            await self._send_message("系统", f"研究过程中出现错误: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_message(self, agent_name: str, content: str):
        """向前端发送消息"""
        agent_id_map = {
            "首席研究员": "pi_agent",
            "数据科学家": "data_scientist_agent",
            "统计学家": "statistician_agent",
            "可视化专家": "visualizer_agent",
            "论文撰写者": "writer_agent",
            "系统": "system"
        }
        
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": agent_id_map.get(agent_name, "system"),
                "agent_name": agent_name,
                "content": {"message": content},
                "timestamp": datetime.now().isoformat()
            }
        })

