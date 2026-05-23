# USAGE — 这个仓库怎么用

> 给**使用者**看的总入口。如果你是来 Claude Code 里跑逆向任务的,从这里开始。
>
> 别的入口:[INSTALL](./INSTALL.md) 安装 · [TRIGGERS](./TRIGGERS.md) 触发词速查 · [99-SKILLS治理/06-网页逆向标准规划.md](./99-SKILLS治理/06-网页逆向标准规划.md) Claude 工作流 · [99-SKILLS治理/07-一致性验证规约.md](./99-SKILLS治理/07-一致性验证规约.md) 一致性验证

---

## 这是什么

逆向工程 SKILL 库,装到 Claude Code 后,**用自然语言**让 Claude 帮你:

- 把一个网站逆向成可调接口(查询/列表/详情)
- 还原请求里的加密参数 (sign / token / x-d-token / reese84)
- 把浏览器加密 JS 搬到 Node.js 独立运行
- 解 Android APP 加固 / hook native 函数
- 验证 "我做出来的接口" 与 "真实网页" 数据一致(fixtures + replay + diff)
- 给自己产出的 Skill 打分 / 回测 / 治理

仓库里有 **18 个 Skill** + 一套 fixtures 一致性验证工具链 + CI + 治理评分。

## 谁应该用

- 做爬虫 / 接口逆向 / 反爬对抗的工程师
- 想用 Claude Code 跑长链路逆向任务的人
- 需要交付"可验证的"接口而不是"看起来能跑的"代码的人

## 怎么快速开始(3 步)

1. **装好**(一次性,5-10 分钟): 见 [INSTALL.md](./INSTALL.md)
2. **打开 Claude Code,在仓库目录内说话**:Claude 会自动加载本仓库的 SKILL 触发词
3. **用自然语言描述任务**(见下面的场景速查),Claude 自动调度对应 Skill 走六阶段(侦察 → 入口 → 还原 → 复现 → 沉淀 → 一致性验证)

---

## 场景速查

> 你说什么 → 触发什么 Skill → 做什么

| 我想做的事 | 我可以说 | 触发的 Skill | Skill 做什么 |
|---|---|---|---|
| 逆向一个新网站,做成纯接口 | "逆向 thaiairways.com 做接口" / "把 XXX 接入 314 框架" / "纯接口实现查询/加车/生单" | `website-314-api-delivery` | 五阶段总控:侦察→识别→还原→复现→交付 314 服务 |
| 爬虫接口还原 / sign 分析 | "JS 逆向 XXX" / "分析 X 网站请求" / "还原签名算法" / "做个采集脚本" | `reverse-js-crawler` | 页面侦察→真实 API 识别→sign/token 还原→Python/Node 复现 |
| 84 盾 / WAF token 被拒 | "84 盾过不去" / "Reese84 token 失败" / "x-d-token 拒了" / "Imperva 挑战页" | `imperva-waf-reese84` | 指纹模拟 + token 缓存 + 接受度阶段化验证 |
| 找请求里某个参数怎么生成的 | "x-sign 在哪生成" / "找加密入口" / "这个 token 哪来的" / "签名怎么算的" | `find-crypto-entry` | 静态搜索 + XHR 断点,只定位函数位置,不还原算法 |
| JS 看不懂(混淆) | "解混淆" / "_0x 是啥" / "字符串数组解密" / "代码全是乱码" / "deobfuscate" | `ast-deobfuscate` | Babel AST 解混淆:字符串解密 / 控制流还原 / 死代码删除 |
| 把浏览器 JS 拿到 Node 跑 | "补环境" / "把 JS 搬到 Node" / "webpack 模块提取" / "Node 里跑" | `env-patch` | Node 环境模拟:window/document/navigator/Proxy 引擎 |
| 逆向 Android APP | "APK 逆向" / "Frida hook Android app" / "航司 app 接口" / "安卓 app 抓包逆向" | `mobile-app-reverse-delivery` | Mobile 总控:协议判别(H5/Native/RN/Flutter)→对应路径 |
| 写 Frida hook 脚本 | "用 Frida hook ..." / "trace 调用参数" / "拦截 Java/ObjC/native 方法" | `rev-frida` | 现代 Frida API 脚本生成,Java/ObjC/native 都支持 |
| 写 IDAPython / IDALib 脚本 | "IDA 里写脚本" / "headless 反编译" / "Hex-Rays API" / "批处理 binary" | `rev-idapython` | IDB 操作 / Hex-Rays / 批处理 |
| Android 加壳 APK 脱壳 | "APK 加固脱壳" / "DEX 内存 dump" / "破解 class-loading 加壳" | `rev-dex-dumper` | 从运行中的 app dump DEX,对抗 360 / 腾讯 / 梆梆等加固 |
| Unity 游戏逆向 | "IL2CPP 符号恢复" / "Unity 游戏逆向" / "导入符号到 IDA" | `rev-u3d-dump` | 解析 global-metadata.dat,生成 IDA/Ghidra 导入脚本 |
| 重建数据结构 | "重建 struct" / "vtable 推断" / "C++ 类对象布局" | `rev-struct` | 跨函数分析内存访问模式 |
| 还原函数符号名 | "stripped binary 命名" / "通过魔数识别算法" / "通过字符串识别 lib 函数" | `rev-symbol` | 用代码特征 / 字符串 / 常量恢复符号 |
| Unicorn 仿真函数 | "用 Unicorn 仿真" / "跑算法不跑完整程序" / "绕过 JNI/syscall" | `rev-unicorn-debug` | 单函数仿真,脱离环境依赖 |
| 接口稳定后做 adapter | "接口化沉淀" / "做 adapter.yaml" / "prompt-router 输出" | `site-api-adapter` | 把逆向产出标准化为 adapter.yaml / schema / runbook |
| 验证产出和网页一致 | "跑一致性" / "fixtures 验证" / "snapshot diff" / "重放对比" | (脚本工具链) | 见 [07 一致性验证规约](./99-SKILLS治理/07-一致性验证规约.md) |
| 给 Skill 打分 / 评测 | "Skill 评分" / "Skill Bench" / "回测 Skill" / "新增 Skill 准入" | `skills-evaluation-governance` | 三段分 → 四段分评分,回测,漂移检测 |
| 创建 / 优化新 Skill | "新建一个 skill" / "优化 SKILL.md 描述" / "跑 eval 优化触发词" | `ai-reverse-skill-creator` | 起骨架,跑 eval loop,优化 description |
| 写代码遵守行为守则 | (隐式触发,看 4-通用规范层) | `karpathy-guidelines` | 最小改动 / 不过度抽象 / 显式假设 |

