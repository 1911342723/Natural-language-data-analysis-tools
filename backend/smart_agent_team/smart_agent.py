"""
智能Agent - 能够思考、决策和使用工具
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from langchain_openai import ChatOpenAI
try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    # LangChain 1.0+ 可能需要不同的导入
    try:
        from langchain_core.agents import AgentExecutor
        from langchain.agents.openai_functions_agent.base import create_openai_tools_agent
    except ImportError:
        # 如果都不行，使用简化版本
        AgentExecutor = None
        create_openai_tools_agent = None
        
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import settings

logger = logging.getLogger(__name__)


class SmartAgent:
    """智能科研Agent - 支持工具调用和流式输出"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        expertise: str,
        tools: List,
        broadcast_callback: Callable
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.expertise = expertise
        self.tools = tools
        self.broadcast_callback = broadcast_callback
        
        # 创建LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7,
            streaming=True
        )
        
        # 工具字典（便于查找）
        self.tool_dict = {tool.name: tool for tool in self.tools if hasattr(tool, 'name')}
        
        # 尝试创建Agent（如果支持）
        if AgentExecutor and create_openai_tools_agent:
            try:
                # 创建Agent提示词
                self.prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_system_prompt()),
                    MessagesPlaceholder("chat_history", optional=True),
                    ("human", "{input}"),
                    MessagesPlaceholder("agent_scratchpad")
                ])
                
                # 创建Agent
                self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
                self.executor = AgentExecutor(
                    agent=self.agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=10
                )
                self.use_agent_executor = True
                logger.info(f"Agent '{self.name}' 使用 AgentExecutor，拥有 {len(self.tools)} 个工具")
            except Exception as e:
                logger.warning(f"无法创建 AgentExecutor: {e}，将使用简化模式")
                self.use_agent_executor = False
        else:
            self.use_agent_executor = False
            logger.info(f"Agent '{self.name}' 使用简化模式，拥有 {len(self.tools)} 个工具")
    
    def _get_system_prompt(self) -> str:
        """获取优化的系统提示词"""
        return f"""你是{self.name}，一位资深的{self.role}，在科研团队中扮演关键角色。

## 你的专业能力
{self.expertise}

## 工作原则

### 1. 深度思考，谨慎决策
- 先分析问题的本质和目标
- 考虑多个解决方案，权衡利弊
- 对复杂问题进行结构化分解
- 评估每个决策的可行性和风险

### 2. 主动使用工具
- **遇到知识盲点** → 立即搜索学术文献或网页
- **需要验证假设** → 编写并执行数据分析代码
- **超出专业范围** → 咨询相关领域的同事
- **关键决策点** → 征询用户意见，提供清晰的选项和建议

### 3. 严谨的科研方法
- 基于证据和数据，不做无根据的推测
- 引用文献和数据来源，增强可信度
- 明确指出假设、限制和不确定性
- 提供可重复、可验证的分析方法

### 4. 清晰的表达和沟通
- 使用结构化的Markdown格式
- 先给结论，再阐述理由（金字塔原理）
- 用具体例子和数据支持论点
- 避免冗长，突出关键信息

## 输出格式要求

使用Markdown格式，包括：
- **标题**: ## 主标题, ### 副标题
- **代码**: \`\`\`python\n代码\n\`\`\`
- **列表**: 有序列表(1. 2. 3.)或无序列表(- 或 *)
- **强调**: **重点内容**，*次要强调*
- **引用**: > 引用文献或数据
- **表格**: 比较数据或方案时使用表格

## 决策流程

当面对研究任务时：

1. **理解任务**
   - 明确研究目标和约束条件
   - 识别关键问题和挑战

2. **信息收集**
   - 如果是新领域 → 搜索相关文献
   - 如果需要最新信息 → 网页搜索
   - 如果不确定方法 → 咨询专家同事

3. **方案设计**
   - 提出2-3个可行方案
   - 分析每个方案的优缺点
   - 推荐最佳方案，并说明理由

4. **执行验证**
   - 对需要代码的任务 → 编写清晰的Python代码
   - 执行后检查结果是否合理
   - 发现问题及时调整

5. **结果呈现**
   - 用可视化展示关键发现
   - 用简洁语言总结要点
   - 指出下一步工作方向

## 特别注意

- ❌ 不要编造数据或文献
- ❌ 不要在不确定时给出肯定答案
- ❌ 不要跳过关键步骤
- ✅ 勇于承认知识边界
- ✅ 主动寻求帮助和验证
- ✅ 保持科学严谨性

记住：你的每个决策和输出都会影响研究的质量，请谨慎负责地工作。
"""
    
    async def think_and_act(self, task: str, context: str = "") -> str:
        """
        思考并执行任务 - 支持工具调用和流式输出
        
        Args:
            task: 要完成的任务
            context: 上下文信息
            
        Returns:
            完整的回答
        """
        # 如果有 AgentExecutor，使用它
        if self.use_agent_executor and hasattr(self, 'executor'):
            return await self._execute_with_agent(task, context)
        else:
            # 否则使用简单的流式响应
            return await self.simple_respond(task, context)
    
    async def _execute_with_agent(self, task: str, context: str = "") -> str:
        """使用 AgentExecutor 执行任务"""
        # 生成唯一的消息ID
        message_id = f"stream_{self.agent_id}_{datetime.now().timestamp()}"
        
        # 构建输入
        input_text = task
        if context:
            input_text = f"背景信息：\n{context}\n\n任务：\n{task}"
        
        # 发送开始信号
        await self._broadcast_stream_start(message_id)
        
        full_response = ""
        try:
            # 流式执行Agent
            async for chunk in self.executor.astream({"input": input_text}):
                # 提取输出内容
                if "output" in chunk:
                    content = chunk["output"]
                    full_response = content
                    
                    # 发送完整输出
                    await self._broadcast_stream_chunk(message_id, content)
                
                # 显示中间步骤
                elif "intermediate_steps" in chunk:
                    steps = chunk["intermediate_steps"]
                    for action, observation in steps:
                        tool_name = action.tool
                        tool_input = action.tool_input
                        
                        # 广播工具调用信息
                        await self._broadcast_tool_use(
                            f"**使用工具**: `{tool_name}`\n参数: {tool_input}"
                        )
            
            # 发送结束信号
            await self._broadcast_stream_end(message_id)
            
            logger.info(f"✅ [{self.name}] 任务完成")
            return full_response
            
        except Exception as e:
            logger.error(f"❌ [{self.name}] 执行失败: {e}", exc_info=True)
            await self._broadcast_stream_end(message_id)
            return f"抱歉，执行任务时遇到问题：{str(e)}"
    
    async def simple_respond(self, question: str, context: str = "") -> str:
        """
        简单回答（不使用工具）- 支持流式输出
        
        用于Agent之间的快速讨论
        """
        message_id = f"stream_{self.agent_id}_{datetime.now().timestamp()}"
        
        messages = [
            SystemMessage(content=self._get_system_prompt()),
        ]
        
        if context:
            messages.append(HumanMessage(content=f"背景：\n{context}"))
        
        messages.append(HumanMessage(content=question))
        
        await self._broadcast_stream_start(message_id)
        
        full_response = ""
        try:
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    token = chunk.content
                    full_response += token
                    await self._broadcast_stream_chunk(message_id, token)
            
            await self._broadcast_stream_end(message_id)
            return full_response
            
        except Exception as e:
            logger.error(f"回答失败: {e}")
            await self._broadcast_stream_end(message_id)
            return f"抱歉，回答时出错：{str(e)}"
    
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
    
    async def _broadcast_tool_use(self, tool_info: str):
        """广播工具使用信息"""
        await self.broadcast_callback({
            "type": "agent_message",
            "data": {
                "from_agent": self.agent_id,
                "content": {"message": tool_info},
                "timestamp": datetime.now().isoformat()
            }
        })

