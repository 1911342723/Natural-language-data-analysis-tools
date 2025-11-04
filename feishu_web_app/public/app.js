/**
 * 数据分析工具 - 前端主程序
 * 支持自动登录、导航栏用户头像展示
 */

let currentUser = null;
let userStats = null;

// 页面加载完成后执行
window.addEventListener("DOMContentLoaded", function () {
  console.log("📱 页面加载完成，开始初始化");
  init();
});

/**
 * 初始化应用
 */
async function init() {
  // 检查是否在飞书客户端中
  if (!window.h5sdk) {
    console.error("❌ 未检测到 h5sdk，请在飞书客户端中打开");
    showError("请在飞书客户端中打开此应用");
    return;
  }

  console.log("✅ 检测到飞书环境");

  // 先进行 JSSDK 鉴权
  await apiAuth();
}

/**
 * JSAPI 鉴权
 */
async function apiAuth() {
  console.log("🔐 开始 JSSDK 鉴权");

  const url = encodeURIComponent(location.href.split("#")[0]);
  console.log("📍 当前 URL:", decodeURIComponent(url));

  try {
    const response = await fetch(`/get_config_parameters?url=${url}`);
    const res = await response.json();

    console.log("✅ 获取到鉴权参数");

    // 错误处理
    window.h5sdk.error((err) => {
      console.error("❌ JSSDK 错误:", err);
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
        console.log("✅ JSSDK 鉴权成功");
      },
      onFail: (err) => {
        console.error("❌ JSSDK 鉴权失败:", err);
        showError(`鉴权失败: ${JSON.stringify(err)}`);
      },
    });

    // JSSDK 环境准备就绪
    window.h5sdk.ready(() => {
      console.log("✅ JSSDK 环境准备就绪");

      // 检查登录状态
      checkLoginStatus();
    });
  } catch (error) {
    console.error("❌ 鉴权过程出错:", error);
    showError(`鉴权失败: ${error.message}`);
  }
}

/**
 * 检查登录状态
 */
async function checkLoginStatus() {
  console.log("👤 检查登录状态");

  try {
    const response = await fetch("/api/check_login");
    const res = await response.json();

    if (res.data.logged_in) {
      console.log("✅ 用户已登录:", res.data.user.name);
      await loadUserInfo();
      showAppContent();
    } else {
      console.log("❌ 用户未登录");
      // 自动触发登录
      setTimeout(() => {
        showLoginPrompt();
        // 3秒后自动登录
        setTimeout(() => {
          doLogin();
        }, 1500);
      }, 500);
    }
  } catch (error) {
    console.error("❌ 检查登录状态失败:", error);
    showLoginPrompt();
  }
}

/**
 * 执行登录
 */
function doLogin() {
  console.log("🔑 开始登录流程");

  if (!window.tt) {
    alert("请在飞书客户端中打开");
    return;
  }

  // 显示加载状态
  showLoading("正在登录...");

  // 调用飞书 JSAPI 获取授权码
  tt.requestAuthCode({
    appId: window.h5sdk.config.appId,
    success: async (res) => {
      console.log("✅ 获取授权码成功");

      try {
        // 发送授权码到服务端
        const response = await fetch("/api/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            code: res.code,
          }),
        });

        const result = await response.json();

        if (result.code === 0) {
          console.log("✅ 登录成功:", result.data.name);

          // 显示成功提示
          tt.showToast({
            title: `欢迎，${result.data.name}`,
            icon: "success",
            duration: 2000,
          });

          // 加载用户信息
          await loadUserInfo();

          // 显示应用内容
          setTimeout(() => {
            showAppContent();
          }, 500);
        } else {
          console.error("❌ 登录失败:", result.msg);
          showError(`登录失败: ${result.msg}`);
        }
      } catch (error) {
        console.error("❌ 登录请求失败:", error);
        showError(`登录失败: ${error.message}`);
      }
    },
    fail: (err) => {
      console.error("❌ 获取授权码失败:", err);
      showError(`获取授权码失败: ${JSON.stringify(err)}`);
    },
  });
}

/**
 * 加载用户信息
 */
async function loadUserInfo() {
  try {
    const response = await fetch("/api/current_user");
    const res = await response.json();

    if (res.code === 0) {
      currentUser = res.data;
      userStats = res.data.stats;

      // 更新导航栏
      updateNavbar();

      // 更新欢迎信息
      updateWelcome();

      // 加载最近分析
      loadRecentAnalysis();

      console.log("✅ 用户信息加载完成");
    }
  } catch (error) {
    console.error("❌ 加载用户信息失败:", error);
  }
}

/**
 * 更新导航栏
 */
