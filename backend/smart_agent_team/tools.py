"""
科研工具集 - 搜索、分析、协作
"""
import logging
from typing import Dict, Any, Optional, Callable
from langchain.tools import tool
from core.jupyter_manager import jupyter_manager
from mcp_integration import web_search as mcp_web_search
from mcp_integration import academic_search as mcp_academic_search

logger = logging.getLogger(__name__)


class ResearchTools:
    """科研工具集"""
    
    def __init__(self, message_callback: Callable, team_manager=None):
        self.message_callback = message_callback
        self.team_manager = team_manager
        
    def get_all_tools(self):
        """获取所有工具"""
        return [
            self.search_academic_papers,
            self.search_web,
            self.execute_python_code,
            self.ask_colleague,
            self.ask_user_opinion,
        ]
    
    @tool
    async def search_academic_papers(self, query: str) -> str:
        """
        搜索学术论文和文献资料（使用PubMed数据库）
        
        Args:
            query: 搜索关键词，例如"cell communication mechanisms"
            
        Returns:
            搜索结果摘要（Markdown格式）
        """
        logger.info(f"🔍 搜索学术论文: {query}")
        
        # 广播搜索开始消息
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "system",
                "content": {"message": f"🔍 正在PubMed数据库搜索: **{query}**..."},
                "timestamp": ""
            }
        })
        
        # 调用MCP学术搜索
        result = await mcp_academic_search(query, max_results=5)
        
        # 广播搜索完成
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "system",
                "content": {"message": "✅ 文献搜索完成"},
                "timestamp": ""
            }
        })
        
        return result
    
    @tool
    async def search_web(self, query: str) -> str:
        """
        联网搜索最新资讯和数据（使用Google/Serper搜索引擎）
        
        Args:
            query: 搜索关键词
            
        Returns:
            网页搜索结果（Markdown格式）
        """
        logger.info(f"🌐 网页搜索: {query}")
        
        # 广播搜索开始消息
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "system",
                "content": {"message": f"🌐 正在搜索: **{query}**..."},
                "timestamp": ""
            }
        })
        
        # 调用MCP网页搜索
        result = await mcp_web_search(query, num_results=5)
        
        # 广播搜索完成
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "system",
                "content": {"message": "✅ 网页搜索完成"},
                "timestamp": ""
            }
        })
        
        return result
    
    @tool
    async def execute_python_code(self, code: str, description: str = "") -> str:
        """
        执行Python数据分析代码（支持matplotlib画图）
        
        Args:
            code: Python代码
            description: 代码用途说明
            
        Returns:
            执行结果（包括输出和图表）
        """
        logger.info(f"💻 执行代码: {description}")
        
        try:
            # 使用现有的Jupyter管理器
            result = await jupyter_manager.execute_code(code, timeout=30)
            
            output_parts = []
            
            if result.get("output"):
                output_parts.append(f"**输出**:\n```\n{result['output']}\n```")
            
            if result.get("figures"):
                output_parts.append(f"\n**生成了{len(result['figures'])}张图表**")
                for idx, fig_path in enumerate(result['figures']):
                    output_parts.append(f"- 图表{idx+1}: {fig_path}")
            
            if result.get("error"):
                output_parts.append(f"\n**错误**: {result['error']}")
            
            return "\n".join(output_parts) if output_parts else "代码执行完成，无输出"
            
        except Exception as e:
            logger.error(f"代码执行失败: {e}")
            return f"执行失败: {str(e)}"
    
    @tool
    async def ask_colleague(self, colleague_role: str, question: str) -> str:
        """
        向团队中的其他专家咨询问题
        
        Args:
            colleague_role: 专家角色，可选值：
                - "data_scientist" (数据科学家)
                - "statistician" (统计学家)
                - "visualizer" (可视化专家)
                - "writer" (论文撰写者)
            question: 要咨询的问题
            
        Returns:
            专家的回答
        """
        logger.info(f"💬 咨询 {colleague_role}: {question}")
        
        if not self.team_manager:
            return "无法联系团队成员"
        
        # 获取对应的Agent并让其回答
        colleague = self.team_manager.get_agent(colleague_role)
        if not colleague:
            return f"找不到{colleague_role}这个角色"
        
        # 发送消息到前端
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "pi_agent",
                "content": {"message": f"向{colleague.name}咨询：{question}"},
                "timestamp": ""
            }
        })
        
        # 让同事回答
        answer = await colleague.think_and_respond(question, context="")
        return answer
    
    @tool
    async def ask_user_opinion(self, question: str, options: list[str]) -> str:
        """
        向用户征询意见（用于关键决策点）
        
        Args:
            question: 要问用户的问题
            options: 选项列表，例如 ["方案A：使用方法1", "方案B：使用方法2"]
            
        Returns:
            用户的选择和反馈
        """
        from .decision_manager import decision_manager
        
        logger.info(f"❓ 咨询用户: {question}")
        logger.info(f"   选项: {options}")
        
        # 广播决策请求消息（提醒用户）
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "pi_agent",
                "content": {"message": f"🤔 **需要您的意见**\n\n{question}\n\n请在弹出的对话框中选择..."},
                "timestamp": ""
            }
        })
        
        # 请求用户决策（会等待用户响应）
        result = await decision_manager.request_user_decision(
            question=question,
            options=options,
            context={"source": "research_tool"},
            timeout=300  # 5分钟超时
        )
        
        # 格式化响应
        choice = result.get("choice", "")
        feedback = result.get("feedback", "")
        
        response_text = f"用户选择：**{choice}**"
        if feedback:
            response_text += f"\n\n用户反馈：{feedback}"
        
        if result.get("timeout"):
            response_text += "\n\n*（决策超时，使用了默认选项）*"
        
        # 广播用户决策
        await self.message_callback({
            "type": "agent_message",
            "data": {
                "from_agent": "system",
                "content": {"message": f"✅ 收到用户决策\n\n{response_text}"},
                "timestamp": ""
            }
        })
        
        return response_text


def create_tool_instances(message_callback: Callable, team_manager=None):
    """创建工具实例"""
    tools_manager = ResearchTools(message_callback, team_manager)
    return tools_manager.get_all_tools()

