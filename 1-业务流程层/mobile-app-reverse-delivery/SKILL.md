---
name: mobile-app-reverse-delivery
description: >-
  Use this skill when a user wants to reverse-engineer a mobile app (Android APK or iOS IPA) and turn it into a callable HTTP/Python interface, especially for airline / booking / flight apps that combine H5 webview + native bridge + protected APIs. Trigger when the user mentions APK 逆向, IPA 逆向, 移动 App 逆向, 航司 App 逆向, 航空公司 App 接口, 安卓 app 接口逆向, app 抓包逆向, app 加密参数, app 接口还原, mobile crawler, mobile app reverse, Android booking app, iOS airline app, Frida hook airline, H5 套壳, native crypto in app, sign in app, sn in app, airline app login/search/order/payment, vietjet app, thaiairways app, airasia app, or similar airline-app reverse delivery requests.
---

# Mobile App Reverse Delivery

## Do NOT Trigger When

- 用户目标是纯 Web 网站（浏览器访问） → 切到 `website-314-api-delivery`
- 用户只问 Frida 脚本怎么写 → 切到 `rev-frida`
- 用户只问 IDA 分析某个 .so 函数 → 切到 `rev-idapython`
- 用户只问 Android 脱壳 → 切到 `rev-dex-dumper`
- 用户只问 Unity 游戏 IL2CPP → 切到 `rev-u3d-dump`（航司 app 极少是纯 Unity）
- 用户问的是普通 H5 加密参数还原（mobile app 内嵌的 webview 本质是 web） → 优先尝试 `reverse-js-crawler` + `env-patch`

## Purpose

把一个 mobile app（重点：**航司 / 旅行预订类 App**）从"抓包看不懂" 推进到"可独立调用的 HTTP/Python 接口实现"。这个 Skill 是 mobile 端的业务流程总控，对标 `website-314-api-delivery`，但因为移动端有 H5 / RN / Flutter / Native 等多协议形态混合，需要先做协议判别再选工具链。

## When To Use

- "实现 VietJet App 的航班搜索/订座/行李加购/支付接口"
- "把 Thai Airways Android App 的搜索接口翻成 Python"
- "AirAsia App 抓包有签名，帮我还原"
- "这个 app 是 H5 套壳还是 native，怎么破解它的 sign"
- "把航司 app 的接口接到 314 框架"

## Skill Routing

按协议形态调用不同工具：

| 协议形态 | 调用 |
|---|---|
| H5 webview 加密在 JS 中 | `reverse-js-crawler` + `find-crypto-entry` + `env-patch` + `ast-deobfuscate` |
| Native .so 加密（C/C++） | `rev-frida`（动态 hook）+ `rev-idapython`（静态分析）+ `rev-unicorn-debug`（仿真验证） |
| Native 加密但符号被剥 | `rev-symbol` 还原 + `rev-struct` 重建结构 |
| 加壳 APK | 先 `rev-dex-dumper` 脱壳 |
| React Native bundle | bundle 解包 → `ast-deobfuscate` → 类 web 流程 |
| Flutter | snapshot dump + Frida 动态 hook（无静态符号） |
| WAF/反爬在 mobile SDK | `imperva-waf-reese84`（如果是 Reese84 系）或专项分析 |
| 接口稳定后沉淀 adapter | `5-沉淀工具层/site-api-adapter` |
| 用户要求"接 314" | 本 skill 是 mobile 端总控，314 接入由本 skill 协调 |

## Workflow

### 阶段 A：协议形态判别（30 分钟内）

1. **抓包**：用 mitmproxy / Charles / Fiddler，配 CA + SSL Pinning bypass（Frida `frida-tools` 的 `objection` 一键 bypass 大多数航司 app）
2. **过滤业务请求**：找出 search / availability / booking / order / payment 关键接口
3. **判别 webview 痕迹**：
   - User-Agent 含 `wv` / `WebView` → 大概率 H5 套壳
   - 接口域名和官网 web 完全一致 → 大概率 H5 复用
   - User-Agent 是定制 SDK 标识（如 `VietjetAir/x.y.z (Android)`） → 大概率 native
