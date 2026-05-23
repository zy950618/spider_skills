# TRIGGERS — 触发词速查表

> 说什么 → 触发哪个 Skill。中英双列。
>
> 这张表是**用户视角**的速查。每个 Skill 自己的 frontmatter `TRIGGER when:` 是**Claude 视角**的判断依据。两者互补。
>
> 其他入口:[USAGE](./USAGE.md) · [INSTALL](./INSTALL.md)

---

## 怎么读这张表

- **关键词**:你说这句话或包含这些词,Claude 会激活对应 Skill
- **Skill**:被触发的 Skill 名
- **层**:1=业务流程总控 / 2=JS 工具 / 3=移动工具 / 4=规范 / 5=沉淀
- **做什么**:Skill 接管后的实际行为(一句话)
- **不触发**:什么时候 Skill 不应该被激活(避免误触)

---

## 网页逆向类

| 关键词 (中) | 关键词 (en) | Skill | 层 | 做什么 | 不触发 |
|---|---|---|---|---|---|
| 逆向 XXX 网站 / 把 XXX 接入 314 / 纯接口实现 / 网站接入 | reverse XXX website / new site adapter / pure API / 314 framework | `website-314-api-delivery` | 1 | 五阶段总控,把网页 → adapter.yaml → 314 服务 | 只想看 HTML 内容 / 调浏览器自动化 |
| JS 逆向 / 接口还原 / 加密参数 / 补环境 / 批量采集 | JS reverse / API restoration / sign reverse / crawler delivery | `reverse-js-crawler` | 1 | 页面侦察 + 真实 API 识别 + sign 还原 + Python/Node 复现 | 静态分析 / IDA / 移动 app |
| 84 盾 / Reese84 / Incapsula / x-d-token / WAF 挑战 / 风控 token / 浏览器指纹 / 反扒 / token 被拒 | reese84 / incapsula / imperva / x-d-token / browser fingerprint / WAF challenge / anti-bot | `imperva-waf-reese84` | 1 | 指纹模拟 + token 缓存 + 阶段化接受度验证 | 普通 cookie / 单纯 401(非 WAF) |
| 找加密入口 / xxx 在哪生成 / 签名怎么算 / 请求头 xxx 哪来的 / 定位加密函数 | locate sign entry / find crypto entry / where is x-sign generated | `find-crypto-entry` | 2 | 静态搜参数名 + XHR 断点,只输出函数位置+调用链 | 抓包看请求 / 分析普通参数 |
| 解混淆 / 反混淆 / 字符串数组解密 / _0x 看不懂 / 控制流平坦化 / deobfuscate / sojson / obfuscator.io | deobfuscate / unobfuscate / string array decrypt / control flow flattening | `ast-deobfuscate` | 2 | Babel AST:字符串解密 / 控制流还原 / 死代码删除 | minified(只是压缩) / 想格式化代码 |
| 补环境 / 把 JS 搬到 Node / webpack 模块提取 / Node 里跑 / 环境模拟 | env patch / node sandbox / webpack module extract / run browser JS in Node | `env-patch` | 2 | window/document/navigator/Proxy 引擎 + 模块提取 | 浏览器内调试 / 普通 Node 代码 |

---

## Mobile / Native 逆向类

| 关键词 (中) | 关键词 (en) | Skill | 层 | 做什么 | 不触发 |
|---|---|---|---|---|---|
| APK 逆向 / IPA 逆向 / 移动 app 逆向 / 航司 app / 安卓抓包逆向 / app 加密参数 / sn in app | mobile app reverse / Android booking app / iOS airline app / Frida hook airline | `mobile-app-reverse-delivery` | 1 | 协议判别(H5/Native/RN/Flutter)+ 对应路径 | 纯 Web 站(走 website-314)/ 桌面应用 |
| Frida hook / trace 调用 / 拦截 Java/ObjC/native 方法 / dump 内存 | Frida script / hook function at runtime / intercept method / memory dump | `rev-frida` | 3 | 现代 Frida API 脚本生成 | 静态分析 / smali 改包 / 想用 Xposed |
| IDAPython / IDALib / IDB / Hex-Rays API / headless 反编译 / 批处理 binary | IDAPython script / IDALib headless / Hex-Rays / batch IDB | `rev-idapython` | 3 | IDB 操作 / Hex-Rays / IDALib 批处理 | Ghidra / radare2 / 普通 Python |
| APK 加固脱壳 / DEX 内存 dump / 破解 class-loading 加壳 / 360 加固 / 腾讯乐固 / 梆梆 / 爱加密 | unpack APK / DEX dump / defeat class-loading packing | `rev-dex-dumper` | 3 | 从运行中的 app dump DEX | 原始未加固 APK 直接 jadx |
| IL2CPP 符号恢复 / Unity 游戏逆向 / global-metadata 解析 / 导入符号到 IDA | Unity IL2CPP dump / metadata parsing / import to IDA | `rev-u3d-dump` | 3 | 解析 IL2CPP binary + metadata,生成导入脚本 | 非 Unity 应用 / 普通 NDK |
| 重建 struct / vtable 推断 / C++ 类布局 / 跨函数追内存偏移 | reconstruct struct / vtable inference / C++ object layout | `rev-struct` | 3 | 跨函数分析内存访问模式 | 已有源码 struct / 单变量 |
| stripped binary 命名 / 通过魔数识别算法 / 通过字符串识别 lib 函数 / 函数符号恢复 | symbol recovery / magic constant detection / library function fingerprint | `rev-symbol` | 3 | 用代码特征 / 字符串 / 常量恢复符号 | 已有 symtab / 只想反编译 main |
| Unicorn 仿真 / 跑算法不跑完整程序 / 绕过 JNI/syscall 仿真 / 解密本地 string | unicorn emulate / function fragment emulation / bypass JNI | `rev-unicorn-debug` | 3 | 单函数仿真,脱离环境依赖 | 想用 Frida 动态 hook / 拿到源码直接编译 |

