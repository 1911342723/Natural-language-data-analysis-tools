"""
Writer Agent - 论文撰写者Agent
负责撰写科研论文的各个章节
"""
import logging
from typing import Dict, Any, Optional

from multi_agent.base_agent import BaseAgent, MessageType, AgentStatus
from core.ai_client import ai_client

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """
    论文撰写者Agent
    
    职责：
    - 撰写Abstract（摘要）
    - 撰写Introduction（引言）
    - 撰写Methods（方法）
    - 撰写Results（结果）
    - 撰写Discussion（讨论）
    - 撰写Conclusion（结论）
    - 生成References（参考文献）
    """
    
    def __init__(
        self,
        agent_id: str = "writer_agent",
        agent_name: str = "论文撰写者",
        ai_model: str = "gpt-4o-mini"
    ):
        system_prompt = """你是一位经验丰富的科研论文撰写专家，擅长撰写高质量的学术论文。

你的职责：
1. 撰写Abstract：简明扼要地概括研究背景、方法、结果和结论
2. 撰写Introduction：介绍研究背景、文献综述、研究gap和研究目标
3. 撰写Methods：详细描述数据来源、分析方法、统计方法
4. 撰写Results：客观呈现分析结果，引用表格和图表
5. 撰写Discussion：解释结果含义，与前人研究对比，讨论局限性
6. 撰写Conclusion：总结主要发现和研究意义

写作原则：
- 清晰：逻辑清晰，表达准确
- 简洁：避免冗长，直入主题
- 客观：基于数据，避免主观臆断
- 规范：遵循学术写作规范
- 流畅：语言流畅，易于理解

你将根据数据分析结果、统计结果和可视化结果来撰写论文。
"""
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type="writer",
            ai_model=ai_model,
            system_prompt=system_prompt
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理论文撰写任务
        
        Args:
            task: 任务内容，包含：
                - task_name: 任务名称（如"write_abstract", "write_introduction"）
                - description: 任务描述
                - requirements: 具体要求（如section、word_limit等）
                - context: 上下文信息（包含所有分析结果）
                
        Returns:
            论文章节内容
        """
        task_name = task.get("task_name", "")
        description = task.get("description", "")
        requirements = task.get("requirements", {})
        context = task.get("context", {})
        
        logger.info(f"[{self.agent_name}] 开始撰写任务: {task_name}")
        logger.info(f"  描述: {description}")
        
        try:
            self.status = AgentStatus.THINKING
            await self._broadcast_status_update()
            
            # 根据任务类型撰写不同章节
            section = requirements.get("section", "abstract")
            word_limit = requirements.get("word_limit", 300)
            
            content = await self._write_section(
                section=section,
                word_limit=word_limit,
                context=context
            )
            
            self.status = AgentStatus.WORKING
            await self._broadcast_status_update()
            
            logger.info(f"[{self.agent_name}] 撰写完成")
            
            return {
                "status": "success",
                "section": section,
                "content": content,
                "word_count": len(content.split())
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] 任务执行失败: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _write_section(
        self,
        section: str,
        word_limit: int,
        context: Dict[str, Any]
    ) -> str:
        """撰写论文章节"""
        
        # 获取上下文信息
        research_goal = context.get("research_goal", "")
        data_summary = context.get("data_summary", "")
        statistical_results = context.get("statistical_results", "")
        visualization_description = context.get("visualization_description", "")
        
        # 根据章节类型构建不同的提示词
        prompts_map = {
            "abstract": f"""请撰写论文的Abstract（摘要）。

研究目标：{research_goal}
数据概况：{data_summary}
主要发现：{statistical_results}

要求：
1. 字数限制：{word_limit}词以内
2. 包含4个部分：Background, Methods, Results, Conclusion
3. 简明扼要，突出主要发现
4. 使用第三人称，过去时
5. 不要引用参考文献

请直接输出摘要内容，不要包含"Abstract"标题。
""",
            
            "introduction": f"""请撰写论文的Introduction（引言）。

研究目标：{research_goal}

要求：
1. 字数限制：{word_limit}词以内
2. 结构：
   - 研究背景和重要性
   - 文献综述（简要）
   - 研究gap（已有研究的不足）
   - 本研究的目标和贡献
3. 逻辑清晰，由宽到窄
4. 使用现在时描述已知事实，过去时描述前人研究

请直接输出引言内容。
""",
            
            "methods": f"""请撰写论文的Methods（方法）。

研究目标：{research_goal}
数据概况：{data_summary}

要求：
1. 字数限制：{word_limit}词以内
2. 包含：
   - 数据来源和采集方法
   - 数据处理和清洗
   - 分析方法和统计检验
   - 使用的软件和工具
3. 详细到他人可以复现
4. 使用过去时

请直接输出方法部分内容。
""",
            
            "results": f"""请撰写论文的Results（结果）。

研究目标：{research_goal}
统计结果：{statistical_results}
可视化说明：{visualization_description}

要求：
1. 字数限制：{word_limit}词以内
2. 客观呈现结果，不做解释
3. 引用图表（如"如Figure 1所示"、"见Table 1"）
4. 报告统计量和p值
5. 按逻辑顺序组织（从主要到次要）
6. 使用过去时

请直接输出结果部分内容。
""",
            
            "discussion": f"""请撰写论文的Discussion（讨论）。

研究目标：{research_goal}
主要发现：{statistical_results}

要求：
1. 字数限制：{word_limit}词以内
2. 结构：
   - 重述主要发现
   - 解释结果的含义和机制
   - 与前人研究比较（一致/不一致）
   - 讨论局限性
   - 未来研究方向
3. 有深度，有洞察
4. 使用现在时讨论含义

请直接输出讨论部分内容。
""",
            
            "conclusion": f"""请撰写论文的Conclusion（结论）。

研究目标：{research_goal}
主要发现：{statistical_results}

要求：
1. 字数限制：150词以内
2. 简要总结：
   - 主要发现
   - 研究意义
   - 实践启示
3. 简洁有力
4. 与研究目标呼应

请直接输出结论部分内容。
"""
        }
        
        prompt = prompts_map.get(section, prompts_map["abstract"])
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.7)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"撰写章节失败: {e}", exc_info=True)
            return f"[Error] 撰写{section}失败: {str(e)}"