4. **判别框架**：
   - 应用根目录有 `libapp.so` + `libflutter.so` → Flutter
   - `assets/index.android.bundle` → React Native
   - `classes.dex` 但反编译后多为壳代码 → 加壳
   - 正常 Java 类清晰可读 → 原生 Android
5. **判别加密位置**：
   - 抓包请求中的 `sign / sn / x-sign / auth` 等参数：先尝试 JS 端搜索（如果 webview）
   - 如果 webview 里找不到 → 大概率 native 端 → Frida hook 关键 OkHttp / native 函数

### 阶段 B：H5 路径（如果是 webview 套壳）

1. 在 webview debug 模式下打开 chrome://inspect 接入 → 完全等同 `reverse-js-crawler` 流程
2. 如果厂家关了 webview debug：用 `Frida` hook `WebView.loadUrl` 强制 enable
3. 接口和 web 完全一致 → 直接复用网站逆向脚本

### 阶段 C：Native 路径（如果是 .so 端加密）

1. **动态优先**：用 `rev-frida` hook 关键 Java/Kotlin 入口函数（如 `*Manager.sign(...)` / `*Util.encrypt(...)`）拿到参数和返回值
2. **静态辅助**：拿出 .so 用 `rev-idapython` 分析，找到 native 函数地址
3. **断点验证**：Frida `Module.findExportByName` 或 `Interceptor.attach` 在 native 函数处打断点
4. **仿真还原**：算法清晰后用 `rev-unicorn-debug` 在 Python 中独立仿真（脱离手机依赖）
5. **替代方案**：如果 native 算法太复杂，保留 Frida RPC 做"在线签名服务"，业务侧调用 Frida server 拿签名

### 阶段 D：复现 + 验证

| 步骤 | 标准 |
|---|---|
| 单接口复现 | Python/Node 能稳定拿到与 app 抓包一致的响应 |
| 链路串接 | search → availability → cart → order → payment 全链路通过 |
| 签名稳定性 | 同一 device id / token / market 下，签名 100% 可复算 |
| 失败路径 | 主动测试 token 过期、被风控、错误业务参数 |

支付阶段强制：sandbox / dry-run 优先，真实扣款必须用户明示授权。

### 阶段 E：沉淀

1. `站点经验库/<app-bundle-or-domain>/known-failures.md`（mobile 端特有的失败模式：SSL pinning 变体、Frida 反调试、root 检测、设备指纹绑定）
2. `站点经验库/<app-bundle-or-domain>/route-decisions.md`（H5 vs native 判别结果、关键签名函数位置）
3. 调用 `5-沉淀工具层/site-api-adapter` 产出 adapter.yaml
4. 调用 `skills-evaluation-governance` 给本次任务用到的 skill 打分

## Success Criteria

- 已判别 app 协议形态（H5 / native / RN / Flutter / 混合）
- 已找到关键加密函数位置（JS / .so / RN bundle / Flutter snapshot）
- 复现成 Python/Node 调用且服务端真实接受
- 已区分 native crypto / WAF / 业务错 / 路由错 / 设备绑定错
- 已沉淀站点经验库 + adapter
- 真实扣款不在自动化流程跑

## Boundaries

- 这是 mobile app 业务流程总控，不替代具体工具 skill（Frida/IDA/Unicorn 等都是被调用的工具）
- 不混入编码 AGENT 规则
- 不涉及游戏外挂、付费破解、跳过登录付费等灰黑产场景（仅用于自有/授权 app 的接口集成）

## Governance

- Version: 0.1.0
- Status: initial scaffold, awaiting first real airline-app project to validate
- Change log: 记录新触发词、新协议形态、新失败模式到 `references/governance.md`
- Drift tests: 添加新航司 app 案例后回测全部 evals
- Site memory: 任务结束写回 `站点经验库/<app-bundle-or-domain>/`

## References

- `references/workflow.md`：完整 5 阶段交付流程详细版
- `references/airline-app-patterns.md`：航司 app 常见模式（H5 套壳比例、典型签名函数命名、常见 SSL Pinning 实现）
- `references/governance.md`：版本、变更、漂移测试策略
