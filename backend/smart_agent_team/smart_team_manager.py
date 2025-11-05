"""
智能科研团队管理器 - 灵活的讨论和决策流程
"""
import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from .smart_agent import SmartAgent
from .tools import create_tool_instances

logger = logging.getLogger(__name__)


class SmartScientistTeam:
    """智能科研团队 - 支持动态讨论和决策"""
    
    def __init__(self, message_callback: Callable):
        self.message_callback = message_callback
        self.agents: Dict[str, SmartAgent] = {}
        self.conversation_history = []
        
        # 创建工具
        self.tools = create_tool_instances(message_callback, self)
        
        # 初始化团队成员
        self._create_team_members()
        
        logger.info("✅ 智能科研团队初始化完成")
    
    def _create_team_members(self):
        """创建团队成员"""
        
        # 1. 首席研究员（PI）- 拥有所有工具
        self.agents['pi'] = SmartAgent(
            agent_id="pi_agent",
            name="首席研究员",
            role="项目负责人和协调者",
            expertise="""
- 统筹整个研究项目
- 制定研究计划和策略
- 协调团队成员合作
- 做出关键决策
- 必要时咨询用户意见
""",
            tools=self.tools,  # PI拥有所有工具
            broadcast_callback=self.message_callback
        )
        
        # 2. 数据科学家 - 有代码执行和咨询工具
        self.agents['data_scientist'] = SmartAgent(
            agent_id="data_scientist_agent",
            name="数据科学家",
            role="数据分析专家",
            expertise="""
- 数据清洗和预处理
- 探索性数据分析（EDA）
- 特征工程和数据转换
- 编写Python分析代码
- 使用pandas、numpy等工具
""",
            tools=[t for t in self.tools if t.name in ['execute_python_code', 'search_academic_papers']],
            broadcast_callback=self.message_callback
        )
        
        # 3. 统计学家
        self.agents['statistician'] = SmartAgent(
            agent_id="statistician_agent",
            name="统计学家",
            role="统计分析专家",
            expertise="""
- 统计假设检验
- 回归分析和建模
- 实验设计
- 结果显著性评估
- 统计方法咨询
""",
            tools=[t for t in self.tools if t.name in ['execute_python_code', 'search_academic_papers']],
            broadcast_callback=self.message_callback
        )
        
        # 4. 可视化专家
        self.agents['visualizer'] = SmartAgent(
            agent_id="visualizer_agent",
            name="可视化专家",
            role="数据可视化专家",
            expertise="""
- 设计高质量图表
- 使用matplotlib、seaborn
- 创建出版级别的图表
- 数据故事讲述
- 可视化最佳实践
""",
            tools=[t for t in self.tools if t.name in ['execute_python_code']],
            broadcast_callback=self.message_callback
        )
        
        # 5. 论文撰写者
        self.agents['writer'] = SmartAgent(
            agent_id="writer_agent",
            name="论文撰写者",
            role="学术写作专家",
            expertise="""
- 撰写研究论文
- 组织论文结构
- 学术语言表达
- 文献引用规范
- 论文润色修改
""",
            tools=[t for t in self.tools if t.name in ['search_academic_papers']],
            broadcast_callback=self.message_callback
        )
    
    def get_agent(self, role: str) -> Optional[SmartAgent]:
        """获取指定角色的Agent"""
        return self.agents.get(role)
    
    async def conduct_research(
        self,
        user_input: str,
        data_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        智能研究流程 - PI自主决策，动态调用工具
        
        类似人类科研团队的自然协作：
        - PI 根据课题特点自主决定研究路径
        - 需要数据分析？需要画图？需要文献？由 PI 判断
        - 不强制任何步骤，完全自主决策
        """
        logger.info(f"🚀 PI主导智能研究: {user_input}")
        
        pi_agent = self.agents['pi']
        
        # 研究记忆（累积所有信息）
        research_memory = {
            "topic": user_input,
            "data_info": data_info,
            "literature": "",
            "analysis": [],
            "figures": [],
            "discussions": []
        }
        
        # 创建 Jupyter Session（如果需要代码执行）
        self.session_id = None
        if data_info:
            try:
                from core.jupyter_manager import jupyter_manager
                import json
                self.session_id = await jupyter_manager.create_session(
                    json.dumps(data_info)
                )
                logger.info(f"✅ 创建 Jupyter Session: {self.session_id}")
            except Exception as e:
                logger.warning(f"⚠️ 创建 Jupyter Session 失败: {e}")
        
        await self._broadcast_system_message(
            "首席研究员",
            f"收到课题：**{user_input}**\n\n我会根据课题特点，自主决定研究路径。开始思考..."
        )
        
        # 智能循环：PI自主决策
        max_rounds = 10  # 最多10轮
        literature_search_count = 0  # 文献搜索计数
        
        for round_num in range(1, max_rounds + 1):
            logger.info(f"📍 研究轮次 {round_num}/{max_rounds}")
            
            # PI决策：下一步做什么（像真正的科研工作者一样思考）
            decision_prompt = f"""
你是一位经验丰富的首席研究员，正在领导一个科研项目。

**课题**：{user_input}

**当前进展**：
- 文献搜索：已进行 {literature_search_count} 次 {'（✅已足够）' if literature_search_count >= 2 else '（可继续）'}
- 数据分析：已进行 {len(research_memory['analysis'])} 次
- 图表：已生成 {len(research_memory['figures'])} 个
- 团队讨论：{len(research_memory['discussions'])} 次
- 是否有数据：{'是' if data_info else '否（纯理论研究）'}
- 当前轮次：{round_num}/{max_rounds}

**你的思考（按顺序评估）**：
1. **文献是否足够？** 
   - 如果已搜索 2+ 次 → 文献基础已建立，应进入下一阶段
   - 如果是理论研究 → 1-2 次文献搜索即可，不需要更多

2. **是否需要数据分析或可视化？**
   - 如果有数据 → 考虑执行代码分析
   - 如果是纯理论 → 跳过此步骤

3. **是否需要专家意见？**
   - 对复杂问题咨询统计学家、撰写专家等

4. **是否可以撰写论文？**
   - 文献✓ 且 （有数据分析 或 纯理论）→ 可以开始写了
   - 不要拖延！有足够信息就写

**决策原则**：
- ⚠️ **避免重复**：不要连续做同样的事（如连续搜索文献）
- ⚠️ **高效推进**：理论研究不需要反复搜索，1-2次即可
- ✅ **及时撰写**：信息足够就写论文，不要等到轮次用完

输出格式（只输出JSON）：
```json
{{
  "action": "search_literature|execute_code|consult_expert|write_paper|done",
  "reason": "简短说明为什么现在需要这一步（考虑已完成的工作）",
  "details": "具体要做什么"
}}
```

**提示**：如果文献已搜索2次以上，强烈建议 `write_paper` 或 `consult_expert`！

请决策：
"""
            
            # PI决策
            decision_text = await pi_agent.simple_respond(decision_prompt, "")
            
            # 解析决策
            import json
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', decision_text, re.DOTALL)
            if json_match:
                try:
                    decision = json.loads(json_match.group(1))
                except:
                    decision = {"action": "done", "reason": "无法解析决策"}
            else:
                # 如果没有JSON，尝试直接解析
                try:
                    decision = json.loads(decision_text)
                except:
                    decision = {"action": "done", "reason": "解析失败"}
            
            action = decision.get("action", "done")
            reason = decision.get("reason", "")
            details = decision.get("details", "")
            
            await self._broadcast_system_message(
                "首席研究员",
                f"**第{round_num}轮决策**：{action}\n\n**理由**：{reason}\n\n**计划**：{details}"
            )
            
            # 执行决策
            if action == "search_literature":
                literature_search_count += 1  # 增加计数
                
                from mcp_integration import academic_search
                search_result = await academic_search(user_input, max_results=5)
                research_memory['literature'] = search_result
                await self._broadcast_system_message(
                    "系统",
                    f"📚 文献搜索完成（第{literature_search_count}次）\n\n{search_result[:500]}..."
                )
                
            elif action == "execute_code":
                # 检查是否可以执行代码
                if not self.session_id:
                    await self._broadcast_system_message(
                        "系统",
                        "⚠️ 无法执行代码：未创建 Jupyter Session（可能是纯理论研究）"
                    )
                    continue
                
                # 让数据科学家编写并执行代码
                data_scientist = self.agents['data_scientist']
                code_task = f"""
**任务**：{details}

**要求**：
- 如果需要画图：使用 matplotlib/seaborn，必须调用 plt.show()
- 如果需要数据分析：打印关键结果
- 如果只需要计算：输出结果即可
- 代码简洁实用

只输出代码，格式：
```python
# 你的代码
```

根据实际需求灵活编写，不要为了画图而画图。
"""
                
                await self._broadcast_system_message(
                    "首席研究员",
                    f"💡 安排数据科学家：{details[:100]}..."
                )
                
                code_response = await data_scientist.simple_respond(code_task, "")
                
                # 提取代码
                code_match = re.search(r'```python\s*(.*?)\s*```', code_response, re.DOTALL)
                if code_match:
                    code = code_match.group(1)
                    
                    await self._broadcast_system_message(
                        "数据科学家",
                        f"✅ 代码已编写，正在执行...\n\n```python\n{code}\n```"
                    )
                    
                    # 执行代码（通过 session）
                    from core.jupyter_manager import jupyter_manager
                    session = jupyter_manager.get_session(self.session_id)
                    if not session:
                        await self._broadcast_system_message(
                            "系统",
                            "❌ Session 已失效，无法执行代码"
                        )
                        continue
                    
                    exec_result = await session.execute_code(code, timeout=60)
                    
                    # 格式化输出
                    output_parts = []
                    
                    # 处理文本输出
                    if exec_result.get('stdout'):
                        stdout_text = ''.join(exec_result['stdout'])
                        if stdout_text.strip():
                            output_parts.append(f"**输出**:\n```\n{stdout_text}\n```")
                    
                    # 处理图表
                    charts = []
                    if exec_result.get('data'):
                        for data_item in exec_result['data']:
                            data_content = data_item.get('data', data_item)
                            if 'image/png' in data_content:
                                charts.append({
                                    'type': 'image',
                                    'format': 'png',
                                    'data': data_content['image/png']
                                })
                    
                    if charts:
                        output_parts.append(f"\n**生成了 {len(charts)} 张图表**")
                        research_memory['figures'].extend(charts)
                    
                    # 处理错误
                    if exec_result.get('error'):
                        output_parts.append(f"\n**错误**: {exec_result['error']}")
                    
                    research_memory['analysis'].append({
                        "code": code,
                        "stdout": exec_result.get('stdout', []),
                        "charts": charts,
                        "error": exec_result.get('error')
                    })
                    
                    result_text = "\n\n".join(output_parts) if output_parts else "代码执行完成"
                    
                    await self._broadcast_system_message(
                        "数据科学家",
                        f"执行完成！\n\n{result_text}"
                    )
                    
                    # 如果有图表，特别标注
                    if charts:
                        await self._broadcast_system_message(
                            "系统",
                            f"📊 已生成 {len(charts)} 张图表，可在前端查看"
                        )
                else:
                    await self._broadcast_system_message(
                        "数据科学家",
                        "未能提取到有效代码"
                    )
                
            elif action == "consult_expert":
                # 咨询专家
                expert_role = details.split()[0] if details else "data_scientist"
                expert = self.agents.get(expert_role, self.agents['data_scientist'])
                
                question = f"基于研究课题'{user_input}'，{details}"
                response = await expert.simple_respond(question, "")
                
                research_memory['discussions'].append({
                    "expert": expert.name,
                    "question": question,
                    "response": response
                })
                
                await self._broadcast_system_message(
                    expert.name,
                    f"**我的意见**：\n\n{response[:500]}..."
                )
                
            elif action == "write_paper":
                # 撰写论文（整合所有研究成果）
                writer = self.agents['writer']
                
                # 构建详细的研究总结
                analysis_summary = "\n".join([
                    f"- 分析{i+1}: {a.get('stdout', ['无输出'])[0][:100] if a.get('stdout') else '代码执行'}..."
                    for i, a in enumerate(research_memory['analysis'][:3])  # 最多3条
                ]) if research_memory['analysis'] else "无数据分析"
                
                discussions_summary = "\n".join([
                    f"- {d['expert']}: {d['response'][:100]}..."
                    for d in research_memory['discussions'][:3]  # 最多3条
                ]) if research_memory['discussions'] else "无专家讨论"
                
                paper_task = f"""
**研究课题**：{user_input}

**研究成果汇总**：

1. **文献综述**：
{research_memory['literature'][:800] if research_memory['literature'] else '无文献综述'}

2. **数据分析**（共{len(research_memory['analysis'])}次）：
{analysis_summary}

3. **图表**：共生成 {len(research_memory['figures'])} 张图表

4. **团队讨论**（共{len(research_memory['discussions'])}次）：
{discussions_summary}

**撰写要求**：
基于以上所有成果，撰写一篇完整的研究论文。

**论文结构**：
- Abstract（摘要）
- Introduction（引言，包括背景和研究意义）
- Methods（方法）
- Results（结果，引用图表）
- Discussion（讨论）
- Conclusion（结论）
- References（参考文献）

请以Markdown格式输出，确保逻辑清晰、学术严谨。
"""
                
                await self._broadcast_system_message(
                    "首席研究员",
                    f"✍️ 安排论文撰写者整理所有成果并撰写论文..."
                )
                
                paper = await writer.simple_respond(paper_task, "")
                
                await self._broadcast_system_message(
                    "论文撰写者",
                    paper
                )
                
                await self._broadcast_system_message(
                    "首席研究员",
                    f"🎉 研究完成！\n\n**统计**：\n- 决策轮次：{round_num}\n- 文献搜索：{'✓' if research_memory['literature'] else '✗'}\n- 数据分析：{len(research_memory['analysis'])}次\n- 图表生成：{len(research_memory['figures'])}个\n- 团队讨论：{len(research_memory['discussions'])}次"
                )
                
                return {
                    "status": "completed",
                    "result": paper,
                    "rounds": round_num,
                    "research_summary": {
                        "literature": bool(research_memory['literature']),
                        "analysis_count": len(research_memory['analysis']),
                        "figures_count": len(research_memory['figures']),
                        "discussions_count": len(research_memory['discussions'])
                    },
                    "framework": "SmartAgentTeam"
                }
                
            elif action == "done":
                await self._broadcast_system_message(
                    "首席研究员",
                    f"研究在第{round_num}轮完成。"
                )
                break
        
        # 如果达到最大轮次
        await self._broadcast_system_message(
            "首席研究员",
            f"达到最大轮次({max_rounds})，总结研究成果..."
        )
        
        return {
            "status": "completed",
            "result": "研究过程记录在记忆中",
            "rounds": max_rounds,
            "framework": "SmartAgentTeam"
        }
    
    def _build_context(self, user_input: str, data_info: Optional[Dict]) -> str:
        """构建研究上下文"""
        context_parts = [f"研究课题：{user_input}"]
        
        if data_info:
            context_parts.append(f"\n数据信息：")
            context_parts.append(f"- 行数：{data_info.get('total_rows', 'N/A')}")
            context_parts.append(f"- 列数：{data_info.get('total_columns', 'N/A')}")
            if data_info.get('columns'):
                context_parts.append(f"- 字段：{', '.join(data_info['columns'][:10])}")
        
        return "\n".join(context_parts)
    
    def _describe_data(self, data_info: Optional[Dict]) -> str:
        """描述数据情况"""
        if not data_info:
            return "暂无具体数据，这是理论研究。"
        
        return f"""
- 数据规模：{data_info.get('total_rows', 'N/A')}行 × {data_info.get('total_columns', 'N/A')}列
- 主要字段：{', '.join(data_info.get('columns', [])[:10])}
"""
    
    async def _broadcast_system_message(self, agent_name: str, content: str):
        """广播系统消息"""
        agent_id_map = {
            "首席研究员": "pi_agent",
            "数据科学家": "data_scientist_agent",
            "统计学家": "statistician_agent",
            "可视化专家": "visualizer_agent",
            "论文撰写者": "writer_agent",
            "系统": "system"
        }
        agent_id = agent_id_map.get(agent_name, "system")
        
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": agent_id,
                "agent_name": agent_name,
                "content": {"message": content},
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def handle_user_decision(
        self,
        decision_id: str,
        choice: str,
        feedback: Optional[str] = None
    ):
        """
        处理用户的决策反馈
        
        TODO: 实现决策等待和响应机制
        """
        logger.info(f"📝 收到用户决策: {decision_id} -> {choice}")
        
        # 将用户决策传递给等待的Agent
        # 这需要一个决策队列机制
        pass

