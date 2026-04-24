# 314 Integration

## When To Use 314

Use 314 only when:

- the user explicitly asks for 314, `flight_cwl_common_314`, or 314 base framework
- the project already imports and depends on the 314 framework
- the final output must be an API service rather than a standalone crawler

## Service Boundaries

Recommended split:

```text
api/
  routes/<vendor>/
  services/<vendor>/
  anti_bot/<vendor>/
  crypto/<vendor>/
  tests/
reverse/<vendor>/
```

Responsibilities:

- routes: HTTP endpoint mapping and request/response DTOs
- services: business flow orchestration
- anti_bot: WAF, captcha, Reese84, challenge state
- crypto: sign/token/cookie generation that is not WAF-specific
- reverse: extracted scripts, Node runners, debug artifacts
- tests: service-level and HTTP API tests

## Logging Requirements

Chinese API logs should include:

- 接口名称
- 路径
- session_id / trace_id
- 入参摘要
- 阶段
- 耗时
- 返回码
- 信息 / 原始信息
- 返回摘要

Do not log full tokens, cookies, card data, or passenger sensitive data.

## Test Requirements

- direct service tests
- HTTP router tests
- 2-3 stability loops for key endpoints
- negative tests for invalid route/date/passenger
- WAF marker tests when applicable
- payment dry-run or sandbox tests only, unless real payment is explicitly authorized

