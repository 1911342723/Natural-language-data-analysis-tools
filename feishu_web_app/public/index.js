/**
 * 飞书网页应用前端交互代码
 * 负责 JSSDK 鉴权和调用 JSAPI
 */

// 页面加载完成后执行
window.addEventListener("DOMContentLoaded", function () {
  console.log("页面加载完成，开始初始化");
  apiAuth();
});

/**
 * JSAPI 鉴权函数
 */
function apiAuth() {
  console.log("开始 JSAPI 鉴权");

  // 检查是否在飞书客户端中
  if (!window.h5sdk) {
    console.error("未检测到 h5sdk，请在飞书客户端中打开");
    showError("请在飞书客户端中打开此页面");
    return;
  }

  // 获取当前网页 URL
  // 注意：这里必须使用这种方式获取，不要手写 URL
  const url = encodeURIComponent(location.href.split("#")[0]);
  console.log("当前页面 URL:", decodeURIComponent(url));

  // 向服务端请求鉴权参数
  fetch(`/get_config_parameters?url=${url}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((res) => {
      console.log("服务端返回的鉴权参数:", res);

      // 检查返回的参数是否完整
      if (!res.appid || !res.signature || !res.noncestr || !res.timestamp) {
        throw new Error("服务端返回的鉴权参数不完整");
      }

      // 通过 error 接口处理 API 验证失败后的回调
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
        jsApiList: [], // 需要使用的 JSAPI 列表，为空表示所有
        // 鉴权成功回调
        onSuccess: (result) => {
          console.log("鉴权成功:", JSON.stringify(result));
        },
        // 鉴权失败回调
        onFail: (err) => {
          console.error("鉴权失败:", JSON.stringify(err));
          showError(`鉴权失败: ${JSON.stringify(err)}`);
        },
      });

      // 完成鉴权后，在 h5sdk.ready 里调用 JSAPI
      window.h5sdk.ready(() => {
        console.log("JSSDK 环境准备就绪");

        // 调用 showToast 显示提示
        tt.showToast({
          title: "鉴权成功",
          icon: "success",
          duration: 2000,
        });

        // 获取用户信息
        getUserInfo();
      });
    })
    .catch((error) => {
      console.error("鉴权过程出错:", error);
      showError(`鉴权失败: ${error.message}`);
    });
}

/**
 * 获取用户信息
 */
function getUserInfo() {
  console.log("开始获取用户信息");

  // 调用 getUserInfo API
  // 文档：https://open.feishu.cn/document/uYjL24iN/ucjMx4yNyEjL3ITM
  tt.getUserInfo({
    success: (res) => {
      console.log("获取用户信息成功:", JSON.stringify(res));
      showUserInfo(res.userInfo);
    },
    fail: (err) => {
      console.error("获取用户信息失败:", JSON.stringify(err));
      showError(`获取用户信息失败: ${JSON.stringify(err)}`);
    },
  });
}

/**
 * 显示用户信息
 */
function showUserInfo(userInfo) {
  // 隐藏加载状态
  document.getElementById("loading").style.display = "none";

  // 显示用户信息卡片
  document.getElementById("user-info").style.display = "block";

  // 填充用户信息
  if (userInfo.avatarUrl) {
    document.getElementById("user-avatar").src = userInfo.avatarUrl;
  }

  if (userInfo.name) {
    document.getElementById("user-name").textContent = userInfo.name;
  }

  if (userInfo.enName) {
    document.getElementById("user-en-name").textContent = userInfo.enName;
  }

  if (userInfo.openId) {
    document.getElementById("user-open-id").textContent = userInfo.openId;
  }

  console.log("用户信息已展示");
}

/**
 * 显示错误信息
 */
function showError(message) {
  // 隐藏加载状态
  document.getElementById("loading").style.display = "none";

  // 显示错误信息
  const errorDiv = document.getElementById("error");
  const errorText = document.getElementById("error-text");

  errorText.textContent = message;
  errorDiv.style.display = "block";
}

/**
 * 刷新用户信息
 */
function refreshUserInfo() {
  console.log("刷新用户信息");

  // 显示加载状态
  document.getElementById("loading").style.display = "block";
  document.getElementById("user-info").style.display = "none";
  document.getElementById("error").style.display = "none";

  // 重新获取用户信息
  setTimeout(() => {
    getUserInfo();
  }, 500);
}

// 其他 JSAPI 调用示例

/**
 * 扫一扫功能示例
 */
function scanQRCode() {
  if (!window.tt) {
    showError("JSSDK 未初始化");
    return;
  }

  tt.scanCode({
    success: (res) => {
      console.log("扫码成功:", res);
      tt.showToast({
        title: `扫码结果: ${res.text}`,
        duration: 3000,
      });
    },
    fail: (err) => {
      console.error("扫码失败:", err);
      showError(`扫码失败: ${JSON.stringify(err)}`);
    },
  });
}

/**
 * 选择图片示例
 */
function chooseImage() {
  if (!window.tt) {
    showError("JSSDK 未初始化");
    return;
  }

  tt.chooseImage({
    count: 1,
    sizeType: ["original", "compressed"],
    sourceType: ["album", "camera"],
    success: (res) => {
      console.log("选择图片成功:", res);
      const tempFilePaths = res.tempFilePaths;
      tt.showToast({
        title: "图片选择成功",
        icon: "success",
      });
    },
    fail: (err) => {
      console.error("选择图片失败:", err);
    },
  });
}

/**
 * 获取位置信息示例
 */
function getLocation() {
  if (!window.tt) {
    showError("JSSDK 未初始化");
    return;
  }

  tt.getLocation({
    type: "gcj02",
    success: (res) => {
      console.log("获取位置成功:", res);
      const { latitude, longitude } = res;
      tt.showToast({
        title: `位置: ${latitude}, ${longitude}`,
        duration: 3000,
      });
    },
    fail: (err) => {
      console.error("获取位置失败:", err);
      showError(`获取位置失败: ${JSON.stringify(err)}`);
    },
  });
}

console.log("index.js 加载完成");


