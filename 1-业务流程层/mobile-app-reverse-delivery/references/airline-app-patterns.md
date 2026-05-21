# 航司类 App 常见模式

记录公共可观察的设计规律（不针对特定航司）。新案例完成后补充新观察到此处。

## 协议形态比例（公开市场观察）

| 形态 | 占比（粗估） | 典型代表特征 |
|---|---|---|
| H5 套壳为主 | 50%+ | 低成本航司、改版频繁的航司 |
| H5 + Native bridge | 20-30% | 关键业务（搜索/支付）在 H5，登录/设备指纹在 native |
| 纯 Native | 10-20% | 大型全服务航司、注重 UX 一致性 |
| React Native | 5-10% | 较新的航司或 IT 现代化的航司 |
| Flutter | 极少 | 一般不见于航司主 app |

## 签名常见命名

观察到的高频命名（搜 jadx 反编译产物找类似模式）：

- `*Manager.sign()` / `*Util.sign()`
- `*SecurityHelper.encrypt()`
- `*Interceptor.intercept()`（OkHttp）
- `*Service.addCommonHeaders()`

native 端常见入口（找 Java_*）：

- `Java_*_signRequest`
- `Java_*_genSign`
- `Java_*_encrypt`

## 设备绑定字段

航司 app 常见做法是把设备指纹绑进签名或 token：

- `device_id` / `udid` / `imei`（旧 app）
- `android_id` / `idfa`（新 app）
- 自定义 `cd_id` / `app_uuid`（持久化到 SharedPreferences）
- 通常首次启动注册到服务端，之后无法跨设备复用

逆向时必须找到生成位置和持久化路径，否则换设备就失效。

## 常见 SSL Pinning 实现

按检测严格度从低到高：

1. **OkHttp CertificatePinner**：objection 一键 bypass
2. **自定义 TrustManager**：objection 一般也能 bypass
3. **native pinning（.so 中校验证书）**：需 Frida hook native 函数
4. **多层 pinning + 反 Frida**：先用 magisk hide / zygisk-detach 隐藏 root，再做 pinning bypass
5. **白名单 IP + 多端校验**：极少见，遇到要专项

## 反 Frida / 反调试

部分航司 app（少数）有反 Frida 检测：

- 检测 `frida-server` 进程
- 检测 `/data/local/tmp/re.frida.server`
- 检测线程名含 `gum-js`、`gmain`
- 检测端口 27042 / 27043

应对：用 magisk frida-server 或 fart 隐藏，或者用 `fridare` 改 Frida 二进制特征。

## 已知具体案例

> 留白：每完成一个航司 app 真实任务后，在此追加 1-2 行：
> - 任务时间 / app 名 / 协议形态 / 关键签名位置 / 主要坑

例：

- 2026-MM-DD / Example Airlines / H5 套壳 / 加密在 webview JS / 主要坑: webview debug 被禁需 Frida 强开
