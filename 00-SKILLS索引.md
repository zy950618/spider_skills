---
title: 可用的 SKILLS 索引
tags:
  - codex
  - skills
  - reverse
  - skill-bench
  - governance
---

# 可用的 SKILLS 索引

这个目录只放 **SKILLS**：也就是可触发、可复用、可评测、可长期进化的任务能力包。

后续的 **AGENT / AGENTS** 另建目录处理，那里放写代码行为规则、项目协作规则、提交规范、代码审查规则。代码工程规则和逆向采集技能不要混在一个文件里。

## 核心边界

- `SKILLS`：解决某一类任务，例如 JS 逆向、反爬 token、站点接口化、314 服务化、技能评分。
- `AGENT / AGENTS`：约束编码代理如何思考和改代码，例如谨慎假设、最小改动、测试闭环。
- `references/`：技能被触发后按需读取的详细资料。
- `evals/`：Skill Bench 或人工评分用例。
- `governance.md`：版本、变更记录、漂移测试策略。

## 当前可用技能

| Skill | 适用场景 | 主要来源 |
|---|---|---|
| `website-314-api-delivery` | 新网站 -> 纯接口 -> 查询/加车/生单/支付 -> 314 框架接口交付 | 新站点长期接入流程、Thai Airways 需求模型 |
| `reverse-js-crawler` | 页面侦察、真实接口识别、签名/token 还原、采集脚本交付 | 爬虫逆向 Agent、JS 逆向模板、Thai Airways 复盘 |
| `imperva-waf-reese84` | Imperva/Incapsula/Reese84/x-d-token/WAF challenge 深度处理 | Thai Airways 反爬处理经验 |
| `site-api-adapter` | 把单站点逆向经验沉淀为 adapter、schema、runbook、prompt-router | 通用站点接口化分析体系 |
| `skills-evaluation-governance` | 给技能评分、补 eval、接 Skill Bench、判断是否能直接安装 | SKILLS 评分与能力评估 |

## 新网站接入入口

以后如果要处理一个新网站，优先从 `website-314-api-delivery` 开始。

典型输入：

```text
目标网站：https://www.example.com/
目标：纯接口实现查询、加车、生单、支付
要求：加解密全部实现，最后使用 314 基础框架提供接口
```

处理顺序：

```text
website-314-api-delivery
  -> reverse-js-crawler
  -> imperva-waf-reese84（如果有 WAF/84盾/风控）
  -> site-api-adapter
  -> skills-evaluation-governance
```

## 长期进化闭环

每次真实任务结束后，都要问：

- 有没有新触发词？
- 有没有新失败类型？
- 有没有新分类规则？
- 有没有新加解密或反爬模式？
- 有没有应该加入 eval 的场景？
- 是否需要升级版本号？

固定沉淀路径：

```text
真实任务
  -> 归类
  -> 执行
  -> 记录失败点
  -> 更新 references
  -> 增加 eval
  -> 评分
  -> 版本升级
  -> 漂移测试
```

## 官方 CI 跑分是什么意思

“结构已准备好，但还没接官方 CI 跑分”指的是：

- 本地目录已经有 `SKILL.md` 和 `evals/`，具备被 Skill Bench 评测的结构。
- 但官方 Skill Bench 通常通过 GitHub Actions 在仓库里运行，需要仓库可见路径，例如 `skills/<skill-name>/`。
- GitHub Actions 还需要配置模型 API key secret，例如 `ANTHROPIC_API_KEY`。
- 本地结构校验只能说明“格式正确”，不等于官方模型已经对 evals 跑过分。

如果要做正式长期跟踪，需要把这些 Skill 镜像到一个 Git 仓库，并配置 PR 触发和定时触发的 Skill Bench workflow。

## 治理文档

- `99-SKILLS治理/01-生命周期.md`
- `99-SKILLS治理/02-新网站接入分类.md`
- `99-SKILLS治理/03-测试评分漂移.md`
- `99-SKILLS治理/04-新增SKILL评分回测准入.md`
- `99-SKILLS治理/05-当前评分与回测结果.md`

这些是 SKILLS 的治理说明，不是 AGENT 编码规则。

## 新 Skill 准入

后续每次新增 Skill，必须先过准入：

```text
标准结构
  -> quick_validate
  -> 本地评分脚本
  -> 正例/负例/历史回归回测
  -> 更新评分结果
  -> 再进入可用目录
```

评分参考 `skills-evaluation-governance/references/scorecard-rubric.md`，同时吸收 Karpathy 风格的行为检查：不默默假设、不过度复杂、精准边界、目标驱动验证。



## GitHub CI ????

????????

```text
website-314-api-delivery/references/github-ci.md
```

?????

1. ???????? `crawler-skills`?
2. ??? Skill ????? `skills/` ???
3. ?? `.github/workflows/skill-bench.yml`?
4. ? GitHub Secrets ??? `ANTHROPIC_API_KEY`?
5. ? PR???????????????
