---
title: 站点经验库
tags:
  - skills
  - site-memory
  - crawler
  - reverse
---

# 站点经验库

这个目录记录 **测试阶段** 产生的站点经验，不依赖线上运行。

目标是让同一个网站、同类市场、同类币种、同类接口阶段不重复犯错。

## 维度

站点经验按这些维度拆分：

- domain：例如 `thaiairways.com`
- market：例如 `CN`、`JP`、`US`、`TH`
- locale：例如 `zh-CN`、`ja-JP`、`en-US`
- currency：例如 `CNY`、`JPY`、`USD`、`THB`
- stage：search、cart、order、payment
- protection：none、js-crypto、waf、reese84、captcha
- framework：standalone、314

## 固定文件

每个站点目录建议包含：

```text
site-memory.md
market-matrix.md
known-failures.md
test-log-lessons.md
route-decisions.md
eval-backlog.md
change-log.md
```

## 使用规则

在处理新网站或同网站新市场前，先查：

1. 是否已有 domain 目录。
2. 是否已有 market/locale/currency 记录。
3. 是否已有相同 stage 的 known failure。
4. 是否已有 eval backlog 尚未沉淀到 Skill。

测试完成后，必须写回：

1. 成功/失败摘要。
2. 从日志提炼的失败模式。
3. 是否更新 Skill。
4. 是否新增 eval。
5. 是否更新版本。

