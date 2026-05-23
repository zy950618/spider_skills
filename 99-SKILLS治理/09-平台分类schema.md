---
title: 平台分类 schema
tags:
  - skills
  - governance
  - scoring
  - platforms
version: 0.1.0
---

# 平台分类 schema (v0.1.0)

> 引入起点: v0.3.9 (2026-05-23)
> 原因: thaiairways.com (web) 一致性证据被错位分给 mobile/native skill,8 个 app 类
> skill 拿到不该有的 consistency=30。需要 Skill ↔ domain platform 匹配后再计 consistency。

## 1. 平台分类(终端维度)

| 标签 | 中文 | 含义 |
|---|---|---|
| `web` | 网页 | PC 浏览器(Chrome/Edge/Firefox 等),HTML/JS/CSS,无 webview 套壳 |
| `h5` | 移动 H5 | 移动浏览器(Safari iOS / Chrome Android)直接打开的页面,或 APP 内 WebView 套壳 |
| `app` | 原生 APP | Android APK / iOS IPA 中的原生代码部分(Java/Kotlin/ObjC/Swift/C/C++)|
| `mini-program` | 小程序 | 微信小程序、支付宝小程序、字节小程序等(JS 但运行在专属容器) |
| `cross-platform` | 跨端通用 | 规范/治理/创建/评估类 skill,不绑定单一终端 |

约定:
- `web` 与 `h5` 在很多 skill 上重叠(都是浏览器 JS 环境),允许同时打两个标签。
- `app` 内嵌 WebView 调用 H5 页面时,如果 skill 的工作面是 H5 部分(JS 加密),应同时标 `h5` + `app`。
- 一个站点(domain)通常是**单平台**(thaiairways.com → web),但同一公司可能有多端 domain
  (m.thaiairways.com → h5, com.thaiairways → app)。

## 2. SKILL.md frontmatter 约定

每个 SKILL.md 在 frontmatter 加 `platforms` 字段,**列出适用平台的并集**:

```yaml
---
name: reverse-js-crawler
description: ...
platforms: [web, h5]   # 网页 + 移动 H5
---
```

```yaml
---
name: rev-frida
description: ...
platforms: [app]       # 仅原生 APP
---
```

```yaml
---
name: karpathy-guidelines
description: ...
platforms: [cross-platform]   # 通用规范,任何平台都适用
---
```

特殊规则:
- 列表必须非空,至少一个标签
- `cross-platform` 必须**独占**(不能 `[cross-platform, web]`),否则语义冲突
- `mini-program` 当前仓库无相关 skill,保留备用

## 3. domain 平台标识

每个 `站点经验库/<domain>/` 加 `_platform.yaml`,记录该 domain 主要平台:

```yaml
# 站点经验库/thaiairways.com/_platform.yaml
platform: web
notes: |
  PC 浏览器站点。m.thaiairways.com 走 h5,需要单独建目录。
  APK com.thaiairways.thaiairwaysapp 走 app,也需单独建目录(暂未接入)。
```

约定:
- 字段 `platform` 是**单值**(不是列表),与 skill 的 `platforms` 列表对应
- 若 domain 实际上多端共用同一目录,**应拆分**成多个 domain 目录,而不是 platform 写成列表
- 不写 `_platform.yaml` 的 domain → 默认 `web` (向后兼容)

## 4. 评分匹配规则

`score_skills.py` 的 `collect_consistency_evidence()` 改为 per-domain 字典,
`score_consistency(skill_platforms, consistency_by_domain)` 按以下规则聚合:

```
对每个 domain in 站点经验库:
    domain_platform = read(站点经验库/<domain>/_platform.yaml).platform or "web"

    if "cross-platform" in skill_platforms:
        applicable = True   # 跨端 skill 任何 domain 都计
    elif domain_platform in skill_platforms:
        applicable = True
    else:
        applicable = False

    if applicable:
        merge domain 的 fixtures/snapshots/reports/trend 进总体证据

按合并后的总体证据 → 满分 30,不匹配 → 0 分
```

## 5. 当前 skill ↔ platforms 映射

| Skill | 目录 | platforms | 理由 |
|---|---|---|---|
| reverse-js-crawler | 1-业务流程层 | `[web, h5]` | JS 逆向 |
| website-314-api-delivery | 1-业务流程层 | `[web, h5]` | 网站交付 |
| imperva-waf-reese84 | 1-业务流程层 | `[web, h5]` | WAF |
| mobile-app-reverse-delivery | 1-业务流程层 | `[app]` | 移动 App 交付 |
| skills-evaluation-governance | 1-业务流程层 | `[cross-platform]` | 治理 |
| find-crypto-entry | 2-JS逆向工具层 | `[web, h5]` | JS 加密入口 |
| ast-deobfuscate | 2-JS逆向工具层 | `[web, h5]` | JS AST 解混淆 |
| env-patch | 2-JS逆向工具层 | `[web, h5]` | 补环境 |
| skill-creator (ai-reverse-skill-creator) | 2-JS逆向工具层 | `[cross-platform]` | 创建 skill |
| rev-frida | 3-移动逆向工具层 | `[app]` | Frida |
| rev-idapython | 3-移动逆向工具层 | `[app]` | IDA |
| rev-dex-dumper | 3-移动逆向工具层 | `[app]` | DEX dump |
| rev-u3d-dump | 3-移动逆向工具层 | `[app]` | Unity IL2CPP |
| rev-symbol | 3-移动逆向工具层 | `[app]` | 符号恢复 |
| rev-struct | 3-移动逆向工具层 | `[app]` | 结构恢复 |
| rev-unicorn-debug | 3-移动逆向工具层 | `[app]` | Unicorn 模拟 |
| karpathy-guidelines | 4-通用规范层 | `[cross-platform]` | 通用规范 |
| site-api-adapter | 5-沉淀工具层 | `[web, h5, app]` | 接口沉淀,多端通用 |

## 6. 当前 domain ↔ platform 映射

| Domain | platform | 备注 |
|---|---|---|
| `thaiairways.com` | web | PC 网站,fixtures 来自 PC 浏览器录制 |

## 7. 与既有分类的关系

| 维度 | 字段 | 取值 |
|---|---|---|
| 终端(本文档) | `platforms` | web / h5 / app / mini-program / cross-platform |
| 业务分类(02-接入分类.md) | (无字段,在文档分类表里) | 纯HTTP / JS加密 / 补环境 / WAF / 接口化沉淀 / 314服务化 / 技能治理 |

**两个维度正交**:thaiairways.com 在终端维度是 `web`,在业务维度可能是 `纯HTTP + 接口化沉淀`。
评分目前只用终端维度过滤 consistency,业务维度未来再加(避免一上来过度复杂)。

## 8. Roadmap

- [x] v0.3.9: platforms 字段落地,score_skills.py 按 platform 过滤
- [ ] 后续: 在 platforms 之上叠加 scenarios(业务分类) 二级过滤
- [ ] 后续: 引入小程序专属 skill (微信/支付宝/字节)
- [ ] 后续: domain 自动从 _platform.yaml + 实际 fixtures 推断终端类型,无 yaml 时不默认 web
