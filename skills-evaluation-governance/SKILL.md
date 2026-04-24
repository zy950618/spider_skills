---
name: skills-evaluation-governance
description: >-
  Use this skill to score, refine, backtest, and govern Codex/Claude skills: assess whether notes are installable skills, create evals, prepare Skill Bench structure, compare SKILL.md quality, define trigger/negative-trigger tests, track drift, maintain versions, record changes, and enforce admission gates for new Skills. Trigger when the user asks to rate skills, use Skill Bench, convert notes into usable skills, evaluate trigger accuracy, maintain a skills library, score a new Skill before accepting it, run backtests, or Chinese requests such as SKILLS评分, 技能评分, 可用SKILLS, 新增Skill准入, Skill Bench跑分, 回测, 漂移测试, 长期治理, 版本号, 变更记录, 触发词优化, 负例测试, or 技能库治理.
---

# Skills Evaluation Governance

## Purpose

把经验笔记升级为可安装、可触发、可评测、可回测、可持续改进的 Skills。评分时必须区分笔记质量、Skill 包质量、Skill Bench 可跑性、站点经验沉淀和长期漂移风险。

新增 Skill 不能直接进入“可用”。必须先完成评分、回测、版本记录和准入判断。

## Rubric

Score separately:

- Knowledge quality: domain depth, examples, templates.
- Skill package quality: `SKILL.md`, frontmatter, concise workflow, references.
- Trigger quality: description can trigger correct tasks and avoid near-miss tasks.
- Eval quality: positive and negative prompts, criteria, repeatability.
- Site memory quality: test logs become known failures, market matrix, eval backlog, and change log.
- Operational quality: CI, drift tracking, versioning, install path.
- Karpathy behavior quality: assumptions surfaced, scope kept narrow, success criteria verifiable, changes traceable to the request.

## Workflow

0. 站点记忆评估：
   - 检查是否存在站点经验库、市场矩阵、已知失败、测试日志提炼、eval backlog、change log。
   - 判断同域名不同 market/locale/currency/stage 是否被分开治理。

1. 只读评估：
   - 统计 `SKILL.md`、`evals/`、`agents/openai.yaml`、`references/`。
   - 判断是笔记库、模板库，还是可安装 Skill。

2. 设计 eval：
   - 至少包含正例、边界例、负例。
   - criteria 要能客观判断，不写空泛评价。

3. 接 Skill Bench：
   - Skill 路径必须仓库可见。
   - CI 需要 API key secret。
   - 本地结构校验不等于官方跑分。

4. 迭代：
   - 根据失败 eval 调整 description 或 workflow。
   - 从正常测试日志提炼失败模式，写回站点经验库。
   - 不为了通过 eval 过拟合单个案例。

5. 新 Skill 准入：
   - 检查 `99-SKILLS治理/04-新增SKILL评分回测准入.md`。
   - 跑 quick_validate 和 `scripts/score_skills.py`。
   - 回测至少一个正例、一个负例、一个历史回归例。
   - 更新 `99-SKILLS治理/05-当前评分与回测结果.md`。

## Karpathy Checks

这些原则用于评价 Skill 行为，不替代后续 AGENT 编码规则：

- 不默默假设：Skill 要求先分类、列证据、标注未知。
- 不过度复杂：Skill 不吞掉相邻任务，复杂细节放 references。
- 精准处理：每个 Skill 只解决清晰边界内的问题。
- 目标驱动：必须有可验证成功标准和回测闭环。

## Success Criteria

- 新 Skill 没有绕过准入评分。
- 评分结果区分结构校验、本地回测和官方 Skill Bench 跑分。
- 每个 Skill 至少有正例、负例和回归/边界 eval。
- 测试日志中的重复失败能进入站点经验库或 eval backlog。
- 改动后版本、变更记录和漂移测试要求同步更新。

## Boundaries

- 用户只要求评分时，不改文件。
- 用户要求整合、创建、准入或治理时，才写入目标目录。
- AGENT 编码规则后续单独沉淀，不混入 Skill 评分包。
- 不把“本地格式通过”说成“官方 Skill Bench 已跑分”。

## Governance

When scoring crawler/reverse Skills, include site memory quality: test logs should produce known failures, market matrix updates, eval backlog entries, and version changes.

When a new real website task reveals a repeated gap, update the relevant Skill, add or revise evals, record the version change, and schedule drift testing. Do not let the skills library become static notes.

- Version: 0.2.0
- Status: admission-and-backtest baseline
- Change log: record material trigger, workflow, reference, score, and eval changes in `references/governance.md`.
- Drift tests: rerun evals after changing descriptions, adding new cases, or after important real-world failures.
- Review cadence: update examples and negative triggers when repeated user corrections show a gap.

## References

- `references/scorecard-rubric.md`: stricter scorecard and backtest rubric based on Skill Creator plus Karpathy-style behavior checks.
- `references/site-memory-scoring.md`: site memory, market matrix, test-log mining, eval backlog, and change-log scoring.
- `references/governance.md`: versioning, change log, and drift-test policy.
- `references/scoring-rubric.md`: scoring details.
- `references/skill-bench.md`: Skill Bench setup requirements.
