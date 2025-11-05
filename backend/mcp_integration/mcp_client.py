"""
MCP客户端 - 统一管理MCP工具调用
"""
import logging
import os
from typing import Dict, Any, Optional, List
import aiohttp
from config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP客户端 - 支持多种搜索和工具调用"""
    
    def __init__(self):
        # 从环境变量读取配置
        self.search_api_key = os.getenv("MCP_SEARCH_API_KEY", "")
        self.search_engine_id = os.getenv("MCP_SEARCH_ENGINE_ID", "")
        self.serper_api_key = os.getenv("SERPER_API_KEY", "")  # Serper.dev API
        
        logger.info("MCP客户端初始化完成")
    
    async def google_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用Google Custom Search API进行搜索
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.search_api_key or not self.search_engine_id:
            logger.warning("Google Search API未配置，返回模拟结果")
            return self._mock_search_results(query)
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.search_api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": num_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_google_results(data)
                    else:
                        logger.error(f"Google搜索失败: {response.status}")
                        return self._mock_search_results(query)
        
        except Exception as e:
            logger.error(f"搜索请求失败: {e}")
            return self._mock_search_results(query)
    
    async def serper_search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用Serper.dev API进行搜索（推荐，更稳定）
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        if not self.serper_api_key:
            logger.warning("Serper API未配置，使用Google搜索")
            return await self.google_search(query, num_results)
        
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": num_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_serper_results(data)
                    else:
                        logger.error(f"Serper搜索失败: {response.status}")
                        return self._mock_search_results(query)
        
        except Exception as e:
            logger.error(f"Serper搜索失败: {e}")
            return self._mock_search_results(query)
    
    async def pubmed_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索PubMed学术文献
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            文献列表
        """
        try:
            # PubMed E-utilities API
            # 1. 搜索获取PMIDs
            search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=search_params, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"PubMed搜索失败: {response.status}")
                        return self._mock_academic_results(query)
                    
                    data = await response.json()
                    pmids = data.get("esearchresult", {}).get("idlist", [])
                    
                    if not pmids:
                        return []
                    
                    # 2. 获取文献详情
                    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                    fetch_params = {
                        "db": "pubmed",
                        "id": ",".join(pmids),
                        "retmode": "json"
                    }
                    
                    async with session.get(fetch_url, params=fetch_params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._parse_pubmed_results(data)
                        else:
                            return self._mock_academic_results(query)
        
        except Exception as e:
            logger.error(f"PubMed搜索失败: {e}")
            return self._mock_academic_results(query)
    
    def _parse_google_results(self, data: Dict) -> List[Dict[str, Any]]:
        """解析Google搜索结果"""
        results = []
        items = data.get("items", [])
        
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "Google"
            })
        
        return results
    
    def _parse_serper_results(self, data: Dict) -> List[Dict[str, Any]]:
        """解析Serper搜索结果"""
        results = []
        organic = data.get("organic", [])
        
        for item in organic:
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "Serper"
            })
        
        return results
    
    def _parse_pubmed_results(self, data: Dict) -> List[Dict[str, Any]]:
        """解析PubMed搜索结果"""
        results = []
        result_data = data.get("result", {})
        
        for pmid, article in result_data.items():
            if pmid == "uids":
                continue
            
            # 提取作者
            authors = article.get("authors", [])
            author_names = [a.get("name", "") for a in authors[:3]]
            author_str = ", ".join(author_names)
            if len(authors) > 3:
                author_str += " et al."
            
            results.append({
                "title": article.get("title", ""),
                "authors": author_str,
                "journal": article.get("fulljournalname", ""),
                "year": article.get("pubdate", "").split()[0] if article.get("pubdate") else "",
                "pmid": pmid,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source": "PubMed"
            })
        
        return results
    
    def _mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """模拟搜索结果（API未配置时使用）"""
        return [
            {
                "title": f"关于'{query}'的最新研究进展",
                "link": "https://example.com/article1",
                "snippet": f"这是关于{query}的详细研究，包含最新的研究成果和方法...",
                "source": "Mock"
            },
            {
                "title": f"{query}的实际应用案例",
                "link": "https://example.com/article2",
                "snippet": f"本文介绍了{query}在实际场景中的应用，取得了显著效果...",
                "source": "Mock"
            },
            {
                "title": f"{query}综述与展望",
                "link": "https://example.com/article3",
                "snippet": f"全面综述{query}领域的研究现状，并展望未来发展方向...",
                "source": "Mock"
            }
        ]
    
    def _mock_academic_results(self, query: str) -> List[Dict[str, Any]]:
        """模拟学术搜索结果"""
        return [
            {
                "title": f"{query}: A Comprehensive Review",
                "authors": "Smith J, Johnson A, et al.",
                "journal": "Nature",
                "year": "2024",
                "pmid": "12345678",
                "link": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                "source": "Mock"
            },
            {
                "title": f"Novel Insights into {query}",
                "authors": "Zhang L, Wang M, et al.",
                "journal": "Cell",
                "year": "2023",
                "pmid": "12345679",
                "link": "https://pubmed.ncbi.nlm.nih.gov/12345679/",
                "source": "Mock"
            },
            {
                "title": f"Mechanisms of {query} in Disease",
                "authors": "Brown R, Davis K, et al.",
                "journal": "Science",
                "year": "2024",
                "pmid": "12345680",
                "link": "https://pubmed.ncbi.nlm.nih.gov/12345680/",
                "source": "Mock"
            }
        ]


# 全局MCP客户端实例
mcp_client = MCPClient()

