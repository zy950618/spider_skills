# Governance: mobile-app-reverse-delivery

## Version

- 0.1.0 — initial scaffold（2026-05-21）

## Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-05-21 | 创建 skill，对标 website-314-api-delivery 的 mobile 端版本，主场景定位为航司 app 接口逆向交付 |

## Drift Test Policy

新案例完成后必须回归：

1. positive eval（航司 app + 已知签名定位）
2. negative eval（纯 web 任务被切到 reverse-js-crawler，本 skill 不应触发）
3. regression eval（H5 套壳类 app，确认本 skill 不会把所有 H5 都拦下来强制走 native 流程）

## Open Questions

- React Native 路径是否需要单独 skill？目前并入本 skill 的"H5 路径"分支处理。
- 越狱越来越难（Android 13+ / iOS 17+），未来是否需要 "non-root reverse" 路径？

## Real-Task Backlog

> 留白：每完成一个真实任务，在此记录学到的新模式，对 skill 做版本升级。
