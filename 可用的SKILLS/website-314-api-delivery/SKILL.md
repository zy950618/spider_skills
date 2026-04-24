---
name: website-314-api-delivery
description: >-
  Use this skill when a user gives a new website or existing target site and asks for end-to-end pure-interface implementation, API service delivery, or integration with the 314 base framework. Trigger for requests such as new website crawler, pure API implementation, site-to-service delivery, search/cart/order/payment flow, flight booking interface, 314 framework, flight_cwl_common_314, 接口实现, 纯接口, 网站接入, 新站点接入, 查询/加车/生单/支付, 加解密全部实现, 314基础框架, 提供接口, 服务化, or 长期可维护接口交付.
---

# Website 314 API Delivery

## Purpose

把一个新网站从“给 URL / 业务目标”推进到“纯接口实现 + 314 框架服务化 + 测试闭环 + 可持续沉淀”。这个 Skill 是总控流程，用来调度逆向、反爬、接口化、测试和长期治理。

## When To Use

使用这个 Skill 处理类似任务：

- “给你一个网站，做纯接口实现”
- “实现查询、加车、生单、支付”
- “加解密全部实现”
- “最后用 314 基础框架提供接口”
- “把这个站点接入长期可维护的服务”

## Skill Routing

按问题类型调用已有 Skill：

- 真实接口、参数、JS 加密：`reverse-js-crawler`
- WAF、84盾、Reese84、Incapsula、x-d-token：`imperva-waf-reese84`
- adapter、schema、runbook、prompt-router：`site-api-adapter`
- 评分、eval、漂移测试、版本治理：`skills-evaluation-governance`

不要把所有细节塞进一个 Skill。这个 Skill 负责分层、排期、验收和交付边界。

## Delivery Workflow

1. 新站点建档：
   - 记录目标 URL、业务目标、市场/语言、是否登录、是否支付、是否有真实交易风险。
   - 明确目标接口阶段，例如 search、availability、fare、cart、traveler、order、payment。
   - 先查 `../站点经验库/<domain>/`，同域名不同 market/locale/currency 也要分开看。
   - 如果没有站点目录，按 `../站点经验库/_templates/` 建立测试期记忆文件。

2. 页面真实流程侦察：
   - 从官方页面入口开始，不直接猜 API。
   - 记录页面路由、配置、feature flag、rollout、market rule。
   - 如果页面没有真实业务能力，不能伪造成功。

3. 接口识别与分类：
   - 纯 HTTP：直接复现。
   - JS 加密：定位入口并复现。
   - 浏览器环境：抽官方 JS 到 Node 补环境。
   - WAF/反爬：切到 WAF 专项。
   - 业务路由错误：先修路由，不硬补参数。

4. 业务阶段实现：
   - 查询：航线/日期/人数/舱位/币种/市场。
   - 加车：选中 bound/fare/offer 后创建 cart 或 booking session。
   - 生单：旅客、联系人、行李、附加服务、订单确认。
   - 支付：优先做 sandbox/dry-run/支付前置接口；真实扣款必须人工授权，不能默认执行不可逆交易。

5. 314 框架接入：
   - 只有用户明确要求 314 或项目已使用 314 时接入。
   - 保留 314 的 trace/session id、日志、代理、请求执行器、并发生命周期。
   - 服务层只放业务编排；加解密放 crypto/runtime；WAF 放 anti_bot。

6. 测试闭环：
   - service-level 单测。
   - HTTP API 测试。
   - 稳定性循环。
   - WAF 接受度测试。
   - 失败路径测试。
   - 从测试日志提炼失败模式：symptom、stage、market、currency、status、marker、root cause、correct handling。

7. 沉淀：
   - 生成 adapter/runbook/case notes。
   - 更新相关 Skill references。
   - 把新失败点加入 eval。
   - 更新版本号和变更记录。
   - 写回 `站点经验库/<domain>/known-failures.md`、`test-log-lessons.md`、`eval-backlog.md`、`change-log.md`。

## Success Criteria

成功不是“脚本能跑一下”，而是：

- 目标业务接口真实接受请求。
- API 返回结构稳定。
- 日志能定位入参、session_id、阶段、耗时、返回码、错误信息。
- 失败时能区分业务错误、路由错误、加密错误、WAF、IP、支付不可逆风险。
- 结果能沉淀成下一次复用的 Skill/eval。
- 同站点同 market/locale/currency/stage 的已知失败在执行前被检查，并且测试后有写回记录。

## Boundaries

- 这是新站点到接口服务的总控 Skill，不替代编码 AGENT。
- 不把 Karpathy 风格编码纪律写进这里；后续放 AGENT。
- 支付阶段默认按 sandbox/dry-run/支付前置验证处理，真实扣款必须明确授权并满足合法合规要求。

## Governance

- Version: 0.2.0
- Status: site-memory baseline
- Change log: record material trigger, workflow, reference, and eval changes in `references/governance.md`.
- Drift tests: rerun evals after changing descriptions, adding new cases, or after important real-world failures.
- Review cadence: update examples and negative triggers when repeated user corrections show a gap.
- Site memory: read and write `../站点经验库/<domain>/` during normal testing, not only after production incidents.

## References

- `references/intake-and-routing.md`: 新站点接入和分类规则。
- `references/314-integration.md`: 314 框架接入边界。
- `references/delivery-checklist.md`: 查询、加车、生单、支付、测试交付清单。
- `references/test-log-mining.md`: 从测试日志提炼失败模式并回写经验库。
- `references/github-ci.md`: GitHub Skill Bench CI 操作流程。
- `references/governance.md`: 版本、变更、漂移测试策略。
