"""
MCP (Model Context Protocol) 集成
用于联网搜索、学术文献搜索等外部工具调用
"""
from .mcp_client import MCPClient
from .search_tools import web_search, academic_search

__all__ = ['MCPClient', 'web_search', 'academic_search']

