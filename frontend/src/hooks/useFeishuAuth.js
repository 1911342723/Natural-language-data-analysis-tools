/**
 * 飞书认证 Hook
 * 处理飞书登录、用户信息获取等
 * 
 * 重要：requestAuthCode 不需要先调用 config 接口鉴权！
 * 参考：https://open.feishu.cn/document/uYjL24iN/uAjMuAjMuAjM
 */
import { useState, useEffect } from 'react';
import { API_BASE_URL, FEISHU_CONFIG } from '../config';

export const useFeishuAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isFeishuEnv, setIsFeishuEnv] = useState(false);

  // 检查登录状态和环境
  useEffect(() => {
    const init = async () => {
      console.log('🔍 初始化应用...');
      
      // 1. 检查 URL 中是否有飞书回调的 code
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      
      if (code) {
        console.log('✅ 检测到飞书回调 code，处理登录...');
        // 清除 URL 中的 code（避免刷新重复处理）
        window.history.replaceState({}, document.title, window.location.pathname);
        await handleAuthCode(code);
        return;
      }
      
      // 2. 检测飞书客户端环境（用于 JSSDK）
      let inFeishu = !!(window.tt || window.h5sdk);
      if (!inFeishu) {
        // 等待 1 秒让 SDK 加载
        await new Promise(resolve => setTimeout(resolve, 1000));
        inFeishu = !!(window.tt || window.h5sdk);
      }
      setIsFeishuEnv(inFeishu);
      console.log('📱 飞书客户端环境:', inFeishu);
      
      // 3. 检查是否已登录（token）
      const token = localStorage.getItem('feishu_token');
      if (token) {
        console.log('✅ 发现本地 token，尝试自动登录...');
        await loadUserInfo();
        return;
      }
      
      // 4. 未登录，结束 loading
      console.log('⚠️ 未登录');
      setLoading(false);
    };
    
    init();
  }, []);

  // 注意：requestAuthCode 不需要 config 鉴权！
  // 根据文档："除了 requestAuthCode、closeWindow、requestAccess API，
  // 其它所有 JSAPI 在页面被调用时，均需要先完成鉴权。"

  // 直接检查登录状态（非飞书环境）
  const checkLoginStatusDirect = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/check_login`, {
        credentials: 'include'
      });
      const data = await response.json();

      if (data.data.logged_in) {
        await loadUserInfo();
      } else {
        console.log('⚠️ 未登录，需要在飞书客户端中打开才能登录');
        setLoading(false);
      }
    } catch (error) {
      console.error('❌ 检查登录状态失败:', error);
      console.log('💡 提示：请确保后端服务已启动');
      setLoading(false);
    }
  };

  // 检查登录状态（飞书环境）
  const checkLoginStatus = async () => {
    try {
      // ⭐ 先检查 localStorage 中是否有 token
      const token = localStorage.getItem('feishu_token');
      
      if (token) {
        console.log('✅ 发现本地 token，尝试自动登录...');
        // 尝试用 token 获取用户信息
        await loadUserInfo();
        return;
      }
      
      console.log('🔍 没有本地 token，检查服务器 session...');
      
      // 没有 token，检查 session
      const response = await fetch(`${API_BASE_URL}/auth/check_login`, {
        credentials: 'include'
      });
      const data = await response.json();

      if (data.data.logged_in) {
        // Session 登录成功，获取完整用户信息
        console.log('✅ Session 有效，获取用户信息...');
        await loadUserInfo();
      } else {
        // 未登录，自动触发登录
        console.log('🔑 未登录，准备自动触发飞书登录...');
        setLoading(false); // 先结束 loading 状态
        
        // 延迟触发登录，给页面一点渲染时间
        setTimeout(() => {
          console.log('🚀 开始触发飞书登录');
          login();
        }, 800);
      }
    } catch (error) {
      console.error('❌ 检查登录状态失败:', error);
      setLoading(false);
      
      // 即使检查失败，也尝试触发登录
      console.log('🔑 检查失败，尝试触发飞书登录...');
      setTimeout(() => {
        login();
      }, 800);
    }
  };

  // 加载用户信息
  const loadUserInfo = async () => {
    try {
      // ⭐ 添加 Authorization header（如果有 token）
      const token = localStorage.getItem('feishu_token');
      const headers = {
        'Content-Type': 'application/json'
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${API_BASE_URL}/auth/current_user`, {
        credentials: 'include',
        headers: headers
      });
      const data = await response.json();

      if (data.code === 0) {
        setUser(data.data);
        console.log('✅ 用户信息加载成功:', data.data.name);
        setLoading(false); // ⭐ 修复：成功后也要设置 loading 为 false
      } else {
        // Token 可能失效，清除并重新登录
        console.warn('⚠️ 用户信息加载失败，清除 token');
        localStorage.removeItem('feishu_token');
        setUser(null);
        setLoading(false);
      }
    } catch (error) {
      console.error('❌ 加载用户信息失败:', error);
      // Token 可能失效，清除
      localStorage.removeItem('feishu_token');
      setUser(null);
      setLoading(false);
    }
  };

  // 飞书登录（支持客户端和浏览器）
  const login = () => {
    console.log('🔑 开始飞书登录...');
    
    // 方案 1：飞书客户端内 - 使用 JSSDK
    if (window.tt) {
      console.log('📱 使用飞书客户端 JSSDK 登录');
      
      if (window.tt.requestAccess) {
        window.tt.requestAccess({
          appID: FEISHU_CONFIG.APP_ID,
          scopeList: [],
          success: async (res) => {
            console.log('✅ JSSDK 授权成功');
            await handleAuthCode(res.code);
          },
          fail: (err) => {
            if (err.errno === 103) {
              callRequestAuthCode();
            } else if (err.errno === 2700002) {
              console.log('❌ 用户拒绝授权');
              setLoading(false);
            } else {
              console.error('❌ 授权失败:', err);
              setLoading(false);
            }
          }
        });
      } else {
        callRequestAuthCode();
      }
      return;
    }
    
    // 方案 2：浏览器 - 使用标准 OAuth 2.0 跳转
    console.log('🌐 使用浏览器 OAuth 登录');
    const redirectUri = encodeURIComponent(window.location.origin + window.location.pathname);
    const state = Math.random().toString(36).substring(7);
    
    // 保存 state 用于验证
    localStorage.setItem('feishu_oauth_state', state);
    
    // 跳转到飞书授权页面
    const authUrl = `https://open.feishu.cn/open-apis/authen/v1/authorize?` +
      `app_id=${FEISHU_CONFIG.APP_ID}` +
      `&redirect_uri=${redirectUri}` +
      `&state=${state}`;
    
    console.log('🔗 跳转到飞书授权页面:', authUrl);
    window.location.href = authUrl;
  };

  // 降级方案：使用 requestAuthCode
  const callRequestAuthCode = () => {
    window.tt.requestAuthCode({
      appId: FEISHU_CONFIG.APP_ID,
      success: async (res) => {
        console.log('✅ requestAuthCode 成功');
        await handleAuthCode(res.code);
      },
      fail: (err) => {
        console.error('❌ requestAuthCode 失败:', err);
        alert(`登录失败: ${JSON.stringify(err)}`);
        setLoading(false);
      }
    });
  };

  // 处理授权码（统一处理）
  const handleAuthCode = async (code) => {
    try {
      console.log('📤 发送授权码到后端...');
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ code })
      });

      const result = await response.json();

      if (result.code === 0) {
        console.log('✅ 登录成功:', result.data.name);
        
        // ⭐ 保存 token 到 localStorage（用于飞书客户端）
        if (result.data.token) {
          localStorage.setItem('feishu_token', result.data.token);
          console.log('✅ Token 已保存到 localStorage');
        }
        
        setUser(result.data);
        
        // 显示成功提示
        if (window.tt && window.tt.showToast) {
          window.tt.showToast({
            title: `欢迎，${result.data.name}`,
            icon: 'success',
            duration: 2000
          });
        }
      } else {
        console.error('❌ 后端登录失败:', result.msg);
        alert(`登录失败: ${result.msg}`);
      }
    } catch (error) {
      console.error('❌ 登录请求异常:', error);
      alert(`登录失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 退出登录
  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });

      // ⭐ 清除 localStorage 中的 token
      localStorage.removeItem('feishu_token');
      
      setUser(null);
      
      if (window.tt) {
        window.tt.showToast({
          title: '已退出登录',
          icon: 'success',
          duration: 2000
        });
      }

      // 重新登录
      setTimeout(() => {
        login();
      }, 1000);
    } catch (error) {
      console.error('❌ 退出登录失败:', error);
      // 即使请求失败，也清除本地 token
      localStorage.removeItem('feishu_token');
      setUser(null);
    }
  };

  return {
    user,
    loading,
    isFeishuEnv,
    login,
    logout,
    refresh: loadUserInfo
  };
};

