"""
飞书用户认证模块 (FastAPI 版本)
实现基于飞书的免登授权，支持多用户系统
"""
import requests
import time
from functools import wraps
from fastapi import HTTPException, Request
from typing import Optional


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
        
        # 重新获取（注意：是 open-apis，不是 open-api）
        url = f"{self.feishu_host}/open-apis/auth/v3/tenant_access_token/internal"
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
        """
        token = self.get_tenant_access_token()
        
        # 1. 使用 code 获取 user_access_token（注意：是 open-apis，不是 open-api）
        url = f"{self.feishu_host}/open-apis/authen/v1/access_token"
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
        """获取用户详细信息"""
        url = f"{self.feishu_host}/open-apis/authen/v1/user_info"
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


# FastAPI 依赖注入函数
async def get_current_user(request: Request) -> Optional[dict]:
    """
    获取当前登录用户（FastAPI 依赖注入）
    
    支持两种认证方式：
    1. Cookie/Session 认证（浏览器）
    2. Token 认证（飞书客户端）
    """
    # 调试：打印请求信息
    print(f"\n🔍 验证用户登录：{request.url.path}")
    print(f"   Request method: {request.method}")
    
    # 方式1: 尝试从 Authorization header 获取 token
    auth_header = request.headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # 移除 "Bearer " 前缀
        print(f"   认证方式: Token")
        print(f"   Token: {token[:10]}...")
        
        # 从 token 缓存中获取用户信息
        from api.auth import login
        if hasattr(login, '_token_cache') and token in login._token_cache:
            token_data = login._token_cache[token]
            
            # 检查是否过期
            if time.time() - token_data["login_time"] > 86400:  # 24小时
                print(f"   ❌ Token 已过期")
                raise HTTPException(status_code=401, detail="登录已过期")
            
            user_info = token_data["user_info"]
            print(f"   ✅ Token 验证成功：{user_info.get('name')}")
            return user_info
        else:
            print(f"   ❌ Token 无效")
            raise HTTPException(status_code=401, detail="未登录或登录已过期")
    
    # 方式2: 尝试从 session/cookie 获取（兼容浏览器）
    print(f"   认证方式: Cookie/Session")
    print(f"   Cookie: {request.headers.get('cookie', 'None')}")
    
    user_info = request.session.get("user_info") if hasattr(request, "session") else None
    
    if not user_info:
        print(f"   ❌ 验证失败：未登录")
        raise HTTPException(status_code=401, detail="未登录")
    
    # 检查 session 是否过期
    login_time = request.session.get("login_time", 0) if hasattr(request, "session") else 0
    if time.time() - login_time > 86400:  # 24小时过期
        print(f"   ❌ 验证失败：登录已过期")
        raise HTTPException(status_code=401, detail="登录已过期")
    
    print(f"   ✅ Session 验证成功：{user_info.get('name')}")
    return user_info


def login_required(func):
    """
    登录验证装饰器（用于非 FastAPI 风格的函数）
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 这个装饰器主要用于兼容性
        # FastAPI 推荐使用 Depends(get_current_user) 方式
        return await func(*args, **kwargs)
    return wrapper

