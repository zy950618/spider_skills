---
name: imperva-waf-reese84
description: >-
  Use this skill for Imperva/Incapsula/Reese84, x-d-token, reese84 cookies, SWJIYLWA/CWUDNSAI/SWUDNSAI challenge HTML, browser fingerprint simulation, token cache identity, and WAF acceptance testing. Trigger when the user asks to solve 84 shield, Reese84, Incapsula, WAF challenge, anti-bot token rejection, dynamic fingerprinting, protected flight/booking APIs, or Chinese requests such as 84盾, 84风控, Reese84逆向, Incapsula反爬, Imperva风控, x-d-token, reese84 cookie, WAF挑战, 风控token, 浏览器指纹, 指纹模拟, 反扒, 反爬, or token被拒.
---

# Imperva WAF Reese84

## Purpose

处理 WAF/Reese84 时必须区分三件事：本地能生成 token、挑战端点返回 token、业务接口真正接受请求。只有第三个才算成功。

## Workflow

1. 识别保护类型和分类：
   - `403/429`
   - `text/html` but expected JSON
   - `x-iinfo`
   - `_Incapsula_Resource`
   - `SWJIYLWA`, `CWUDNSAI`, `SWUDNSAI`
   - `Pardon Our Interruption`

2. 抽取官方 challenge：
   - 从 HTML 中提取当前脚本 URL。
   - 不手写 token 格式，优先运行官方 challenge JS。
   - 记录 challenge host、cookie domain、script path、post endpoint。

3. 补浏览器环境：
   - 模拟 `window/document/navigator/location/screen/performance/crypto` 等依赖。
   - 对齐 UA、client hints、language、timezone、screen、hardware、referer、origin、sec-fetch。
   - 浏览器只用于诊断或显式 fallback，不依赖用户真实浏览器缓存。

4. 按身份缓存：
   - cache key 至少包括 proxy/IP、UA、client hints、market、host/domain、session scope。
   - 不跨并发用户共享一个浏览器 session 或 cookie jar。
   - 遇到 WAF HTML、403、x-iinfo、challenge marker 强制刷新。

5. 验证接受度：
   - token 生成后必须请求目标业务接口。
   - 如果业务接口仍然返回 challenge，返回保护失败和诊断，不伪造业务成功。

## Success Criteria

- 已证明 challenge token/cookie 生成。
- 已证明目标业务接口是否接受该 token/cookie。
- 已区分 WAF、路由错误、payload 错误、IP/proxy 和业务无数据。
- 已记录 cache key、刷新原因和重试边界。
- 已把测试失败写入站点经验库或 eval backlog。

## Boundaries

- 这是反爬/WAF Skill，不是普通采集 Skill。
- 不把普通 sign/token 任务都升级成 WAF 处理。
- 不把代码工程风格规则放进这里；后续 AGENT 处理编码规则。

## Governance

If the user asks for a full website-to-service delivery with 314 framework, search/cart/order/payment stages, or long-term API service output, use `website-314-api-delivery` as the orchestrator and use this skill only for WAF/anti-bot parts.

- Version: 0.2.0
- Status: scorecard baseline
- Site memory: write WAF markers and stage-specific failures to `站点经验库/<domain>/`.
- Backtest: include token-not-accepted, cache identity, browser policy, and negative basic-sign regression evals.
- CI: use Skill Bench or local backtest; quick_validate must pass before accepting changes.

## References

- `references/architecture.md`: 隔离 anti-bot、business service、reverse runtime。
- `references/testing.md`: WAF token 接受度测试。
- `references/governance.md`: versioning, change log, Skill Bench, GitHub CI, quick_validate, and drift-test policy.

