# Trip.com Change Log

## Version Changes

| Version | Date | Skill | Change | Reason | Eval Added |
|---|---|---|---|---|---|
| 0.0.1 | 2026-05-25 | mobile-app-reverse-delivery | 预案性接入 (external research) | 用户选 B 路径:无环境时用公开资料先建框架 | 0 (列 6 项到 eval-backlog) |

## v0.0.1 — 2026-05-25 — 预案性接入 (external research)

- 创建 `站点经验库/trip.com/` 目录骨架 (从 `_templates/` 复制 7 文件)
- `_platform.yaml`: platform=app
- `site-memory.md`: 写明 Evidence Provenance 声明 (本目录全为外部研究,非实战)
- `known-failures.md`: 6 条预案性条目 (pre-001 到 pre-006),涵盖 SSL pinning / root detection / anti-frida / native sign / device fingerprint / Donut 协议判别
- `test-log-lessons.md`: 列已做/未做/真实接入预期撞到的坑
- `route-decisions.md`: 二级路由表 + 1 条已知 serviceCode (17100101=酒店列表)
- `market-matrix.md`: Trip.com 国际 7 市场矩阵
- `eval-backlog.md`: 6 项待补 eval (全 todo,等实战)

来源: [AlienwareHe/awesome-reverse](https://github.com/AlienwareHe/awesome-reverse/blob/main/android/mt-ctrip-hook-capture.md) + [Vikas Gupta Medium](https://medium.com/@vikasg603/reverse-engineering-a-travel-apps-signature-logic-ssl-pinning-native-obfuscation-0f1c890dba0b) + [Ctrip 隐私政策](https://docs.c-ctrip.com/files/6/unc_agreement_pdf/1tm0d12000lvd5viaF670.pdf) + [余炜 CSDN](https://blog.csdn.net/xiaoxiaoniaoer1/article/details/103757270) + [Trip Tech Donut](https://medium.com/@trip-tech/how-trip-com-group-achieved-99-code-reuse-building-a-high-performance-cross-platform-market-55319b260b68)

## Version Rules

- patch: wording, typo, small trigger adjustment
- minor: new workflow, reference, eval category, site memory rule
- major: stable across multiple real tasks and drift tests

## 下一步 (用户真实环境就绪时)

- 准备 root Android + Magisk + Frida 16.x + IDA/Ghidra
- 解包 Trip.com APK (`ctrip.english` Google Play)
- 跑通 SSL pinning bypass + Frida attach
- hook `ctrip.business.comm.ProcoltolHandle.buileRequest`,dump 注册接口入参
- 若 sign 在 native,Ghidra 看相关 .so
- 实战发现的失败把 known-failures.md 对应条目的 source 改为 `local experiment`
- 升 v0.1.0 (从 0.0.x external research → 0.1.0 first local experiment)
