"""
测试搜索功能
"""
import asyncio
import logging
from mcp_integration.search_tools import get_web_search_results, get_academic_search_results

# 配置日志（使用DEBUG级别查看详细信息）
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_web_search():
    """测试网页搜索"""
    logger.info("=" * 60)
    logger.info("测试网页搜索")
    logger.info("=" * 60)
    
    query = "人工智能最新进展"
    logger.info(f"查询: {query}")
    
    results = await get_web_search_results(query, num_results=3)
    
    logger.info(f"\n搜索结果（共{len(results)}条）:")
    for i, result in enumerate(results, 1):
        logger.info(f"\n{i}. {result.get('title')}")
        logger.info(f"   来源: {result.get('source')}")
        logger.info(f"   链接: {result.get('link')}")
        logger.info(f"   摘要: {result.get('snippet', '')[:100]}...")
    
    return results


async def test_academic_search():
    """测试学术搜索"""
    logger.info("\n" + "=" * 60)
    logger.info("测试学术搜索")
    logger.info("=" * 60)
    
    query = "机器学习"
    logger.info(f"查询: {query}")
    
    results = await get_academic_search_results(query, max_results=3)
    
    logger.info(f"\n搜索结果（共{len(results)}条）:")
    for i, result in enumerate(results, 1):
        logger.info(f"\n{i}. {result.get('title')}")
        logger.info(f"   作者: {result.get('authors', 'N/A')}")
        logger.info(f"   来源: {result.get('source')}")
        logger.info(f"   发表: {result.get('published', 'N/A')}")
        logger.info(f"   链接: {result.get('link')}")
        logger.info(f"   摘要: {result.get('abstract', result.get('snippet', ''))[:100]}...")
    
    return results


async def main():
    """主函数"""
    try:
        # 测试网页搜索
        web_results = await test_web_search()
        
        # 测试学术搜索
        academic_results = await test_academic_search()
        
        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)
        
        web_mock_count = sum(1 for r in web_results if r.get('source') == 'Mock')
        academic_mock_count = sum(1 for r in academic_results if r.get('source') == 'Mock')
        
        logger.info(f"网页搜索: {len(web_results)}条结果, {web_mock_count}条模拟数据")
        logger.info(f"学术搜索: {len(academic_results)}条结果, {academic_mock_count}条模拟数据")
        
        if web_mock_count > 0 or academic_mock_count > 0:
            logger.warning("\n⚠️ 检测到模拟数据，可能的原因：")
            logger.warning("1. API Key 未配置或配置错误")
            logger.warning("2. API 请求失败（网络问题、权限问题等）")
            logger.warning("3. 查询返回空结果")
            logger.warning("\n请检查:")
            logger.warning("- backend/config.py 中的 DASHSCOPE_API_KEY")
            logger.warning("- 或设置环境变量 DASHSCOPE_API_KEY")
        else:
            logger.info("\n✅ 所有搜索功能正常！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

