"""
Visualizer Agent - 可视化专家Agent
负责创建高质量、符合期刊标准的数据可视化
"""
import logging
from typing import Dict, Any, Optional
import json

from multi_agent.base_agent import BaseAgent, MessageType, AgentStatus
from core.ai_client import ai_client
from core.jupyter_manager import jupyter_manager

logger = logging.getLogger(__name__)


class VisualizerAgent(BaseAgent):
    """
    可视化专家Agent
    
    职责：
    - 创建出版级图表（300 DPI）
    - 选择合适的图表类型
    - 优化图表配色和布局
    - 添加统计标注（显著性标记、误差线等）
    - 生成多格式输出（PNG、SVG、PDF）
    - 确保图表符合期刊要求
    """
    
    def __init__(
        self,
        agent_id: str = "visualizer_agent",
        agent_name: str = "可视化专家",
        ai_model: str = "gpt-4o-mini"
    ):
        system_prompt = """你是一位专业的数据可视化专家，擅长创建符合科研期刊标准的高质量图表。

你的职责：
1. 根据数据类型和分析目标选择最佳图表类型
2. 创建出版级质量的图表（300 DPI，符合Nature/Science标准）
3. 优化图表的配色、字体、布局
4. 添加统计标注（p值、显著性星号、误差线等）
5. 确保图表清晰、美观、信息完整

工作原则：
- 清晰：图表信息一目了然
- 美观：配色协调，符合色盲友好原则
- 规范：遵循APA/期刊投稿要求
- 准确：正确表达数据含义

你需要生成Python代码来创建图表，代码会在Jupyter Kernel环境中执行。
数据已加载为pandas DataFrame，变量名为 `df`。
可用的可视化库：
- matplotlib：基础图表
- seaborn：统计图表
- plotly：交互式图表
- 科研级配置：publication-quality settings
"""
        
        super().__init__(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_type="visualizer",
            ai_model=ai_model,
            system_prompt=system_prompt
        )
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理可视化任务
        
        Args:
            task: 任务内容，包含：
                - task_name: 任务名称
                - description: 任务描述
                - session_id: Jupyter Session ID
                - requirements: 具体要求（如chart_type、style、variables等）
                - context: 上下文信息（包含统计结果等）
                
        Returns:
            可视化结果
        """
        task_name = task.get("task_name", "")
        description = task.get("description", "")
        session_id = task.get("session_id")
        requirements = task.get("requirements", {})
        context = task.get("context", {})
        
        logger.info(f"[{self.agent_name}] 开始可视化任务: {task_name}")
        logger.info(f"  描述: {description}")
        logger.info(f"  要求: {requirements}")
        
        try:
            # 生成可视化代码
            self.status = AgentStatus.THINKING
            await self._broadcast_status_update()
            
            code = await self._generate_visualization_code(
                task_name=task_name,
                description=description,
                requirements=requirements,
                context=context
            )
            
            logger.info(f"[{self.agent_name}] 可视化代码已生成")
            logger.debug(f"生成的代码:\n{code}")
            
            # 执行代码
            self.status = AgentStatus.WORKING
            await self._broadcast_status_update()
            
            # 获取Jupyter Session
            session = jupyter_manager.get_session(session_id)
            if not session:
                raise RuntimeError(f"Session不存在: {session_id}")
            
            # 执行代码
            exec_result = await session.execute_code(code, timeout=120)
            
            logger.info(f"[{self.agent_name}] 可视化完成")
            
            # 检查是否有错误
            if exec_result.get("error"):
                logger.error(f"[{self.agent_name}] 执行失败: {exec_result['error']}")
                
                # 尝试修复
                fixed_code = await self._fix_code(
                    original_code=code,
                    error_info=exec_result["error"]
                )
                
                if fixed_code:
                    logger.info(f"[{self.agent_name}] 尝试修复后的代码")
                    exec_result = await session.execute_code(fixed_code, timeout=120)
                    
                    if exec_result.get("error"):
                        return {
                            "status": "failed",
                            "error": exec_result["error"],
                            "code": fixed_code
                        }
            
            # 提取结果
            result = self._extract_visualization_result(exec_result)
            
            logger.info(f"[{self.agent_name}] 可视化任务完成")
            
            return {
                "status": "success",
                "code": code,
                "result": result,
                "execution_output": exec_result
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] 任务执行失败: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_visualization_code(
        self,
        task_name: str,
        description: str,
        requirements: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """生成可视化代码"""
        
        chart_type = requirements.get("chart_type", "auto")
        style = requirements.get("style", "publication")  # publication/presentation/web
        variables = requirements.get("variables", [])
        
        # 构建提示词
        prompt = f"""请生成Python代码来创建高质量的数据可视化。

