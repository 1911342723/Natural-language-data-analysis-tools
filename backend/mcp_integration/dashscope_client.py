"""
阿里百炼（DashScope）联网搜索客户端
使用 OpenAI 兼容 API + enable_search 参数
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)


class DashScopeMCPClient:
    """阿里百炼联网搜索客户端（使用 OpenAI 兼容 API）"""
    
    def __init__(self):
        # 从配置读取API密钥
        self.api_key = settings.dashscope_api_key
        
        # 使用 OpenAI 兼容模式
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        if self.api_key:
            logger.info(f"✅ 阿里百炼联网搜索客户端初始化完成（OpenAI兼容模式）")
        else:
            logger.warning("⚠️ 阿里百炼 API Key 未配置，搜索功能将返回模拟数据")
    
    async def web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        使用阿里百炼联网搜索（通过模型调用）
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            搜索结果列表
        """
        logger.info(f"🌐 阿里百炼联网搜索: {query}")
        
        if not self.api_key:
            logger.warning("API Key未配置，返回模拟数据")
            return self._mock_web_results(query)
        
        try:
            # 调用模型并启用联网搜索
            completion = await self.client.chat.completions.create(
                model="qwen-plus",  # 支持联网搜索的模型
                messages=[
                    {"role": "user", "content": f"请搜索并总结关于'{query}'的最新信息"}
                ],
                extra_body={
                    "enable_search": True,
                    "search_options": {
                        "forced_search": True,  # 强制搜索
                        "search_strategy": "turbo"  # 快速策略
                    }
                }
            )
            
            # 提取回答
            content = completion.choices[0].message.content
            logger.info(f"✅ 联网搜索完成，返回结果长度: {len(content)} 字符")
            logger.debug(f"搜索结果: {content[:300]}...")
            
            # 将结果格式化为列表
            results = [
                {
                    "title": f"关于'{query}'的搜索结果",
                    "snippet": content,
                    "link": "#",
                    "source": "阿里百炼WebSearch"
                }
            ]
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 联网搜索失败: {e}", exc_info=True)
            return self._mock_web_results(query)
    
    async def arxiv_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索学术论文（通过联网搜索）
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            论文列表
        """
        logger.info(f"📚 阿里百炼Arxiv搜索: {query}")
        
        if not self.api_key:
            logger.warning("API Key未配置，返回模拟数据")
            return self._mock_arxiv_results(query)
        
        try:
            # 调用模型并启用联网搜索
            completion = await self.client.chat.completions.create(
                model="qwen-plus",
                messages=[
                    {"role": "user", "content": f"请搜索关于'{query}'的学术论文，列出标题、作者和摘要"}
                ],
                extra_body={
                    "enable_search": True,
                    "search_options": {
                        "forced_search": True,
                        "search_strategy": "turbo"
                    }
                }
            )
            
            # 提取回答
            content = completion.choices[0].message.content
            logger.info(f"✅ 学术搜索完成，返回结果长度: {len(content)} 字符")
            logger.debug(f"搜索结果: {content[:300]}...")
            
            # 将结果格式化为列表
            results = [
                {
                    "title": f"关于'{query}'的学术论文",
                    "authors": "Various Authors",
                    "abstract": content,
                    "published": "2024",
                    "arxiv_id": "N/A",
                    "link": "#",
                    "source": "阿里百炼Search"
                }
            ]
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 学术搜索失败: {e}", exc_info=True)
            return self._mock_arxiv_results(query)
    
    def _mock_web_results(self, query: str) -> List[Dict[str, Any]]:
        """模拟网页搜索结果"""
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
    
    def _mock_arxiv_results(self, query: str) -> List[Dict[str, Any]]:
        """模拟Arxiv搜索结果"""
        return [
            {
                "title": f"{query}: A Comprehensive Study",
                "authors": "Zhang L, Wang M, et al.",
                "abstract": f"This paper presents a comprehensive study on {query}...",
                "published": "2024-11-05",
                "arxiv_id": "2411.12345",
                "link": "https://arxiv.org/abs/2411.12345",
                "source": "Mock"
            },
            {
                "title": f"Advances in {query}",
                "authors": "Li H, Chen Y, et al.",
                "abstract": f"We propose novel methods for {query}...",
                "published": "2024-10-15",
                "arxiv_id": "2410.67890",
                "link": "https://arxiv.org/abs/2410.67890",
                "source": "Mock"
            }
        ]


# 全局实例
dashscope_client = DashScopeMCPClient()
