---
name: reverse-js-crawler
description: >-
  Use this skill for crawler reverse engineering and interface restoration: page reconnaissance, real API discovery, JavaScript sign/token/cookie analysis, browser runtime dependency tracing, request reproduction, batch collection, and verified Python/Node.js delivery. Trigger when the user asks for JS reverse, crawler reverse, API restoration, encrypted parameters, sign/x-sign/authKey/token, web data collection, turning a page into stable collection scripts, or Chinese requests such as 逆向采集, JS逆向, 接口还原, 接口复现, 加密参数, 补环境, 浏览器环境模拟, 请求复现, 批量采集, 数据清洗, or 采集脚本交付.
---

# Reverse JS Crawler

## Purpose

把页面、接口、抓包或 JS 线索还原成可运行、可验证、可维护的采集工程。不要只给方向；要闭环到脚本、测试、日志和失败边界。

## Workflow

1. 侦察页面与真实入口：
   - 从页面行为和网络请求确认真实数据入口。
   - 记录 URL、method、headers、query/body、initiator、返回结构。
   - 区分页面渲染数据、接口 JSON、WebSocket/SSE、静态配置。

2. 依赖分析和分类：
   - 识别 Header、Cookie、localStorage/sessionStorage、时间戳、nonce、UA、Referer、Origin。
   - 标出每个依赖来自服务端、浏览器环境、业务脚本还是第三方 SDK。
   - 分类为纯 HTTP、JS 加密、补环境、WAF、登录态、支付风险或不可自动化。

3. JS 加密还原：
   - 优先定位入口，再决定 AST 解混淆、Hook、补环境或直接复用。
   - 记录调用链、入参、出参、中间态、脚本 URL、函数位置。
   - 对 sign/token/cookie 生成逻辑给出可复现实现和对照样例。

4. 请求复现：
   - 最小可行请求先跑通，再加入重试、分页、并发、代理、日志。
   - 如果需要浏览器或 TLS 指纹，说明原因，并优先把可抽离部分下沉到纯 HTTP/Node runtime。

5. 批量采集与清洗：
   - 增加分页、断点续传、去重、字段校验、异常记录。
   - 输出结构化数据和统计摘要。

6. 交付：
   - 给出工程目录、运行方式、配置项、测试方式、已知失败边界。
   - 成功必须以真实目标请求被服务端接受为准，不以本地 token 生成成功为准。

## Success Criteria

- 已确认真实数据入口，不靠猜 URL。
- 已列出请求依赖和来源。
- 已区分普通加密、补环境、WAF、业务错误和测试数据问题。
- 已提供可运行复现和至少一次稳定性验证。
- 已把测试中的失败模式写入站点经验库或 eval backlog。

## Tool Policy

- 使用 `js_reverse` MCP 做页面打开、网络拦截、Hook、运行时变量、调用栈、Cookie/storage 观察。
- 使用仓库搜索和静态分析定位脚本入口。
- 遇到浏览器环境依赖时使用 `env-patch` 思路把官方 JS 搬到 Node 补环境运行。
- 不要求用户手工抓包，除非当前环境无法访问目标页面并且缺少任何样本。

## Boundaries

- 这是逆向采集 Skill，不是通用编码 AGENT。
- 不把项目代码风格规则写进这里；编码规则后续放 AGENT。
- 不把 WAF/Incapsula/Reese84 深度风控细节堆在这里；遇到这类问题切到 `imperva-waf-reese84`。

## Governance

If the user asks for a full website-to-service delivery with 314 framework, search/cart/order/payment stages, or long-term API service output, use `website-314-api-delivery` as the orchestrator and use this skill only for the reverse/crypto parts.

- Version: 0.2.0
- Status: scorecard baseline
- Site memory: write normal test failures to `站点经验库/<domain>/` when they can affect future same-site work.
- Backtest: run positive, negative, and regression evals after changing trigger words or workflow.
- CI: use Skill Bench or local backtest; quick_validate must pass before accepting changes.

## References

- `references/workflow.md`: 完整逆向交付流程。
- `references/testing.md`: 请求复现和批量采集测试要求。
- `references/governance.md`: versioning, change log, Skill Bench, GitHub CI, quick_validate, and drift-test policy.