任务名称：{task_name}
任务描述：{description}

具体要求：
- 图表类型：{chart_type}（auto表示自动选择最佳类型）
- 样式：{style}
- 变量：{', '.join(variables) if variables else '待确定'}

上下文信息：
研究目标：{context.get('research_goal', '未指定')}
统计结果：{context.get('statistical_results', '无')}

环境说明：
- 数据已加载为pandas DataFrame，变量名为 `df`
- 可用库：matplotlib, seaborn, plotly

图表质量要求：
1. DPI: 300（出版级）
2. 尺寸: 合适的宽高比（如单栏图3.5英寸宽，双栏图7英寸宽）
3. 字体: Times New Roman或Arial，大小适中（10-12pt）
4. 配色: 色盲友好的配色方案（如ColorBrewer）
5. 标签: 清晰的轴标签、图例、标题
6. 统计标注: 如果有统计结果，添加显著性标记

代码模板（请根据实际需求调整）：
```python
import matplotlib.pyplot as plt
import seaborn as sns

# 设置出版级图表参数
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['xtick.major.width'] = 1.5
plt.rcParams['ytick.major.width'] = 1.5

# 创建图表
fig, ax = plt.subplots(figsize=(7, 5))

# 绘制数据
# ... 根据数据类型选择合适的图表

# 优化样式
ax.set_xlabel('X Label', fontsize=12, fontweight='bold')
ax.set_ylabel('Y Label', fontsize=12, fontweight='bold')
ax.set_title('Title', fontsize=14, fontweight='bold')

# 显示图表
plt.tight_layout()
plt.show()
```

请生成完整的Python代码，创建符合期刊标准的图表。
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.3)
            
            # 提取代码
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"生成可视化代码失败: {e}", exc_info=True)
            # 返回默认可视化代码
            return """
import matplotlib.pyplot as plt
import seaborn as sns

# 设置出版级参数
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10

# 创建基础图表
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

# 图1：分布图
numeric_cols = df.select_dtypes(include=['number']).columns[:2]
if len(numeric_cols) > 0:
    df[numeric_cols[0]].hist(ax=axes[0], bins=20, edgecolor='black')
    axes[0].set_title(f'Distribution of {numeric_cols[0]}')
    axes[0].set_xlabel(numeric_cols[0])
    axes[0].set_ylabel('Frequency')

# 图2：相关性
if len(numeric_cols) >= 2:
    axes[1].scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6)
    axes[1].set_title('Correlation Plot')
    axes[1].set_xlabel(numeric_cols[0])
    axes[1].set_ylabel(numeric_cols[1])

plt.tight_layout()
plt.show()
"""
    
    async def _fix_code(
        self,
        original_code: str,
        error_info: Dict[str, Any]
    ) -> Optional[str]:
        """修复可视化代码"""
        
        error_msg = error_info.get("ename", "") + ": " + error_info.get("evalue", "")
        traceback = "\n".join(error_info.get("traceback", []))
        
        prompt = f"""以下可视化代码执行失败，请修复它。

原始代码：
```python
{original_code}
```

错误信息：
{error_msg}

堆栈信息：
{traceback}

常见可视化错误：
1. 变量不存在 → 检查列名
2. 数据类型错误 → 转换类型
3. 空数据 → 添加数据检查
4. matplotlib/seaborn参数错误 → 检查API文档
5. 图表尺寸问题 → 调整figsize

请修复代码。只输出修复后的完整代码。
"""
        
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = ai_client.chat(messages, temperature=0.3)
            
            # 提取代码
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                code = response
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"修复可视化代码失败: {e}", exc_info=True)
            return None
    
    def _extract_visualization_result(self, exec_result: Dict[str, Any]) -> Dict[str, Any]:
        """从执行结果中提取可视化结果"""
        
        result = {
            "charts": [],
            "stdout": exec_result.get("stdout", []),
            "stderr": exec_result.get("stderr", [])
        }
        
        # 提取图表
        for data_item in exec_result.get("data", []):
            if "image/png" in data_item:
                result["charts"].append({
                    "type": "image",
                    "format": "png",
                    "data": data_item["image/png"],
                    "quality": "publication"
                })
        
        logger.info(f"[{self.agent_name}] 提取到 {len(result['charts'])} 个图表")
        
        return result

