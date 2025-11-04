/**
 * 飞书多用户登录系统前端代码
 */

// 页面加载完成后执行
window.addEventListener("DOMContentLoaded", function () {
  console.log("页面加载完成，开始初始化");
  init();
});

/**
 * 初始化
 */
function init() {
  // 检查是否在飞书客户端中
  if (!window.h5sdk) {
    console.error("未检测到 h5sdk，请在飞书客户端中打开");
    showError("请在飞书客户端中打开此页面");
    return;
  }

  // JSAPI 鉴权
  apiAuth();
}

/**
 * JSAPI 鉴权
 */
function apiAuth() {
  console.log("开始 JSAPI 鉴权");

  const url = encodeURIComponent(location.href.split("#")[0]);
  console.log("当前页面 URL:", decodeURIComponent(url));

  fetch(`/get_config_parameters?url=${url}`)
    .then((response) => response.json())
    .then((res) => {
      console.log("服务端返回的鉴权参数:", res);

      window.h5sdk.error((err) => {
        console.error("h5sdk error:", JSON.stringify(err));
        showError(`JSSDK 错误: ${JSON.stringify(err)}`);
      });

      // 调用 config 接口进行鉴权
      window.h5sdk.config({
        appId: res.appid,
        timestamp: res.timestamp,
        nonceStr: res.noncestr,
        signature: res.signature,
        jsApiList: [],
        onSuccess: (result) => {
          console.log("JSSDK 鉴权成功:", JSON.stringify(result));
        },
        onFail: (err) => {
          console.error("JSSDK 鉴权失败:", JSON.stringify(err));
          showError(`鉴权失败: ${JSON.stringify(err)}`);
        },
      });

      // JSSDK 环境准备就绪
      window.h5sdk.ready(() => {
        console.log("JSSDK 环境准备就绪");
        
        // 检查登录状态
        checkLoginStatus();
      });
    })
    .catch((error) => {
      console.error("鉴权过程出错:", error);
      showError(`鉴权失败: ${error.message}`);
    });
}

/**
 * 检查登录状态
 */
function checkLoginStatus() {
  console.log("检查登录状态");
  
  fetch("/api/check_login")
    .then((response) => response.json())
    .then((res) => {
      if (res.data.logged_in) {
        console.log("用户已登录:", res.data.name);
        // 获取完整用户信息
        getCurrentUser();
      } else {
        console.log("用户未登录");
        showLoginSection();
      }
    })
    .catch((error) => {
      console.error("检查登录状态失败:", error);
      showLoginSection();
    });
}

/**
 * 获取当前用户信息
 */
function getCurrentUser() {
  fetch("/api/current_user")
    .then((response) => response.json())
    .then((res) => {
      if (res.code === 0) {
        console.log("获取用户信息成功:", res.data);
        showUserInfo(res.data);
      } else {
        console.error("获取用户信息失败:", res.msg);
        showLoginSection();
      }
    })
    .catch((error) => {
      console.error("获取用户信息失败:", error);
      showLoginSection();
    });
}

/**
 * 执行登录
 */
function doLogin() {
  console.log("开始登录流程");
  
  // 调用飞书 JSAPI 获取授权码
  tt.requestAuthCode({
    appId: window.h5sdk.config.appId,
    success: (res) => {
      console.log("获取授权码成功:", res.code);
      
      // 发送授权码到服务端
      fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          code: res.code,
        }),
      })
        .then((response) => response.json())
        .then((result) => {
          if (result.code === 0) {
            console.log("登录成功:", result.data);
            
            tt.showToast({
              title: "登录成功",
              icon: "success",
              duration: 2000,
            });
            
            // 显示用户信息
            showUserInfo(result.data);
          } else {
            console.error("登录失败:", result.msg);
            showError(`登录失败: ${result.msg}`);
          }
        })
        .catch((error) => {
          console.error("登录请求失败:", error);
          showError(`登录失败: ${error.message}`);
        });
    },
    fail: (err) => {
      console.error("获取授权码失败:", JSON.stringify(err));
      showError(`获取授权码失败: ${JSON.stringify(err)}`);
    },
  });
}

/**
 * 退出登录
 */
function logout() {
  console.log("退出登录");
  
  fetch("/api/logout", {
    method: "POST",
  })
    .then((response) => response.json())
    .then((res) => {
      console.log("退出登录成功");
      
      tt.showToast({
        title: "已退出登录",
        icon: "success",
        duration: 2000,
      });
      
      // 显示登录界面
      setTimeout(() => {
        showLoginSection();
      }, 500);
    })
    .catch((error) => {
      console.error("退出登录失败:", error);
    });
}

/**
 * 显示登录界面
 */
function showLoginSection() {
  document.getElementById("loading").style.display = "none";
  document.getElementById("error").style.display = "none";
  document.getElementById("user-section").style.display = "none";
  document.getElementById("login-section").style.display = "block";
}

/**
 * 显示用户信息
 */
function showUserInfo(userInfo) {
  document.getElementById("loading").style.display = "none";
  document.getElementById("error").style.display = "none";
  document.getElementById("login-section").style.display = "none";
  
  if (userInfo.avatar_url) {
    document.getElementById("user-avatar").src = userInfo.avatar_url;
  }
  
  if (userInfo.name) {
    document.getElementById("user-name").textContent = userInfo.name;
  }
  
  if (userInfo.en_name) {
    document.getElementById("user-en-name").textContent = userInfo.en_name;
  }
  
  if (userInfo.open_id) {
    document.getElementById("user-open-id").textContent = userInfo.open_id;
  }
  
  if (userInfo.email) {
    document.getElementById("user-email").textContent = userInfo.email;
    document.getElementById("email-item").style.display = "flex";
  }
  
  document.getElementById("user-section").style.display = "block";
  
  console.log("用户信息已展示");
}

/**
 * 显示错误信息
 */
function showError(message) {
  document.getElementById("loading").style.display = "none";
  
  const errorDiv = document.getElementById("error");
  const errorText = document.getElementById("error-text");
  
  errorText.textContent = message;
  errorDiv.style.display = "block";
}

console.log("auth.js 加载完成");


