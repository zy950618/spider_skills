---
name: site-api-adapter
description: >-
  Use this skill to turn reverse-engineering findings into a reusable site API adapter: adapter.yaml, request/response schema, route classification, prompt-router rules, runbook, smoke tests, and service boundary documentation. Trigger when the user asks to standardize a site, build an adapter, define API protocol, create prompt-router output, productize crawler reverse results into a maintainable interface, or Chinese requests such as 接口化沉淀, 站点接口化, adapter标准化, adapter.yaml, prompt-router, API协议模板, runbook, schema沉淀, 多站点复用, or 逆向结果工程化.
---

# Site API Adapter

## Purpose

把单站点逆向结果升级为可复用、可回归、可交接的接口化单元。这个 Skill 关注沉淀和标准化，不负责深度破解某个 token。

## Workflow

1. 输入归档和分类：
   - 站点信息、页面入口、接口列表、参数依赖、认证/风控状态、样本响应。
   - 标记 market、locale、currency、stage、protection、framework。

2. 生成 adapter：
   - `adapter.yaml`：站点、市场、入口、接口、路由、依赖、风控类型、限流策略。
   - `schema.json`：请求/响应结构、必填字段、错误码、字段映射。
   - `runbook.md`：如何验证、如何排查、如何扩展。

3. 设计 prompt-router：
   - 把用户请求分类为纯 HTTP、JS runtime、浏览器诊断、WAF 专项、314 交付、不可自动化。
   - 输出 JSON，不能只输出自然语言。

4. 写 smoke tests：
   - 至少覆盖一个成功路径、一个业务错误、一个保护/不可用路径。
   - 记录稳定性循环的 exact code/message/count。

5. 维护边界：
   - adapter 只描述站点能力和调用规范。
   - 加密实现放 crypto/runtime。
   - 业务服务放 services。
   - 反爬专项放 anti_bot。

## Success Criteria

- adapter 能表达接口、依赖、保护、路由、测试和失败边界。
- prompt-router 能输出结构化分类，不靠自然语言猜测。
- 已区分 adapter 沉淀、JS 逆向、WAF 专项和 314 服务化。
- 已把站点/市场差异写入站点经验库。
- 已有 smoke、negative、regression 或 boundary eval。

## Boundaries

- 这是接口化沉淀 Skill，不是 token 破解 Skill。
- 不负责具体 WAF token 逆向；遇到 WAF 切到 `imperva-waf-reese84`。
- 不负责完整 314 服务交付；遇到 314 全流程切到 `website-314-api-delivery`。

## Governance

If the user asks for implementation through the 314 base framework, do not stop at adapter design. Use `website-314-api-delivery` as the orchestrator, then produce adapter/schema/runbook as part of the delivery.

- Version: 0.2.0
- Status: scorecard baseline
- Site memory: adapter decisions should update `站点经验库/<domain>/route-decisions.md` and `market-matrix.md`.
- Backtest: include adapter-from-notes, prompt-router, negative token-reverse, and regression classification evals.
- CI: use Skill Bench or local backtest; quick_validate must pass before accepting changes.

## References

- `references/adapter-schema.md`: adapter 字段建议。
- `references/prompt-router.md`: 分类输出规范。
- `references/governance.md`: versioning, change log, Skill Bench, GitHub CI, quick_validate, and drift-test policy.

