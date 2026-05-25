# Trip.com Known Failures (Pre-experiment / External Research)

> **⚠️ 重要:本文件目前全部条目来源为公开资料,confidence: LOW-MEDIUM**
>
> 真实接入触发新失败时,source 改为 `local experiment` 且 confidence 升至 HIGH。
> 模板字段与 `站点经验库/_templates/known-failures.md` 一致,额外增加 `source` / `confidence` / `source-url` 字段。

---

## Failure Entry 001 — SSL Pinning blocks mitmproxy

- id: pre-001
- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 A 侦察
- request path: any (TLS layer)
- input summary: 任何 HTTPS 请求
- status code: N/A (connection-level failure)
- content type: N/A
- message: app 启动后无网络请求,或立即 crash
- raw marker: 网络抓包看不到任何业务流量
- failure class: waf (SSL pinning,广义反爬)
- root cause: 商业 OTA app 默认实现 SSL Pinning 阻止 mitmproxy 拦截
- correct handling: 用 objection 或 frida-android-hook 的 bypass-ssl 脚本 hook SSL 验证函数,强制返回 true
- related skill: rev-frida
- added eval: no
- version updated: no
- **source**: external research
- **source-url**: https://medium.com/@vikasg603/reverse-engineering-a-travel-apps-signature-logic-ssl-pinning-native-obfuscation-0f1c890dba0b
- **confidence**: HIGH (travel app 通用模式,Ctrip 系几乎必有)

---

## Failure Entry 002 — Root Detection causes app to crash

- id: pre-002
- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 A 侦察
- request path: N/A
- input summary: 在 root 后的设备启动 app
- status code: N/A
- content type: N/A
- message: app 启动后立即退出,或弹窗提示"检测到 root 环境"
- raw marker: logcat 显示 app 进程被自身 kill
- failure class: waf (root detection,广义反爬)
- root cause: 商业 OTA app 集成 RootBeer-style 检测,发现 root 后主动退出
- correct handling: Frida hook RootBeer 类的 isRooted() 等方法返回 false;或用 Magisk Hide / Zygisk DenyList 隐藏 root 痕迹
- related skill: rev-frida
- added eval: no
- version updated: no
- **source**: external research
- **source-url**: https://www.redfoxsec.com/blog/android-root-detection-bypass-using-frida
- **confidence**: MEDIUM-HIGH (商业 app 通用,Ctrip 系强相关)

---

## Failure Entry 003 — Anti-Frida detection kills hook

- id: pre-003
- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 B/C (Frida hook 阶段)
- request path: N/A
- input summary: 用 Frida attach 到 app 进程后
- status code: N/A
- content type: N/A
- message: Frida script 加载后 app crash / Frida session 断开
- raw marker: frida 终端报 `Process terminated` 或 connection refused
- failure class: waf (anti-frida)
- root cause: 商业 OTA app 扫描 frida-server / frida-gum 痕迹,发现后退出
- correct handling: 用 magisk-frida (frida-gadget 注入) / 改 frida-server 名称 / 修改 frida-agent 默认端口
- related skill: rev-frida
- added eval: no
- version updated: no
- **source**: external research
- **source-url**: https://book.hacktricks.xyz/mobile-pentesting/android-app-pentesting/bypass-biometric-authentication-android
- **confidence**: MEDIUM (推测,Ctrip 系商业级 app 大概率有)

---

## Failure Entry 004 — sign computed in native, Java hook returns nothing useful

- id: pre-004
- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 C 还原
- request path: any (sign-protected APIs)
- input summary: hook `ctrip.business.comm.ProcoltolHandle.buileRequest` 拿到 request 对象,但 sign 字段尚未填充
- status code: N/A
- content type: N/A
- message: hook 入参看不到最终 sign 值,sign 是在 native 层注入
- raw marker: buileRequest 返回的 request 对象的 sign 字段为 null 或占位符
- failure class: js-crypto (native crypto,广义"非 web 端加密")
- root cause: Ctrip 系 sign 算法实现在 native .so (推测 libcomponent-base.so 或类似),Java 层只是组装入参
- correct handling: 用 frida-trace 在 native 层枚举 JNI 函数,定位实际 sign 函数;Ghidra 分析 .so 找 HMAC/MD5 构造
- related skill: rev-frida + rev-idapython
- added eval: no
- version updated: no
- **source**: external research
- **source-url**: https://github.com/AlienwareHe/awesome-reverse/blob/main/android/mt-ctrip-hook-capture.md
- **confidence**: HIGH (公开资料直接命名 Ctrip 类,推测合理)

---

## Failure Entry 005 — Device fingerprint upload rate-limited blocks immediate replay

- id: pre-005
- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 D 复现
- request path: 注册/登录类接口
- input summary: 第二次调用 sign 一致但缺 valid device-id
- status code: 可能 200 业务码异常 (Ctrip 系常用业务码非 HTTP 码)
- content type: application/json
- message: "device not registered" / "risk control reject" 类似业务错
- raw marker: 业务码非 200 但 HTTP 200
- failure class: payload-mapping (设备指纹绑定)
- root cause: Ctrip 隐私政策显式说 Android ID 每次打开上传 ≤ 2 次,设备指纹刷新有节流,直接重放会缺最新 device-id
- correct handling: 在两次正常 app 启动之间限制调用;或 hook 设备指纹上传函数,捕获最新 device-id 后注入到 replay 脚本
- related skill: rev-frida
- added eval: no
- version updated: no
- **source**: external research
- **source-url**: https://docs.c-ctrip.com/files/6/unc_agreement_pdf/1tm0d12000lvd5viaF670.pdf
- **confidence**: HIGH (Ctrip 官方隐私政策文档)

---

## Failure Entry 006 — Donut 跨平台引擎 H5/RN 入口判别错误

- id: pre-006
- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 A 协议判别
- request path: N/A
- input summary: 看到接口域名同 web 就走 H5 路径,但实际是 RN/Donut 引擎
- status code: N/A
- content type: N/A
- message: 阶段 B (H5 路径) 找不到对应 JS 代码
- raw marker: webview debug 接入后页面是空白,DOM 树异常
- failure class: route-decision (协议形态判别错)
- root cause: Trip Tech 公开博客确认 Trip.com Group 用 Donut 引擎实现 99% 跨平台复用,部分页面是 RN/Donut 而非纯 H5
- correct handling: 阶段 A 完成前必须 check `assets/index.android.bundle` 是否存在;若存在则切到 React Native bundle 解包路径 (ast-deobfuscate)
- related skill: ast-deobfuscate (RN bundle 解包)
- added eval: no
- version updated: no
- **source**: external research
- **source-url**: https://medium.com/@trip-tech/how-trip-com-group-achieved-99-code-reuse-building-a-high-performance-cross-platform-market-55319b260b68
- **confidence**: MEDIUM (官方博客证实跨平台,但 Donut 是否等价 RN bundle 形态未公开)