---

## 一致性验证类(产出 vs 真实网页对齐)

> 没有专门的 SKILL,是**脚本工具链**。Claude 看到对应关键词会走 [07 一致性验证规约](./99-SKILLS治理/07-一致性验证规约.md) 的流程。

| 关键词 (中) | 关键词 (en) | 工具 | 做什么 |
|---|---|---|---|
| 跑一致性 / fixtures / snapshot diff / 重放对比 / 验证产出和网页一致 | run consistency / fixtures verification / snapshot diff / replay vs original | `tools/recorder/cloak_recorder.py` + `tools/replayer/snapshot_replay.py` + `consistency_report.py` | 录制 fixtures → 重放 → 字段 diff → 出 markdown 报告 + trend.json |
| HAR 导入 / 抓包导入 fixtures | HAR import / DevTools to fixtures | `tools/recorder/har_to_fixtures.py` | Chrome DevTools 导出的 HAR → snapshots 三件套 |
| CloakBrowser 录制 / 反指纹浏览器录制 | CloakBrowser record / cloak record | `tools/recorder/cloak_recorder.py` | 启动带反指纹的 Chromium 录请求 |
| 验证 fixtures 合规 / fixtures schema 检查 | validate fixtures schema | `tools/replayer/validate_fixtures.py` | 检查三件套齐 / category 合法 / expiry 未过 |

---

## 治理 / 评分 / 创建类

| 关键词 (中) | 关键词 (en) | Skill | 层 | 做什么 | 不触发 |
|---|---|---|---|---|---|
| Skill 评分 / Skill Bench / 跑分 / 评测 / 回测 / 漂移测试 / 新增 Skill 准入 / 负例测试 | score skills / Skill Bench / backtest / drift test / new skill admission | `skills-evaluation-governance` | 1 | 三段分→四段分评分,回测,漂移检测 | 一般代码评审 / PR review |
| 新建 skill / 创建 skill 从零起 / 优化 SKILL.md 描述 / 跑 description loop / 触发词优化 | create skill / optimize SKILL.md description / run trigger loop | `ai-reverse-skill-creator` | 2 | 起骨架 + eval loop + 触发词优化 | 一般 prompt 优化 / 通用 GPT 调优 |
| 接口化沉淀 / adapter.yaml / prompt-router / runbook / schema 沉淀 / 多站点复用 | API adapter / adapter.yaml / prompt-router / standardization | `site-api-adapter` | 5 | 把接口稳定的逆向产出 → adapter.yaml / schema.json / runbook | 还在调接口 / 接口未稳定 |
| 行为守则 / 最小改动 / 避免过度抽象 / 显式假设 / 可验证成功标准 | karpathy guidelines / surgical changes / surface assumptions / verifiable success | `karpathy-guidelines` | 4 | 隐式触发(写代码时遵循) | 不主动召唤,看代码评审时自动应用 |

---

## 跨类场景(多 Skill 协同)

| 场景 | 触发顺序 |
|---|---|
| 新网站全链路接口 | `website-314-api-delivery` → `reverse-js-crawler` → `find-crypto-entry` → `ast-deobfuscate` / `env-patch` → 一致性验证 → `site-api-adapter` |
| 航司 App 接口 | `mobile-app-reverse-delivery` → 分支(H5 → JS 链路 / Native → `rev-frida`+`rev-idapython`+`rev-unicorn-debug`)→ `site-api-adapter` |
| WAF 拒接口 | 主链路任意触发 + `imperva-waf-reese84` 并行处理 token |
| Unity 手游逆向 | `rev-u3d-dump` → `rev-symbol` → `rev-frida` 动态验证 → `rev-unicorn-debug` 算法仿真 |
| 收尾治理 | (任意 Skill 工作完)→ `skills-evaluation-governance` 打分 + 站点经验库写回 |

---

## 反例:这些词**不会**自动触发本仓库 Skill

- 写普通业务代码 / CRUD / React 前端 / 数据库设计
- 抓包看请求(没有"逆向"意图)
- 装环境 / 配置 / 部署
- 写文档 / 开会 / 项目管理
- LLM 通用 prompt 调优(非 Claude SKILL)

如果你想做这些事但 Claude 误触发了某个 Skill,直接说"不要走 reverse-js-crawler 流程,我只是想 X"即可。

---

## 找不到对应触发词

提个 issue 或直接在 Claude 里说:**"我想做 X,但不知道触发哪个 Skill"**。Claude 会:
1. 尝试匹配最接近的 Skill 询问你确认
2. 如果都不匹配,提示走通用代码 / 走 `ai-reverse-skill-creator` 创建新 Skill

新触发词会沉淀到对应 SKILL.md 的 `description`(下轮 auto_tune 自动跑触发词校准),让下次更准。
