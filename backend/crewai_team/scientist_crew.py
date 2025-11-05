"""
基于CrewAI的科学家团队实现
真正的Agent之间对话和协作
"""
import asyncio
from typing import Dict, Any, Optional, Callable
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """LangChain回调处理器 - 捕获LLM思考时的流式token"""
    
    def __init__(self, agent_name: str, broadcast_func: Callable, main_loop):
        self.agent_name = agent_name
        self.broadcast_func = broadcast_func
        self.main_loop = main_loop
        self.current_message_id = None
        self.is_streaming = False
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM开始思考"""
        self.current_message_id = f"stream_{datetime.now().timestamp()}"
        self.is_streaming = True
        
        logger.info(f"🤔 [{self.agent_name}] 开始思考...")
        
        # 发送开始流式输出的信号
        future = asyncio.run_coroutine_threadsafe(
            self.broadcast_func({
                "type": "agent_stream_start",
                "data": {
                    "agent_id": self._get_agent_id(),
                    "agent_name": self.agent_name,
                    "message_id": self.current_message_id,
                    "stage": "thinking"
                }
            }),
            self.main_loop
        )
        try:
            future.result(timeout=1.0)
        except Exception as e:
            logger.error(f"发送stream_start失败: {e}")
    
    def on_llm_new_token(self, token: str, **kwargs):
        """接收到新token - 实时流式输出"""
        if not self.is_streaming:
            return
            
        # 实时广播token
        future = asyncio.run_coroutine_threadsafe(
            self.broadcast_func({
                "type": "agent_stream_chunk",
                "data": {
                    "agent_id": self._get_agent_id(),
                    "message_id": self.current_message_id,
                    "chunk": token
                }
            }),
            self.main_loop
        )
        try:
            future.result(timeout=0.5)
        except Exception as e:
            logger.debug(f"发送token失败: {e}")
    
    def on_llm_end(self, response, **kwargs):
        """LLM思考结束"""
        if not self.is_streaming:
            return
            
        logger.info(f"✅ [{self.agent_name}] 思考完成")
        
        # 发送结束信号
        future = asyncio.run_coroutine_threadsafe(
            self.broadcast_func({
                "type": "agent_stream_end",
                "data": {
                    "agent_id": self._get_agent_id(),
                    "message_id": self.current_message_id
                }
            }),
            self.main_loop
        )
        try:
            future.result(timeout=1.0)
        except Exception as e:
            logger.error(f"发送stream_end失败: {e}")
        
        self.is_streaming = False
        self.current_message_id = None
    
    def on_llm_error(self, error, **kwargs):
        """LLM出错"""
        logger.error(f"❌ [{self.agent_name}] LLM错误: {error}")
        self.is_streaming = False
    
    def _get_agent_id(self) -> str:
        """根据名称获取agent_id"""
        mapping = {
            "首席研究员": "pi_agent",
            "数据科学家": "data_scientist_agent",
            "统计学家": "statistician_agent",
            "可视化专家": "visualizer_agent",
            "科研论文撰写者": "writer_agent",
            "同行评审专家": "reviewer_agent"
        }
        return mapping.get(self.agent_name, "system")


class ScientistCrew:
    """科学家团队 - 使用CrewAI实现真实的A2A协作"""
    
    def __init__(self, message_callback: Optional[Callable] = None):
        """
        初始化科学家团队
        
        Args:
            message_callback: 消息回调函数，用于向前端广播消息
        """
        self.message_callback = message_callback
        
        # 创建科学家团队
        self.agents = self._create_agents()
        
        logger.info(f"✅ CrewAI科学家团队已初始化，共{len(self.agents)}名成员")
    
    def _create_agents(self) -> Dict[str, Agent]:
        """创建所有科学家Agent"""
        
        agents = {}
        
        # 临时创建一个基础LLM（后续会在conduct_research中替换为带callback的版本）
        base_llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.7
        )
        
        # 1. 首席研究员 (PI)
        agents['pi'] = Agent(
            role="首席研究员",
            goal="统筹整个研究项目，协调团队成员，确保研究质量",
            backstory="""你是一位经验丰富的首席研究员，擅长：
            - 制定研究计划和策略
            - 协调团队成员工作
            - 把控研究方向和质量
            - 做出关键决策
            你善于倾听团队成员的意见，并做出明智的判断。回答要简洁明了。""",
            llm=base_llm,
            verbose=True,
            allow_delegation=True,  # 允许委派任务
            max_iter=3
        )
        
        # 2. 数据科学家
        agents['data_scientist'] = Agent(
            role="数据科学家",
            goal="负责数据清洗、探索性分析和特征工程",
            backstory="""你是一位专业的数据科学家，擅长：
            - 数据质量检查和清洗
            - 探索性数据分析（EDA）
            - 特征工程和数据转换
            - 识别数据中的模式和异常
            你会主动提出对数据的见解，并与团队讨论。回答要简洁明了。""",
            llm=base_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # 3. 统计学家
        agents['statistician'] = Agent(
            role="统计学家",
            goal="进行统计分析、假设检验和建立统计模型",
            backstory="""你是一位严谨的统计学家，擅长：
            - 统计假设检验
            - 相关性和因果分析
            - 统计建模和预测
            - 解释统计结果的意义
            你会质疑不合理的假设，确保统计严谨性。回答要简洁明了。""",
            llm=base_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # 4. 可视化专家
        agents['visualizer'] = Agent(
            role="可视化专家",
            goal="创建清晰、美观、有洞察力的数据可视化",
            backstory="""你是一位数据可视化专家，擅长：
            - 选择合适的图表类型
            - 设计美观且信息丰富的可视化
            - 突出数据中的关键信息
            - 制作发表级别的图表
            你会建议最佳的可视化方案。回答要简洁明了。""",
            llm=base_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # 5. 论文撰写者
        agents['writer'] = Agent(
            role="科研论文撰写者",
            goal="撰写高质量的研究论文和报告",
            backstory="""你是一位经验丰富的科研作者，擅长：
            - 撰写清晰的研究报告
            - 组织论文结构
            - 用学术语言表达发现
            - 引用相关文献
            你会确保论文的逻辑性和可读性。回答要简洁明了。""",
            llm=base_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        # 6. 审稿人
        agents['reviewer'] = Agent(
            role="同行评审专家",
            goal="批判性地评审研究成果，提出改进建议",
            backstory="""你是一位严格的审稿人，擅长：
            - 发现研究中的问题和不足
            - 提出建设性的改进意见
            - 评估研究的创新性和严谨性
            - 确保研究符合学术标准
            你会直言不讳地指出问题。回答要简洁明了。""",
            llm=base_llm,
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
        
        return agents
    
    async def conduct_research(
        self, 
        user_input: str, 
        data_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行完整的研究流程
        
        Args:
            user_input: 用户的研究课题
            data_info: 数据信息（可选）
        
        Returns:
            研究结果
        """
        try:
            # 向前端广播开始消息
            await self._broadcast("首席研究员", f"收到研究课题：{user_input}")
            await self._broadcast("首席研究员", "让我组织团队开始讨论和协作...")
            
            # 构建研究任务
            tasks = await self._create_research_tasks(user_input, data_info)
            
            # 获取当前事件循环（用于callback）
            main_loop = asyncio.get_event_loop()
            last_output_hash = set()  # 用于去重
            current_agent = None  # 跟踪当前正在工作的Agent
            
            # 创建Crew，配置step_callback
            def step_callback(output):
                """CrewAI的步骤回调 - 显示Agent工作进度"""
                nonlocal last_output_hash, current_agent
                try:
                    # 提取Agent名称
                    if hasattr(output, 'agent') and hasattr(output.agent, 'role'):
                        agent_name = output.agent.role
                    else:
                        return  # 跳过非Agent输出
                    
                    # 如果是新的Agent开始工作，发送"正在思考"消息
                    if current_agent != agent_name:
                        current_agent = agent_name
                        logger.info(f"🤔 [{agent_name}] 开始工作...")
                        future = asyncio.run_coroutine_threadsafe(
                            self._broadcast(agent_name, f"正在思考和分析..."),
                            main_loop
                        )
                        try:
                            future.result(timeout=1.0)
                        except:
                            pass
                    
                    # 提取内容 - 只要真实的输出结果
                    content = None
                    if hasattr(output, 'raw') and output.raw:
                        content = str(output.raw).strip()
                    
                    # 过滤无效内容
                    if not content or len(content) < 20:
                        return
                    
                    # 去重 - 避免重复发送相同内容
                    content_hash = hash(content)
                    if content_hash in last_output_hash:
                        return
                    last_output_hash.add(content_hash)
                    
                    # 限制输出长度
                    max_len = 800
                    if len(content) > max_len:
                        content = content[:max_len] + "\n\n...(内容较长，已截断)"
                    
                    logger.info(f"✅ [{agent_name}] 完成工作，输出结果")
                    
                    # 使用线程安全的方式广播结果
                    future = asyncio.run_coroutine_threadsafe(
                        self._broadcast(agent_name, content),
                        main_loop
                    )
                    try:
                        future.result(timeout=2.0)
                    except:
                        pass
                    
                except Exception as e:
                    logger.error(f"Step callback失败: {e}", exc_info=True)
            
            crew = Crew(
                agents=list(self.agents.values()),
                tasks=tasks,
                process=Process.sequential,  # 顺序执行
                verbose=True,  # 启用详细日志
                step_callback=step_callback  # 添加步骤回调
            )
            
            # 执行研究（在后台线程中执行，因为crew.kickoff()是同步的）
            logger.info("🚀 CrewAI开始执行研究任务...")
            result = await asyncio.to_thread(crew.kickoff)
            
            await self._broadcast("首席研究员", "研究完成！团队成果已整理完毕。")
            
            return {
                "status": "completed",
                "result": result,
                "tasks_output": [task.output for task in tasks if hasattr(task, 'output')]
            }
            
        except Exception as e:
            logger.error(f"研究执行失败: {e}", exc_info=True)
            await self._broadcast("系统", f"研究过程中出现错误: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _create_research_tasks(
        self,
        user_input: str,
        data_info: Optional[Dict[str, Any]]
    ) -> list:
        """创建研究任务链"""
        
        tasks = []
        
        # 数据描述
        data_desc = "暂无具体数据，这是理论研究。" if not data_info else f"""
        数据规模：{data_info.get('total_rows', 'N/A')}行 × {data_info.get('total_columns', 'N/A')}列
        主要字段：{', '.join(data_info.get('columns', [])[:10])}
        """
        
        # 任务1：制定研究计划
        await self._broadcast("首席研究员", "【任务1】我开始制定研究计划...")
        task1 = Task(
            description=f"""
            研究课题：{user_input}
            数据情况：{data_desc}
            
            作为首席研究员，请制定详细的研究计划：
            1. 明确研究目标和假设
            2. 设计研究方法和步骤
            3. 分配团队成员的工作
            4. 列出预期成果
            
            请与团队成员讨论并确定最佳方案。
            """,
            agent=self.agents['pi'],
            expected_output="一份详细的研究计划，包括目标、方法、分工和预期成果"
        )
        tasks.append(task1)
        
        # 任务2：数据分析（如果有数据）
        if data_info:
            await self._broadcast("数据科学家", "【任务2】我接手数据分析工作...")
            task2 = Task(
                description="""
                根据研究计划，进行数据分析：
                1. 检查数据质量
                2. 进行探索性分析
                3. 识别关键特征
                4. 提出初步发现
                
                与统计学家讨论分析结果的统计意义。
                """,
                agent=self.agents['data_scientist'],
                expected_output="数据分析报告，包括数据质量评估和初步发现",
                context=[task1]
            )
            tasks.append(task2)
            
            # 任务3：统计检验
            await self._broadcast("统计学家", "【任务3】我负责统计检验和建模...")
            task3 = Task(
                description="""
                基于数据分析结果，进行统计检验：
                1. 验证研究假设
                2. 进行显著性检验
                3. 评估结果的可靠性
                4. 解释统计意义
                
                与数据科学家讨论结果的实际意义。
                """,
                agent=self.agents['statistician'],
                expected_output="统计分析报告，包括假设检验结果和统计解释",
                context=[task2]
            )
            tasks.append(task3)
            
            # 任务4：可视化
            await self._broadcast("可视化专家", "【任务4】我来设计数据可视化方案...")
            task4 = Task(
                description="""
                创建数据可视化方案：
                1. 设计关键图表
                2. 突出重要发现
                3. 确保图表的专业性
                4. 建议可视化改进
                
                与团队讨论最佳的可视化方式。
                """,
                agent=self.agents['visualizer'],
                expected_output="可视化方案，列出所需图表类型和设计要点",
                context=[task3]
            )
            tasks.append(task4)
        
        # 任务5：撰写报告
        await self._broadcast("科研论文撰写者", "【任务5】我开始撰写研究报告...")
        task5 = Task(
            description="""
            整合所有研究成果，撰写研究报告：
            1. 撰写研究背景和目标
            2. 描述研究方法
            3. 呈现研究结果
            4. 讨论结果的意义
            5. 得出结论和建议
            
            确保报告结构清晰、逻辑严密。
            """,
            agent=self.agents['writer'],
            expected_output="完整的研究报告草稿",
            context=tasks
        )
        tasks.append(task5)
        
        # 任务6：审稿和改进
        await self._broadcast("同行评审专家", "【任务6】我来审核研究成果...")
        task6 = Task(
            description="""
            作为审稿人，全面评审研究成果：
            1. 检查研究的严谨性
            2. 评估结论的合理性
            3. 指出需要改进的地方
            4. 提供修改建议
            
            提供建设性的反馈意见。
            """,
            agent=self.agents['reviewer'],
            expected_output="审稿意见和改进建议",
            context=[task5]
        )
        tasks.append(task6)
        
        return tasks
    
    async def _broadcast(self, agent_name: str, content: str):
        """向前端广播消息"""
        if self.message_callback:
            try:
                await self.message_callback({
                    "type": "agent_message",
                    "data": {
                        "from_agent": self._get_agent_id(agent_name),
                        "agent_name": agent_name,
                        "content": {"message": content},
                        "timestamp": asyncio.get_event_loop().time()
                    }
                })
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
    
    def _get_agent_id(self, agent_name: str) -> str:
        """根据名称获取agent_id"""
        mapping = {
            "首席研究员": "pi_agent",
            "数据科学家": "data_scientist_agent",
            "统计学家": "statistician_agent",
            "可视化专家": "visualizer_agent",
            "科研论文撰写者": "writer_agent",
            "同行评审专家": "reviewer_agent"
        }
        return mapping.get(agent_name, "system")

