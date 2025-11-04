"""
飞书认证 API 路由
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import time
import hashlib
import os

from core.feishu_auth import UserAuth, get_current_user
from core.feishu_db import db

# 从配置中获取飞书配置（使用 FastAPI 的配置管理）
from config import settings

APP_ID = settings.feishu_app_id
APP_SECRET = settings.feishu_app_secret
FEISHU_HOST = settings.feishu_host
NONCE_STR = "Y7a8KkqX041bsSwT"

# 调试：打印配置（注意：生产环境要删除或注释掉）
print(f"🔍 飞书配置检查:")
print(f"   APP_ID: {APP_ID[:20] if APP_ID else 'None'}...")
print(f"   APP_SECRET: {'*' * 20 if APP_SECRET else 'None'}...")
print(f"   FEISHU_HOST: {FEISHU_HOST}")

# 检查配置是否有效
if not APP_ID or not APP_SECRET:
    raise ValueError("❌ 飞书配置缺失！请检查 .env 文件中的 FEISHU_APP_ID 和 FEISHU_APP_SECRET")

# 初始化用户认证
user_auth = UserAuth(APP_ID, APP_SECRET, FEISHU_HOST)

# 创建路由
router = APIRouter(tags=["飞书认证"])


class LoginRequest(BaseModel):
    """登录请求"""
    code: str


class ConfigRequest(BaseModel):
    """JSSDK 配置请求"""
    url: str


@router.post("/login")
async def login(request: Request, data: LoginRequest):
    """
    飞书登录接口
    
    前端通过 tt.requestAuthCode 获取 code 后调用此接口
    """
    try:
        print(f"收到登录请求，code: {data.code[:20]}...")
        
        # 通过 code 获取用户信息
        user_info = user_auth.get_user_info_by_code(data.code)
        
        # 保存到数据库（异步）
        await db.save_user_async(user_info)
        
        # 保存到 session
        if not hasattr(request, "session"):
            raise HTTPException(status_code=500, detail="Session 未初始化")
        
        # 保存到 session（兼容 cookie 认证）
        request.session["user_info"] = user_info
        request.session["login_time"] = time.time()
        
        # 生成 token（用于飞书客户端，因为飞书不支持 cookie）
        import secrets
        import base64
        token = secrets.token_urlsafe(32)
        
        # 将 token 和用户信息存储到内存缓存（简单实现）
        # 生产环境应该用 Redis
        if not hasattr(login, '_token_cache'):
            login._token_cache = {}
        login._token_cache[token] = {
            "user_info": user_info,
            "login_time": time.time()
        }
        
        print(f"✓ 用户登录成功: {user_info.get('name')} ({user_info.get('open_id')})")
        print(f"   Session ID: {id(request.session)}")
        print(f"   Token: {token[:10]}...")
        
        return {
            "code": 0,
            "msg": "登录成功",
            "data": {
                "name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url"),
                "open_id": user_info.get("open_id"),
                "en_name": user_info.get("en_name"),
                "mobile": user_info.get("mobile", ""),
                "email": user_info.get("email", ""),
                "token": token  # ⭐ 返回 token 给前端
            }
        }
        
    except Exception as e:
        print(f"✗ 登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/logout")
async def logout(request: Request):
    """用户登出"""
    if hasattr(request, "session"):
        user_info = request.session.get("user_info")
        if user_info:
            print(f"用户登出: {user_info.get('name')}")
        request.session.clear()
    
    return {"code": 0, "msg": "登出成功"}


@router.get("/current_user")
async def current_user(request: Request, user: dict = Depends(get_current_user)):
    """
    获取当前登录用户信息
    需要登录才能访问
    """
    # 获取用户统计信息（异步）
    stats = await db.get_user_stats_async(user["open_id"])
    
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "open_id": user.get("open_id"),
            "en_name": user.get("en_name"),
            "mobile": user.get("mobile", ""),
            "email": user.get("email", ""),
            "stats": stats
        }
    }


@router.get("/check_login")
async def check_login(request: Request):
    """检查登录状态"""
    if not hasattr(request, "session"):
        return {
            "code": 0,
            "msg": "未登录",
            "data": {"logged_in": False}
        }
    
    user_info = request.session.get("user_info")
    
    if user_info:
        return {
            "code": 0,
            "msg": "已登录",
            "data": {
                "logged_in": True,
                "name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url")
            }
        }
    else:
        return {
            "code": 0,
            "msg": "未登录",
            "data": {"logged_in": False}
        }


@router.get("/get_config_parameters")
async def get_config_parameters(url: str):
    """
    获取 JSSDK 配置参数
    用于前端 JSAPI 鉴权
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="缺少 url 参数")
        
        print(f"收到鉴权请求，URL: {url}")
        
        # 获取 jsapi_ticket
        from core.feishu_auth import UserAuth
        auth = UserAuth(APP_ID, APP_SECRET, FEISHU_HOST)
        
        # 需要先获取 tenant_access_token，然后获取 ticket
        token = auth.get_tenant_access_token()
        
        # 获取 ticket（注意：是 open-apis，不是 open-api）
        ticket_url = f"{FEISHU_HOST}/open-apis/jssdk/ticket/get"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        import requests
        resp = requests.post(url=ticket_url, headers=headers)
        resp.raise_for_status()
        
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取 ticket 失败: {data.get('msg')}")
        
        ticket = data.get("data", {}).get("ticket", "")
        
        # 生成签名
        timestamp = int(time.time()) * 1000
        verify_str = f"jsapi_ticket={ticket}&noncestr={NONCE_STR}&timestamp={timestamp}&url={url}"
        signature = hashlib.sha1(verify_str.encode("utf-8")).hexdigest()
        
        print(f"生成签名: {signature}")
        
        return {
            "appid": APP_ID,
            "signature": signature,
            "noncestr": NONCE_STR,
            "timestamp": timestamp,
        }
        
    except Exception as e:
        print(f"获取配置参数失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    获取用户的分析历史
    需要登录才能访问
    """
    history = await db.get_user_history_async(user["open_id"], limit, offset)
    
    return {
        "code": 0,
        "msg": "success",
        "data": {
            "history": history,
            "total": len(history)
        }
    }


@router.get("/history/{analysis_id}")
async def get_analysis_detail(
    analysis_id: int,
    user: dict = Depends(get_current_user)
):
    """
    获取分析详情
    需要登录才能访问
    """
    detail = await db.get_analysis_detail_async(analysis_id, user["open_id"])
    
    if detail:
        return {
            "code": 0,
            "msg": "success",
            "data": detail
        }
    else:
        raise HTTPException(status_code=404, detail="记录不存在或无权限访问")


@router.delete("/history/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    user: dict = Depends(get_current_user)
):
    """删除分析记录"""
    success = await db.delete_analysis_async(analysis_id, user["open_id"])
    
    if success:
        return {"code": 0, "msg": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="删除失败")

