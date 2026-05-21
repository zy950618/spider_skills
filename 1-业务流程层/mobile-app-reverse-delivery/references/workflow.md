# Mobile App Reverse Delivery Workflow

详细版的 5 阶段流程。SKILL.md 是简版总览，本文是被触发后展开阅读的执行手册。

## 阶段 A：协议形态判别

### A.1 准备环境

- Android：root 真机（或夜神/MuMu 但部分 app 检测模拟器）+ Frida server 与 Frida client 版本对齐
- iOS：越狱设备（unc0ver / palera1n）+ Frida + ssh
- 抓包：mitmproxy（首选，可脚本化）/ Charles / Fiddler
- SSL Pinning bypass：`objection -g <pkg> explore` → `android sslpinning disable` / `ios sslpinning disable`

### A.2 抓包定位关键接口

1. 启动 app，走完一遍正常业务流程（search → details → cart → order → payment 关键页都点一遍）
2. 在抓包工具里过滤 host = api.<airline>.com 或类似业务 host
3. 标记每个业务阶段的关键 URL、method、headers、payload
4. 重点关注非标准 header：`x-sign`、`x-nonce`、`x-timestamp`、`x-device-id`、`sn`、`sign`、`token`

### A.3 协议形态判别表

| 信号 | 推断 |
|---|---|
| User-Agent 含 `; wv)` 或 `WebView` | H5 套壳 |
| User-Agent 是定制 SDK 标识 | native |
| 接口 host 和 web 一致，参数命名一致 | 大概率 H5 复用 |
| 接口 host 是 mobile 专属（如 `mapi.xxx.com`） | 大概率 native |
| APK 里有 `libapp.so` + `libflutter.so` | Flutter |
| APK 里有 `assets/index.android.bundle` | React Native |
| APK 解包后 `classes.dex` 反编译为壳代码 | 加壳，先脱壳 |

## 阶段 B：H5 路径

H5 套壳本质等同 web 逆向。优先 webview 接入 chrome://inspect。

如果 webview debug 被禁：

```python
# Frida 强制启用 webview debug
Java.perform(function() {
    var WebView = Java.use('android.webkit.WebView');
    WebView.setWebContentsDebuggingEnabled.implementation = function(enabled) {
        this.setWebContentsDebuggingEnabled(true);
    };
});
```

接入后切到 `reverse-js-crawler` + `find-crypto-entry` + `env-patch` 工具链。

## 阶段 C：Native 路径

### C.1 Java/Kotlin 入口

用 jadx-gui 或 `jadx-cli` 反编译 apk，搜索：

- `sign(` / `Sign(` / `signature` / `SignUtil`
- `encrypt(` / `Encrypt(` / `EncryptUtil`
- okhttp 的 `Interceptor` 子类（请求被签名时往往加在 Interceptor 里）

找到入口后用 Frida hook 看实际参数和返回。

### C.2 Native .so

Java 入口最终调 `System.loadLibrary("xxxx")` 然后 JNI 进入 native。

切到 `rev-frida` + `rev-idapython` 工具链：

1. Frida `Process.enumerateModules()` 找目标 .so
2. `Module.enumerateExports("libxxx.so")` 看导出符号
3. JNI 函数命名规则：`Java_<class>_<method>` 找入口
4. 拉 .so 到电脑用 IDA / Ghidra 反汇编

### C.3 算法仿真

如果算法定位清楚但实现复杂（如自定义白盒 AES、SM4 变种），用 `rev-unicorn-debug` 在 Python 直接调 .so 函数（脱手机依赖）。

如果实在不能仿真，保留"Frida RPC 在线签名服务"方案：手机持续运行 Frida server，业务侧通过 RPC 拿签名。

## 阶段 D：复现 + 验证

参考 `website-314-api-delivery` 的 D 阶段，标准相同。

## 阶段 E：沉淀

参考 `website-314-api-delivery` 的 E 阶段，但站点经验库目录名用 **app bundle id** 或 **官方主域名**（如 `vietjetair.com` 同时覆盖 web 和 app）。