> 找不到对应场景?**直接用自然语言说**。Claude 会按触发词自动匹配,匹配失败会要求你澄清。

---

## 典型对话样例

### 场景 A:逆向一个新网站做接口

> 你: 帮我逆向 https://www.example-airline.com 做成纯接口,要查询航班、加购、生单。最后用 314 框架交付。

Claude 自动触发 `website-314-api-delivery`,先读 `99-SKILLS治理/06-网页逆向标准规划.md`,输出 5 阶段计划让你确认,再开始侦察。

### 场景 B:遇到 WAF token 被拒

> 你: 接口跑通了,但请求带的 reese84 cookie 被服务端拒,返回 incapsula html。

Claude 自动触发 `imperva-waf-reese84`,区分"token 生成成功"vs"业务 API 接受",改用指纹缓存 + 阶段化验证。

### 场景 C:找加密参数的生成函数

> 你: 请求头里有个 x-sign 每次都变,找一下这个在哪段 JS 生成的。

Claude 自动触发 `find-crypto-entry`,先用 search_in_sources 搜参数名,搜不到再上 XHR 断点。只输出函数位置 + 调用链,不还原算法。

### 场景 D:验证我的接口和网页对得上

> 你: 我做完 thaiairways 的搜索接口了,跑一下一致性验证。

Claude 按 [07 一致性验证规约](./99-SKILLS治理/07-一致性验证规约.md) 执行:让你录 fixtures(浏览器抓 HAR 或 CloakBrowser 录制),跑 `snapshot_replay.py` + `consistency_report.py`,出报告。一致率 < 90% 不算交付。

### 场景 E:给现有 Skill 打分

> 你: 给本仓库的所有 Skill 跑一次评分,我想看 v0.3.6 的真实分数。

Claude 触发 `skills-evaluation-governance`,跑 `score_skills.py` 四段分(结构 25/实战 25/一致性 30/漂移 20),输出每个 Skill 的总分 + 短板。

---

## 触发后会发生什么(六阶段)

任何"逆向某站点"类请求,Claude 都会走这个固定流程(详见 [99-SKILLS治理/06](./99-SKILLS治理/06-网页逆向标准规划.md)):

```
阶段 A: 侦察    域名 / WAF / 接口分布 / 站点经验库查重
阶段 B: 入口    sign / token / cookie 生成位置
阶段 C: 还原    算法实现 / 补环境 / 解混淆
阶段 D: 复现    Python/Node 接口可重复跑通
阶段 E: 沉淀    known-failures.md / test-log-lessons.md / change-log.md / adapter.yaml / Skill 评分
阶段 F: 一致性  fixtures 录制 / replay / diff / 一致率 ≥ 90% 才算交付
```

阶段 E 和 F 是**强制**的。没沉淀 = 没做完。没 fixtures = 数据可能错没人知道。

---

## 红线(Claude 不会做)

| 红线 | 原因 |
|---|---|
| 真实支付链路自动测试 | 真实扣款,只在用户明示授权时跑 |
| 把 fixtures 设成 `category: payment` | 一致性验证不录支付,见 07 规约 |
| 跳过五阶段直接写代码 | 长链路任务必须先规划再执行 |
| 跳过沉淀(阶段 E/F) | 不沉淀就是没做完 |
| 把"评分高"等同于"真实能用" | 评分是结构指标,真实成功率看 fixtures 一致率 |
| 把所有字段加 `ignore` 容忍度刷一致率 | 评分作弊,review 时盯防 |
| 自动上传抓包 / fixtures 到第三方 | 反爬数据敏感,不外传 |

---

## 进阶

- **跨项目用 hook**:默认 Stop hook 只在仓库内触发。跨项目工作时手动核对 5 步沉淀,或参考 [CLAUDE.md](./CLAUDE.md) 的「跨项目自动触发」段
- **加新站点**:从 `站点经验库/_templates/` 复制 7 文件模板 + `fixtures/` 子目录到 `站点经验库/<domain>/`
- **加新 Skill**:见 [99-SKILLS治理/04-新增SKILL评分回测准入.md](./99-SKILLS治理/04-新增SKILL评分回测准入.md)
- **看仓库分数**:`python 1-业务流程层/skills-evaluation-governance/scripts/score_skills.py <某一层>`

---

## 帮助

- 安装问题 → [INSTALL.md 的常见问题](./INSTALL.md#常见问题)
- 不知道说什么会触发 → [TRIGGERS.md](./TRIGGERS.md)
- 一致性验证流程 → [99-SKILLS治理/07-一致性验证规约.md](./99-SKILLS治理/07-一致性验证规约.md)
- 评分体系 → [99-SKILLS治理/05-当前评分与回测结果.md](./99-SKILLS治理/05-当前评分与回测结果.md)