function updateNavbar() {
  // 隐藏登录按钮，显示用户信息
  document.getElementById("login-button-container").style.display = "none";
  document.getElementById("user-info-container").style.display = "flex";

  // 设置头像
  if (currentUser.avatar_url) {
    document.getElementById("user-avatar-nav").src = currentUser.avatar_url;
    document.getElementById("user-avatar-menu").src = currentUser.avatar_url;
  }

  // 设置用户名
  document.getElementById("user-name-nav").textContent = currentUser.name;
  document.getElementById("user-name-menu").textContent = currentUser.name;

  // 设置邮箱
  if (currentUser.email) {
    document.getElementById("user-email-menu").textContent = currentUser.email;
  }

  // 设置统计信息
  if (userStats) {
    document.getElementById("analysis-count").textContent = userStats.total_analysis || 0;
  }
}

/**
 * 更新欢迎信息
 */
function updateWelcome() {
  document.getElementById("welcome-user-name").textContent = currentUser.name;

  if (userStats) {
    document.getElementById("stat-total").textContent = userStats.total_analysis || 0;
    document.getElementById("stat-success").textContent = userStats.success_count || 0;
    document.getElementById("stat-files").textContent = userStats.file_count || 0;
  }
}

/**
 * 加载最近分析
 */
async function loadRecentAnalysis() {
  try {
    const response = await fetch("/api/history?limit=5");
    const res = await response.json();

    if (res.code === 0 && res.data.history.length > 0) {
      const list = document.getElementById("recent-list");
      list.innerHTML = "";

      res.data.history.forEach((item) => {
        const div = document.createElement("div");
        div.className = "recent-item";
        div.innerHTML = `
          <div class="recent-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 18h6v-6H3v6zm8 0h6V6h-6v12zm8 0h6v-9h-6v9z"/>
            </svg>
          </div>
          <div class="recent-info">
            <div class="recent-query">${item.query || "未知查询"}</div>
            <div class="recent-meta">
              <span>${new Date(item.created_at).toLocaleString()}</span>
              <span class="status-${item.status}">${item.status === "success" ? "成功" : "失败"}</span>
            </div>
          </div>
          <button class="recent-action" onclick="restoreAnalysis(${item.id})">
            查看
          </button>
        `;
        list.appendChild(div);
      });
    }
  } catch (error) {
    console.error("加载最近分析失败:", error);
  }
}

/**
 * 恢复分析
 */
async function restoreAnalysis(id) {
  console.log("恢复分析:", id);
  // 这里实现恢复分析的逻辑
  tt.showToast({
    title: "正在加载分析结果...",
    icon: "loading",
  });
}

/**
 * 退出登录
 */
async function logout() {
  try {
    await fetch("/api/logout", { method: "POST" });

    tt.showToast({
      title: "已退出登录",
      icon: "success",
      duration: 2000,
    });

    // 刷新页面
    setTimeout(() => {
      location.reload();
    }, 1000);
  } catch (error) {
    console.error("退出登录失败:", error);
  }
}

/**
 * 切换用户菜单
 */
function toggleUserMenu() {
  const menu = document.getElementById("user-menu");
  if (menu.style.display === "none" || !menu.style.display) {
    menu.style.display = "block";
  } else {
    menu.style.display = "none";
  }
}

// 点击其他地方关闭菜单
document.addEventListener("click", function (e) {
  if (!e.target.closest(".user-dropdown") && !e.target.closest(".user-menu")) {
    const menu = document.getElementById("user-menu");
    if (menu) {
      menu.style.display = "none";
    }
  }
});

/**
 * UI 状态切换函数
 */
function showLoading(text = "加载中...") {
  document.getElementById("loading-screen").style.display = "flex";
  document.querySelector(".loading-text").textContent = text;
  document.getElementById("login-prompt").style.display = "none";
  document.getElementById("app-content").style.display = "none";
}

function showLoginPrompt() {
  document.getElementById("loading-screen").style.display = "none";
  document.getElementById("login-prompt").style.display = "flex";
  document.getElementById("app-content").style.display = "none";
  document.getElementById("login-button-container").style.display = "block";
}

function showAppContent() {
  document.getElementById("loading-screen").style.display = "none";
  document.getElementById("login-prompt").style.display = "none";
  document.getElementById("app-content").style.display = "block";
}

function showError(message) {
  alert(message);
  showLoginPrompt();
}

/**
 * 快速操作函数
 */
function uploadFile() {
  tt.showToast({ title: "上传文件功能开发中..." });
}

function newAnalysis() {
  tt.showToast({ title: "新建分析功能开发中..." });
}

function showHistory() {
  tt.showToast({ title: "历史记录功能开发中..." });
}

function showFiles() {
  tt.showToast({ title: "文件管理功能开发中..." });
}

function showTemplates() {
  tt.showToast({ title: "分析模板功能开发中..." });
}

function showSettings() {
  tt.showToast({ title: "设置功能开发中..." });
}

console.log("✅ app.js 加载完成");


