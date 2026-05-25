# Trip.com Test Log Lessons (Pre-experiment)

> **⚠️ 本接入未跑真实抓包/逆向。本文件记录"基于外部研究做了什么 + 真实接入时预期会撞到什么"。**

## Test Run

- date: 2026-05-25
- domain: trip.com
- market: global
- locale: en-US
- currency: USD
- stage: 阶段 0 (前期资料收集,未进入抓包)
- command/API: N/A
- test type: **none — research only, no actual HTTP/service test**

## 本次"接入"做了什么

- 用 WebSearch 收集 6 条 Trip.com / Ctrip 公开资料 (GitHub repo / Medium / CSDN / Ctrip 官方文档)
- 整理为 6 条预案性 known-failures (pre-001 到 pre-006),每条标 source + confidence
- 写 site-memory.md 顶部明确 Evidence Provenance,告诉所有后续读者本目录是 external research 不是实战
- 设 `_platform.yaml: app`,让 score_skills.py 把 trip.com 归入 mobile platform

## 本次没做什么 (Honesty)

- ❌ 没下载 / 没解包 trip.com APK
- ❌ 没跑 Frida hook
- ❌ 没用 mitmproxy 抓任何请求
- ❌ 没分析任何 .so 文件
- ❌ 没获得任何注册接口的真实 sign 值
- ❌ 没产出 fixtures/snapshots 真实样本
- ❌ 没跑 site-api-adapter 输出 adapter.yaml

## Extracted Pattern (基于公开资料的归纳)

- symptom: 商业 OTA app 标准防护组合 (SSL pinning + root detect + anti-frida + native sign + device fingerprint 节流)
- repeated how many times: 多个公开案例显示这是 Ctrip 系一贯模式
- changed variables: 不同业务 serviceCode 不同
- stable variables: 加密入口类名 `ctrip.business.comm.ProcoltolHandle` 大概率稳定
- suspected class: native crypto + 自研风控 SDK
- confirmed class: 暂无 (无实战 confirm)
- action: 列入 known-failures pre-001~pre-006 作为接入前 checklist

## 真实接入时预期撞到的坑 (按出现概率排序)

1. **SSL Pinning** — pre-001。第一次连 mitmproxy 时 100% 触发。bypass 后才能看流量
2. **Root Detection** — pre-002。Magisk 隐藏后大概率绕过,但 Ctrip 可能加强检测
3. **Anti-Frida** — pre-003。需要 magisk-frida / 改 frida-server 名
4. **Native sign 算法** — pre-004。Java 层 hook 只能拿入参,sign 本身要 Ghidra 看 .so
5. **Device fingerprint 节流** — pre-005。注册类接口 replay 必撞,需要 hook 设备指纹刷新
6. **协议形态判别** — pre-006。Donut 引擎让 H5/Native 边界模糊,阶段 A 要小心

## Follow-up (真实接入完成后)

- update site memory: 把推测字段改为实测;补 API hosts 实际值;补 sign 算法位置
- update known failures: 每条 source 改为 `local experiment`,confidence 升 HIGH;新失败追加
- update Skill reference: mobile-app-reverse-delivery `references/airline-app-patterns.md` 补 Trip.com 节
- add eval: 至少 3 个 (trip-001 / trip-003 / trip-005 见 eval-backlog.md)
- update version: change-log.md v0.1.0 (从 v0.0.1 预案 → v0.1.0 实战)

## 给评分体系的诚实信号

接入 trip.com 后,`mobile-app-reverse-delivery` 的 `applicable_domains` 会从 `[]` 变成 `[trip.com]`,
但因为 fixtures 为空 + real-task-summary 为空,score_skills.py 应该会把 evidence 维度的得分**打折**
(具体多少折取决于评分脚本对 external research 的判定)。

**这是预期行为**:不让"没真打过仗"的 skill 拿到"真打过仗"的分。
