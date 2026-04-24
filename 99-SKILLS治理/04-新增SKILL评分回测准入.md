---
title: 新增 SKILL 评分回测准入
tags:
  - skills
  - scorecard
  - backtest
  - governance
---

# 新增 SKILL 评分回测准入

每个新的 Skill 进入 `可用的SKILLS/` 前，必须先评分和回测。

## 准入结论

| 分数 | 状态 | 处理 |
|---:|---|---|
| 90-100 | 可用稳定 | 可进入可用目录，后续做漂移测试 |
| 80-89 | 可用基线 | 可进入，但必须标记待补 eval/回测 |
| 70-79 | 候选 | 只能放候选区，不进入可用 |
| 50-69 | 笔记/模板 | 需要重写成 Skill |
| <50 | 原始材料 | 只能作为 reference 来源 |

## 硬性门槛

新 Skill 至少满足：

- `SKILL.md` 存在。
- frontmatter 有 `name` 和 `description`。
- `description` 同时描述能力和触发场景。
- `agents/openai.yaml` 存在。
- `references/` 至少 2 个文件。
- `evals/` 至少 3 个用例。
- 至少 1 个负例 eval。
- 至少 1 个边界/回归 eval。
- `references/governance.md` 存在。
- quick_validate 通过。

## 评分维度

| 维度 | 分值 | 检查点 |
|---|---:|---|
| 结构有效性 | 15 | 标准目录、frontmatter、agents、references |
| 触发准确性 | 15 | 中英文触发词、正例、负例、近似负例 |
| 渐进披露 | 10 | `SKILL.md` 简洁，细节放 references |
| 执行行为 | 15 | 不假设、不混淆边界、有成功标准 |
| 回测覆盖 | 20 | eval 数量、criteria 可判定、回归场景 |
| 经验沉淀 | 10 | site memory、known failures、change log |
| CI/漂移 | 10 | GitHub CI 或本地回测流程 |
| 可维护性 | 5 | 版本、变更、命名、可读性 |

## Karpathy 风格检查

这些来自 Karpathy 风格编码准则，但用于评测 Skill 行为质量：

- 不默默假设：Skill 要要求分类、证据和边界。
- 不过度复杂：Skill 不要吞掉不属于自己的任务。
- 精准处理：一个 Skill 只解决一类问题。
- 目标驱动：必须定义可验证成功标准。

## 回测要求

新增 Skill 时必须跑：

- 自身 eval。
- 至少 1 个相邻 Skill 的负例。
- 至少 1 个历史失败回归例。
- quick_validate。
- 本地结构评分脚本。

如果接 GitHub CI，则 PR 必须跑 Skill Bench。

## 新增 Skill 记录

每次新增 Skill 后，在 `05-当前评分与回测结果.md` 追加：

- Skill 名称。
- 版本号。
- 新增原因。
- 评分。
- 回测结果。
- 未覆盖风险。
- 后续补强项。

