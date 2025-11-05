"""
MCP搜索工具 - 格式化搜索结果供Agent使用
"""
import logging
from typing import List, Dict, Any
from .mcp_client import mcp_client
from .dashscope_client import dashscope_client

logger = logging.getLogger(__name__)


async def web_search(query: str, num_results: int = 5) -> str:
    """
    联网搜索并格式化结果（优先使用阿里百炼WebSearch）
    
    Args:
        query: 搜索查询
        num_results: 结果数量
        
    Returns:
        格式化的搜索结果文本
    """
    logger.info(f"🌐 执行网页搜索: {query}")
    
    try:
        # 优先使用阿里百炼WebSearch
        results = await dashscope_client.web_search(query, num_results)
        
        # 如果阿里百炼失败，尝试Serper/Google
        if not results or all(r.get('source') == 'Mock' for r in results):
            logger.info("阿里百炼搜索失败，尝试备用搜索...")
            results = await mcp_client.serper_search(query, num_results)
        
        if not results:
            return f"未找到关于'{query}'的相关结果。"
        
        # 格式化结果
        formatted_results = [f"## 🌐 网页搜索结果：{query}\n"]
        formatted_results.append(f"*搜索引擎：{results[0].get('source', '未知')}*\n")
        
        for idx, result in enumerate(results, 1):
            formatted_results.append(f"\n### {idx}. {result['title']}")
            formatted_results.append(f"**链接**: {result['link']}")
            formatted_results.append(f"\n{result['snippet']}\n")
            formatted_results.append("---")
        
        formatted_results.append(f"\n*共找到 {len(results)} 条结果*")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        logger.error(f"网页搜索失败: {e}")
        return f"搜索时发生错误: {str(e)}"


async def academic_search(query: str, max_results: int = 5) -> str:
    """
    搜索学术文献并格式化结果（优先使用阿里百炼Arxiv）
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        
    Returns:
        格式化的文献结果文本
    """
    logger.info(f"📚 执行学术文献搜索: {query}")
    
    try:
        # 优先使用阿里百炼Arxiv
        results = await dashscope_client.arxiv_search(query, max_results)
        
        # 如果阿里百炼失败，尝试PubMed
        if not results or all(r.get('source') == 'Mock' for r in results):
            logger.info("阿里百炼Arxiv搜索失败，尝试PubMed...")
            results = await mcp_client.pubmed_search(query, max_results)
        
        if not results:
            return f"未找到关于'{query}'的相关文献。"
        
        # 格式化结果
        formatted_results = [f"## 📚 学术文献搜索结果：{query}\n"]
        formatted_results.append(f"*数据库：{results[0].get('source', '未知')}*\n")
        
        for idx, paper in enumerate(results, 1):
            formatted_results.append(f"\n### {idx}. {paper['title']}")
            
            # Arxiv结果
            if 'arxiv_id' in paper:
                formatted_results.append(f"**作者**: {paper['authors']}")
                formatted_results.append(f"**发布日期**: {paper.get('published', 'N/A')}")
                formatted_results.append(f"**Arxiv ID**: {paper['arxiv_id']}")
                formatted_results.append(f"**PDF链接**: {paper['link']}")
                if 'abstract' in paper:
                    formatted_results.append(f"\n**摘要**: {paper['abstract']}\n")
            # PubMed结果
            elif 'pmid' in paper:
                formatted_results.append(f"**作者**: {paper['authors']}")
                formatted_results.append(f"**期刊**: {paper['journal']} ({paper['year']})")
                formatted_results.append(f"**链接**: {paper['link']}")
                formatted_results.append(f"**PMID**: {paper['pmid']}\n")
            
            formatted_results.append("---")
        
        formatted_results.append(f"\n*共找到 {len(results)} 篇文献*")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        logger.error(f"学术搜索失败: {e}")
        return f"搜索时发生错误: {str(e)}"


def format_search_summary(results: List[Dict[str, Any]], query: str) -> str:
    """
    生成搜索结果摘要（用于Agent快速理解）
    
    Args:
        results: 搜索结果列表
        query: 搜索查询
        
    Returns:
        简洁的摘要文本
    """
    if not results:
        return f"未找到关于'{query}'的结果。"
    
    summary = [f"找到{len(results)}条关于'{query}'的结果：\n"]
    
    for idx, result in enumerate(results[:3], 1):  # 只摘要前3条
        title = result.get('title', 'N/A')
        snippet = result.get('snippet', result.get('authors', 'N/A'))
        summary.append(f"{idx}. {title}\n   {snippet[:100]}...")
    
    if len(results) > 3:
        summary.append(f"\n...还有{len(results) - 3}条结果")
    
    return "\n".join(summary)


# 用于测试的原始结果返回函数
async def get_web_search_results(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    获取原始的网页搜索结果（字典列表）
    
    Args:
        query: 搜索查询
        num_results: 结果数量
        
    Returns:
        搜索结果字典列表
    """
    logger.info(f"🌐 执行网页搜索: {query}")
    
    try:
        # 优先使用阿里百炼WebSearch
        results = await dashscope_client.web_search(query, num_results)
        
        # 如果阿里百炼失败，尝试Serper/Google
        if not results or all(r.get('source') == 'Mock' for r in results):
            logger.info("阿里百炼搜索失败，尝试备用搜索...")
            results = await mcp_client.serper_search(query, num_results)
        
        return results
    
    except Exception as e:
        logger.error(f"网页搜索失败: {e}")
        return []


async def get_academic_search_results(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    获取原始的学术搜索结果（字典列表）
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        
    Returns:
        搜索结果字典列表
    """
    logger.info(f"📚 执行学术文献搜索: {query}")
    
    try:
        # 优先使用阿里百炼Arxiv
        results = await dashscope_client.arxiv_search(query, max_results)
        
        # 如果阿里百炼失败，尝试PubMed
        if not results or all(r.get('source') == 'Mock' for r in results):
            logger.info("阿里百炼Arxiv搜索失败，尝试PubMed...")
            results = await mcp_client.pubmed_search(query, max_results)
        
        return results
    
    except Exception as e:
        logger.error(f"学术搜索失败: {e}")
        return []

