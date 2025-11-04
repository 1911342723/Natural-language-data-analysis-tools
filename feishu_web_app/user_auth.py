"""
飞书用户认证模块
实现基于飞书的免登授权，支持多用户系统
"""
import requests
import time
from functools import wraps
from flask import session, jsonify, request


class UserAuth:
    """用户认证类"""
    
    def __init__(self, app_id, app_secret, feishu_host):
        self.app_id = app_id
        self.app_secret = app_secret
        self.feishu_host = feishu_host
        self.tenant_access_token = None
        self.token_expire_time = 0
    
    def get_tenant_access_token(self):
        """
        获取 tenant_access_token（带缓存）
        """
        # 检查缓存
        if self.tenant_access_token and time.time() < self.token_expire_time:
            return self.tenant_access_token
        
        # 重新获取
        url = f"{self.feishu_host}/open-api/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"获取 token 失败: {result.get('msg')}")
            
            self.tenant_access_token = result.get("tenant_access_token")
            # 设置过期时间（提前5分钟刷新）
            expire_in = result.get("expire", 7200)
            self.token_expire_time = time.time() + expire_in - 300
            
            print(f"✓ 获取 tenant_access_token 成功，有效期: {expire_in}秒")
            return self.tenant_access_token
            
        except Exception as e:
            print(f"✗ 获取 tenant_access_token 失败: {e}")
            raise
    
    def get_user_info_by_code(self, code):
        """
        通过 code 获取用户信息（免登流程）
        
        Args:
            code: 前端通过 tt.requestAuthCode 获取的临时授权码
            
        Returns:
            dict: 用户信息
        """
        token = self.get_tenant_access_token()
        
        # 1. 使用 code 获取 user_access_token
        url = f"{self.feishu_host}/open-api/authen/v1/access_token"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "authorization_code",
            "code": code
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"获取用户 token 失败: {result.get('msg')}")
            
            user_data = result.get("data", {})
            user_access_token = user_data.get("access_token")
            open_id = user_data.get("open_id")
            
            # 2. 使用 user_access_token 获取用户详细信息
            user_info = self.get_user_detail(user_access_token)
            user_info["open_id"] = open_id
            
            return user_info
            
        except Exception as e:
            print(f"✗ 获取用户信息失败: {e}")
            raise
    
    def get_user_detail(self, user_access_token):
        """
        获取用户详细信息
        
        Args:
            user_access_token: 用户访问令牌
            
        Returns:
            dict: 用户详细信息
        """
        url = f"{self.feishu_host}/open-api/authen/v1/user_info"
        headers = {
            "Authorization": f"Bearer {user_access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                raise Exception(f"获取用户详情失败: {result.get('msg')}")
            
            return result.get("data", {})
            
        except Exception as e:
            print(f"✗ 获取用户详情失败: {e}")
            raise


def login_required(f):
    """
    登录验证装饰器
    用于保护需要登录才能访问的接口
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查 session 中是否有用户信息
        if "user_info" not in session:
            return jsonify({
                "code": 401,
                "msg": "未登录，请先登录",
                "data": None
            }), 401
        
        # 检查 session 是否过期（可选）
        login_time = session.get("login_time", 0)
        if time.time() - login_time > 86400:  # 24小时过期
            session.clear()
            return jsonify({
                "code": 401,
                "msg": "登录已过期，请重新登录",
                "data": None
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """
    获取当前登录用户信息
    
    Returns:
        dict: 用户信息，如果未登录返回 None
    """
    return session.get("user_info")

