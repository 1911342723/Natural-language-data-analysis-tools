"""
飞书网页应用鉴权模块
负责获取 tenant_access_token 和 jsapi_ticket
"""
import requests
import os


# API 端点配置
TENANT_ACCESS_TOKEN_URI = "/open-api/auth/v3/tenant_access_token/internal"
JSAPI_TICKET_URI = "/open-api/jssdk/ticket/get"


class Auth:
    """
    飞书鉴权类
    用于获取 tenant_access_token 和 jsapi_ticket
    """

    def __init__(self, app_id, app_secret, feishu_host):
        """
        初始化鉴权对象
        
        Args:
            app_id: 飞书应用的 App ID
            app_secret: 飞书应用的 App Secret
            feishu_host: 飞书开放平台地址
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.feishu_host = feishu_host
        self.tenant_access_token = ""

    def authorize_tenant_access_token(self):
        """
        获取 tenant_access_token
        
        基于开放平台能力实现，具体参考文档：
        https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        
        Returns:
            str: tenant_access_token
        """
        url = f"{self.feishu_host}{TENANT_ACCESS_TOKEN_URI}"
        req_body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=req_body)
            self._check_error_response(response)
            
            data = response.json()
            self.tenant_access_token = data.get("tenant_access_token", "")
            
            if not self.tenant_access_token:
                raise Exception("Failed to get tenant_access_token")
            
            print(f"✓ 成功获取 tenant_access_token")
            return self.tenant_access_token
            
        except Exception as e:
            print(f"✗ 获取 tenant_access_token 失败: {str(e)}")
            raise

    def get_ticket(self):
        """
        获取 jsapi_ticket
        
        具体参考文档：
        https://open.feishu.cn/document/ukTMukTMukTM/uYTM5UjL2ETO14iNxkTN/h5_js_sdk/authorization
        
        Returns:
            str: jsapi_ticket
        """
        # 先获取 tenant_access_token
        self.authorize_tenant_access_token()
        
        url = f"{self.feishu_host}{JSAPI_TICKET_URI}"
        headers = {
            "Authorization": f"Bearer {self.tenant_access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(url=url, headers=headers)
            self._check_error_response(response)
            
            data = response.json()
            ticket = data.get("data", {}).get("ticket", "")
            
            if not ticket:
                raise Exception("Failed to get jsapi_ticket")
            
            print(f"✓ 成功获取 jsapi_ticket")
            return ticket
            
        except Exception as e:
            print(f"✗ 获取 jsapi_ticket 失败: {str(e)}")
            raise

    @staticmethod
    def _check_error_response(resp):
        """
        检查 API 响应是否有错误
        
        Args:
            resp: requests.Response 对象
            
        Raises:
            Exception: 当 API 返回错误时抛出异常
        """
        if resp.status_code != 200:
            raise Exception(
                f"HTTP 请求失败: status_code={resp.status_code}, "
                f"response={resp.text}"
            )
        
        data = resp.json()
        code = data.get("code", -1)
        
        if code != 0:
            msg = data.get("msg", "unknown error")
            raise Exception(f"API 返回错误: code={code}, msg={msg}")


