"""
数据库模块
用于存储用户的分析历史和会话状态
"""
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path="feishu_app.db"):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    open_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    en_name TEXT,
                    avatar_url TEXT,
                    email TEXT,
                    mobile TEXT,
                    department TEXT,
                    is_active INTEGER DEFAULT 1,
                    first_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 分析历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    query TEXT NOT NULL,
                    result TEXT,
                    result_type TEXT,
                    file_name TEXT,
                    chart_type TEXT,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(open_id)
                )
            """)
            
            # 用户会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    session_id TEXT UNIQUE NOT NULL,
                    session_data TEXT,
                    file_uploads TEXT,
                    current_context TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(open_id)
                )
            """)
            
            # 文件上传记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    table_name TEXT,
                    columns TEXT,
                    row_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(open_id)
                )
            """)
            
            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_analysis_user 
                ON analysis_history(user_id, created_at DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user 
                ON user_sessions(user_id, is_active)
            """)
            
            print("✓ 数据库初始化完成")
    
    # ==================== 用户管理 ====================
    
    def save_user(self, user_info):
        """
        保存或更新用户信息
        
        Args:
            user_info: 用户信息字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 检查用户是否存在
            cursor.execute(
                "SELECT id FROM users WHERE open_id = ?",
                (user_info.get("open_id"),)
            )
            existing = cursor.fetchone()
            
            if existing:
                # 更新用户信息
                cursor.execute("""
                    UPDATE users SET
                        name = ?,
                        en_name = ?,
                        avatar_url = ?,
                        email = ?,
                        mobile = ?,
                        last_login_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE open_id = ?
                """, (
                    user_info.get("name"),
                    user_info.get("en_name"),
                    user_info.get("avatar_url"),
                    user_info.get("email"),
                    user_info.get("mobile"),
                    user_info.get("open_id")
                ))
                print(f"✓ 更新用户信息: {user_info.get('name')}")
            else:
                # 插入新用户
                cursor.execute("""
                    INSERT INTO users (
                        open_id, name, en_name, avatar_url, email, mobile
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_info.get("open_id"),
                    user_info.get("name"),
                    user_info.get("en_name"),
                    user_info.get("avatar_url"),
                    user_info.get("email"),
                    user_info.get("mobile")
                ))
                print(f"✓ 新增用户: {user_info.get('name')}")
    
    def get_user(self, open_id):
        """
        获取用户信息
        
        Args:
            open_id: 用户 open_id
            
        Returns:
            dict: 用户信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE open_id = ? AND is_active = 1",
                (open_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== 分析历史管理 ====================
    
    def save_analysis(self, user_id, query, result=None, **kwargs):
        """
        保存分析记录
        
        Args:
            user_id: 用户 open_id
            query: 用户查询内容
            result: 分析结果
            **kwargs: 其他参数（result_type, file_name等）
            
        Returns:
            int: 记录 ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            result_json = json.dumps(result, ensure_ascii=False) if result else None
            
            cursor.execute("""
                INSERT INTO analysis_history (
                    user_id, session_id, query, result, result_type,
                    file_name, chart_type, status, error_message, execution_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                kwargs.get("session_id"),
                query,
                result_json,
                kwargs.get("result_type"),
                kwargs.get("file_name"),
                kwargs.get("chart_type"),
                kwargs.get("status", "success"),
                kwargs.get("error_message"),
                kwargs.get("execution_time")
            ))
            
            return cursor.lastrowid
    
    def get_user_history(self, user_id, limit=50, offset=0):
        """
        获取用户的分析历史
        
        Args:
            user_id: 用户 open_id
            limit: 返回条数
            offset: 偏移量
            
        Returns:
            list: 历史记录列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, query, result_type, file_name, chart_type,
                    status, created_at, execution_time
                FROM analysis_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_analysis_detail(self, analysis_id, user_id):
        """
        获取分析详情
        
        Args:
            analysis_id: 分析记录 ID
            user_id: 用户 open_id（用于权限验证）
            
        Returns:
            dict: 分析详情
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analysis_history
                WHERE id = ? AND user_id = ?
            """, (analysis_id, user_id))
            
            row = cursor.fetchone()
            if row:
                data = dict(row)
                # 解析 JSON 结果
                if data.get("result"):
                    try:
                        data["result"] = json.loads(data["result"])
                    except:
                        pass
                return data
            return None
    
    def delete_analysis(self, analysis_id, user_id):
        """
        删除分析记录
        
        Args:
            analysis_id: 分析记录 ID
            user_id: 用户 open_id（用于权限验证）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM analysis_history
                WHERE id = ? AND user_id = ?
            """, (analysis_id, user_id))
            
            return cursor.rowcount > 0
    
    # ==================== 会话管理 ====================
    
    def save_session_context(self, user_id, session_id, context_data):
        """
        保存用户会话上下文
        
        Args:
            user_id: 用户 open_id
            session_id: 会话 ID
            context_data: 上下文数据（字典）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            context_json = json.dumps(context_data, ensure_ascii=False)
            
            # 检查会话是否存在
            cursor.execute(
                "SELECT id FROM user_sessions WHERE session_id = ?",
                (session_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE user_sessions SET
                        session_data = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (context_json, session_id))
            else:
                cursor.execute("""
                    INSERT INTO user_sessions (
                        user_id, session_id, session_data
                    ) VALUES (?, ?, ?)
                """, (user_id, session_id, context_json))
    
    def get_session_context(self, session_id):
        """
        获取会话上下文
        
        Args:
            session_id: 会话 ID
            
        Returns:
            dict: 上下文数据
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_data FROM user_sessions
                WHERE session_id = ? AND is_active = 1
            """, (session_id,))
            
            row = cursor.fetchone()
            if row and row["session_data"]:
                try:
                    return json.loads(row["session_data"])
                except:
                    pass
            return {}
    
    # ==================== 文件管理 ====================
    
    def save_file_upload(self, user_id, file_info):
        """
        保存文件上传记录
        
        Args:
            user_id: 用户 open_id
            file_info: 文件信息字典
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            columns_json = json.dumps(file_info.get("columns", []), ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO file_uploads (
                    user_id, file_name, file_path, file_size,
                    file_type, table_name, columns, row_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                file_info.get("file_name"),
                file_info.get("file_path"),
                file_info.get("file_size"),
                file_info.get("file_type"),
                file_info.get("table_name"),
                columns_json,
                file_info.get("row_count")
            ))
            
            return cursor.lastrowid
    
    def get_user_files(self, user_id):
        """
        获取用户上传的文件列表
        
        Args:
            user_id: 用户 open_id
            
        Returns:
            list: 文件列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM file_uploads
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            result = []
            for row in rows:
                data = dict(row)
                # 解析 columns
                if data.get("columns"):
                    try:
                        data["columns"] = json.loads(data["columns"])
                    except:
                        pass
                result.append(data)
            return result
    
    # ==================== 统计信息 ====================
    
    def get_user_stats(self, user_id):
        """
        获取用户统计信息
        
        Args:
            user_id: 用户 open_id
            
        Returns:
            dict: 统计信息
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总分析次数
            cursor.execute("""
                SELECT COUNT(*) as total FROM analysis_history
                WHERE user_id = ?
            """, (user_id,))
            total_analysis = cursor.fetchone()["total"]
            
            # 成功次数
            cursor.execute("""
                SELECT COUNT(*) as success FROM analysis_history
                WHERE user_id = ? AND status = 'success'
            """, (user_id,))
            success_count = cursor.fetchone()["success"]
            
            # 上传文件数
            cursor.execute("""
                SELECT COUNT(*) as files FROM file_uploads
                WHERE user_id = ?
            """, (user_id,))
            file_count = cursor.fetchone()["files"]
            
            # 最近活动时间
            cursor.execute("""
                SELECT MAX(created_at) as last_activity FROM analysis_history
                WHERE user_id = ?
            """, (user_id,))
            last_activity = cursor.fetchone()["last_activity"]
            
            return {
                "total_analysis": total_analysis,
                "success_count": success_count,
                "file_count": file_count,
                "last_activity": last_activity
            }


# 全局数据库实例
db = Database()

