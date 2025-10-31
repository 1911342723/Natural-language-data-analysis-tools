"""
内存缓存管理
用于存储文件元信息和 Session 信息
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class FileCache:
    """文件元信息缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def set(self, file_id: str, file_info: Dict[str, Any]):
        """
        保存文件信息到缓存
        
        Args:
            file_id: 文件ID
            file_info: 文件元信息，包含：
                - file_id: str
                - file_name: str
                - file_size: int
                - total_rows: int
                - total_columns: int
                - columns: List[Dict]
                - preview: List[Dict]
                - data_json: str  # 完整数据JSON
        """
        self._cache[file_id] = file_info
        logger.info(f"文件信息已缓存: {file_id}, 文件名: {file_info.get('file_name')}")
    
    def get(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        return self._cache.get(file_id)
    
    def delete(self, file_id: str):
        """删除文件信息"""
        if file_id in self._cache:
            del self._cache[file_id]
            logger.info(f"文件信息已删除: {file_id}")
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("文件缓存已清空")
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class SessionCache:
    """Session 信息缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def set(self, session_id: str, session_info: Dict[str, Any]):
        """
        保存 Session 信息
        
        Args:
            session_id: Session ID
            session_info: Session 信息，包含：
                - session_id: str
                - file_id: str
                - selected_columns: List[str]
                - created_at: datetime
        """
        self._cache[session_id] = session_info
        logger.info(f"Session 信息已缓存: {session_id}")
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取 Session 信息"""
        return self._cache.get(session_id)
    
    def delete(self, session_id: str):
        """删除 Session 信息"""
        if session_id in self._cache:
            del self._cache[session_id]
            logger.info(f"Session 信息已删除: {session_id}")
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("Session 缓存已清空")


# 全局缓存实例
file_cache = FileCache()
session_cache = SessionCache()


