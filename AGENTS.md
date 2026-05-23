# my_reverse_skill — AGENTS.md

本仓库是逆向工程 SKILLS 总库,18 个 skill 分 5 个分层。本文件是 OpenAI Codex CLI 的入口约定。

## 接到逆向任务时

1. 读 `99-SKILLS治理/06-网页逆向标准规划.md` 输出 5 阶段规划
2. 按 `00-SKILLS索引.md` 选 skill
3. 进入实现前 Read `4-通用规范层/karpathy-guidelines/SKILL.md` 确认 4 原则
4. 遇运行时问题(断点/时间/cookie/TLS 指纹/风控/接口变更)Read `99-SKILLS治理/10-逆向运行时常见问题.md`
5. 完成前跑 `python tools/verify_delivery.py --domain <domain>` 自验

## 强制约束

- 真实扣款不在自动化环境跑,除非用户明示授权
- 不把"评分高"等同于"任务真实成功"
- 不把一次失败硬编码成只适配一个站点的规则
- 任务结束按 `CLAUDE.md` 五步沉淀

## 关键工具

- `tools/replayer/snapshot_replay.py`: replay 验证
- `tools/replayer/snapshot_diff.py`: 字段 diff
- `tools/replayer/schema_alert.py`: 接口版本变更告警
- `tools/replayer/consistency_report.py`: 一致性报告
- `tools/verify_delivery.py`: 完成度 5 维自验
- `tools/post_task_reminder.py`: Stop hook 沉淀提醒
- `tools/sync_site_memory.py`: 跨项目同步 site memory
- `tools/ci_gate.py`: CI 评分阈值
- `1-业务流程层/skills-evaluation-governance/scripts/score_skills.py`: skill 评分

## 仓库分层

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口(5 个 skill) |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具(4 个) |
| 3 | `3-移动逆向工具层/` | Android/iOS/Native 工具(7 个) |
| 4 | `4-通用规范层/` | 基础层规范(karpathy-guidelines) |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化(site-api-adapter) |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入/运行时方法论 |

完整规则见 `CLAUDE.md`。
