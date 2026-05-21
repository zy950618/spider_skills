---
title: my_reverse_skill 索引
tags:
  - codex
  - skills
  - reverse
  - skill-bench
  - governance
---

# my_reverse_skill 索引

本仓库是逆向工程 SKILLS 总库，分层组织，仓库为唯一来源，通过 Windows junction 安装到 `~/.claude/skills/`。

## 层次划分

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口，按用户需求调度 2/3/5 层 |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具，被 1 层调用 |
| 3 | `3-移动逆向工具层/` | Android/iOS/Native 工具，被 1 层调用 |
| 4 | `4-通用规范层/` | 行为守则、代码纪律 |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化沉淀（被 1 层调用） |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入 |
| - | `站点经验库/` | 站点案例（按 domain/market/locale 拆分） |
| - | `tools/` | 仓库辅助脚本（sync_site_memory.py 等） |

## 全部 18 个 skill

### 1-业务流程层（5 个）

| Skill | 适用场景 | 主要触发词 |
|---|---|---|
| `website-314-api-delivery` | 新网站 → 纯接口 → 查询/加车/生单/支付 → 314 交付 | 新站点接入、纯接口、314 基础框架、加解密全部实现 |
| `mobile-app-reverse-delivery` | 航司类 Mobile App → 接口逆向 → 314 交付 | APK 逆向、IPA 逆向、航司 App 接口、安卓 app 接口逆向、Frida hook airline |
| `reverse-js-crawler` | 页面侦察、接口识别、签名/token 还原、采集脚本交付 | JS逆向、接口还原、加密参数、补环境、批量采集 |
| `imperva-waf-reese84` | Imperva/Reese84/84 盾/x-d-token/WAF challenge | 84盾、Reese84逆向、Incapsula、WAF挑战、风控token |
| `skills-evaluation-governance` | 给技能评分、补 eval、回测、漂移测试、版本治理 | SKILLS评分、Skill Bench、新增Skill准入、回测、漂移 |

### 2-JS逆向工具层（4 个）

| Skill | 适用场景 |
|---|---|
| `find-crypto-entry` | 定位 JS 加密参数生成入口（函数位置 + 调用链） |
| `ast-deobfuscate` | Babel AST 解混淆（字符串解密、控制流还原、死代码删除） |
| `env-patch` | 浏览器加密 JS 在 Node.js 中运行（补环境） |
| `ai-reverse-skill-creator` | 创建/优化/评测逆向类 skill |

### 3-移动逆向工具层（7 个）

| Skill | 适用场景 |
|---|---|
| `rev-frida` | Frida hook 脚本生成（Java/ObjC/Native 拦截、参数/返回值 trace） |
| `rev-idapython` | IDAPython / IDALib 脚本（IDB 操作、Hex-Rays、批处理） |
| `rev-dex-dumper` | Android DEX 内存 dump，破解 class-loading 加壳 |
| `rev-u3d-dump` | Unity IL2CPP 符号 dump（方法名/地址，IDA/Ghidra 导入脚本） |
| `rev-struct` | 通过内存访问模式重建数据结构 |
| `rev-symbol` | 通过代码特征/字符串/常量恢复函数符号 |
| `rev-unicorn-debug` | Unicorn 引擎仿真函数（脱离 JNI/syscalls/libc 依赖） |

### 4-通用规范层（1 个）

| Skill | 适用场景 |
|---|---|
| `karpathy-guidelines` | LLM 编码行为守则（最小改动、显式假设、可验证成功标准） |

### 5-沉淀工具层（1 个）

| Skill | 适用场景 |
|---|---|
| `site-api-adapter` | 把单站点稳定的逆向结果标准化为 adapter.yaml / schema.json / runbook / prompt-router（接口稳定后才用，被 1 层调用） |

## 调度顺序（典型场景）

### 网页逆向（最常用）

```
website-314-api-delivery（Web 总控）
  ├─ reverse-js-crawler         主链路
  │    ├─ find-crypto-entry     定位加密
  │    ├─ ast-deobfuscate       看不懂的 JS
  │    └─ env-patch             浏览器 JS → Node
  ├─ imperva-waf-reese84        遇到 84盾/Incapsula
  ├─ 5-沉淀工具层/site-api-adapter   接口稳定后做 adapter
  └─ skills-evaluation-governance    任务结束做评分
```

### Mobile App 逆向（航司类）

```
mobile-app-reverse-delivery（Mobile 总控）
  ├─ 阶段 A: 协议判别（H5 / Native / RN / Flutter）
  ├─ H5 路径   → reverse-js-crawler + 2-JS逆向工具层/*
  ├─ Native 路径 → 3-移动逆向工具层/rev-frida + rev-idapython + rev-unicorn-debug
  ├─ 加壳 APK → 3-移动逆向工具层/rev-dex-dumper
  ├─ 5-沉淀工具层/site-api-adapter   接口稳定后做 adapter
  └─ skills-evaluation-governance    任务结束做评分
```

### 纯 Native 工具单点

```
rev-frida                动态 hook 看真实参数
  ├─ rev-idapython       静态分析
  ├─ rev-struct          重建结构
  ├─ rev-symbol          还原符号
  └─ rev-unicorn-debug   独立仿真验证算法
```

完整规划见 `99-SKILLS治理/06-网页逆向标准规划.md`。

## 新网站接入入口

任何新网站任务都从 `website-314-api-delivery` 开始。典型输入：

```text
目标网站：https://www.example.com/
目标：纯接口实现查询、加车、生单、支付
要求：加解密全部实现，最后使用 314 基础框架提供接口
```

## 长期进化闭环

每次真实任务结束后必须问：

1. 有没有新触发词？
2. 有没有新失败类型？
3. 有没有新分类规则？
4. 有没有新加解密或反爬模式？
5. 有没有应该加入 eval 的场景？
6. 是否需要升级版本号？

沉淀路径：

```
真实任务
  → 归类（02-新网站接入分类.md）
  → 执行（按 06-网页逆向标准规划.md）
  → 记录失败点（站点经验库/<domain>/known-failures.md）
  → 更新 references
  → 增加 eval
  → 评分（skills-evaluation-governance）
  → 版本升级
  → 漂移测试（03-测试评分漂移.md）
```

## 官方 CI 跑分

本地目录已有 `SKILL.md` 和 `evals/`，结构上具备被 Skill Bench 评测的能力。但要正式跑分还需要：

- 把 skill 镜像到一个 Git 仓库（本仓库 my_reverse_skill 已具备）
- 仓库可见路径，例如 `skills/<skill-name>/`（本仓库用分层目录，必要时再镜像一份扁平结构给 CI）
- GitHub Actions 配置模型 API key secret（如 `ANTHROPIC_API_KEY`）
- PR 触发 + 定时触发的 Skill Bench workflow

## 治理文档

- `99-SKILLS治理/01-生命周期.md`
- `99-SKILLS治理/02-新网站接入分类.md`
- `99-SKILLS治理/03-测试评分漂移.md`
- `99-SKILLS治理/04-新增SKILL评分回测准入.md`
- `99-SKILLS治理/05-当前评分与回测结果.md`
- `99-SKILLS治理/06-网页逆向标准规划.md`（meta 规划入口）

## 新 Skill 准入

```
标准结构
  → quick_validate
  → 本地评分脚本
  → 正例/负例/历史回归回测
  → 更新评分结果
  → 进入对应分层目录
  → mklink /J 到 ~/.claude/skills/
```

评分参考 `skills-evaluation-governance/references/scorecard-rubric.md`，吸收 Karpathy 行为守则（4-通用规范层/karpathy-guidelines）。
