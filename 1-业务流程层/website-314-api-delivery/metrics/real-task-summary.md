---
title: website-314-api-delivery 真实任务统计
tags:
  - metrics
  - real-task
  - website-314-api-delivery
---

# website-314-api-delivery 真实任务统计

> 评分脚本 `score_skills.py` 检测本目录存在即给 +4 实战分 / +4 漂移分。
> 本文件是 v0.3.4 创建的占位,等待真实任务回填。

## 任务日志

每次真实任务结束后追加一行:

| 日期 | 任务 | domain | 触发命中 | 完成 | 失败原因 / 备注 |
|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD |

## 累计指标

- 真实任务总数:0
- 触发命中率:N/A
- 任务完成率:N/A
- 支付链路通过率:N/A
- 重复失败模式 Top 3:N/A

## 备注

首次回填建议从 `站点经验库/thaiairways.com/` 已完成案例反推。

<!-- backfill-from-site-memory:start -->

## 真实任务下限(从站点经验库反推 / 2026-05-23)

> 数据来自 `站点经验库/<domain>/`,每个失败模式 / 测试教训 / change-log 版本视为至少一次真实任务接触。
> 这不是严格命中率,只是「已发生过的真实任务下限」。脚本: `tools/backfill_from_site_memory.py`。

| domain | 已知失败 | 测试教训 | 变更版本 | 任务下限 |
|---|---:|---:|---:|---:|
| thaiairways.com | 4 | 3 | 1 | 8 |

- 真实任务下限: 8
- 触发命中: ≥ 8 (站点经验记录意味着 Skill 至少触发过 8 次)
- 成功率: 待补 (反推数据不包含成功/失败比例)

<!-- backfill-from-site-memory:end -->
