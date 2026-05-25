# Trip.com Route Decisions (Pre-experiment)

> **⚠️ 本文件路由决策基于公开资料推测,未经实战验证。真实接入时需对照 mitmproxy 抓包修正。**

| Date | Domain | Market | Locale | Currency | Stage | Official Page Route | API Route | Decision | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| 2026-05-25 | trip.com | GLOBAL | en-US | USD | register | 推测 m.trip.com/account/register | 推测 ProcoltolHandle.buileRequest → serviceCode 1xxxxxxx | unknown | external research |

## Decision Values (沿用模板枚举)

- new-api-enabled
- legacy-flow
- route-disabled
- no-real-flight
- market-not-supported
- waf-blocked
- unknown

## 一级路由 (端 → 入口)

| 触发 | 路由到 |
|---|---|
| 用户说"trip 注册接口" + Android | `mobile-app-reverse-delivery` (本次场景) |
| 用户说"trip 国际版机票搜索" + 浏览器 | 拆独立 web domain,走 `reverse-js-crawler` |
| 用户说"携程国内" | 拆独立 ctrip.com domain |

## 二级路由 (协议形态 → 工具链)

| 信号 | 路由 |
|---|---|
| 抓包看到 H5 同源接口 | 优先 `reverse-js-crawler` (大概率能复用 web 逆向成果) |
| 抓包看到自定义 UA + 接口域名异于 web | `rev-frida` 走 native 路径 |
| `assets/index.android.bundle` 存在 | `ast-deobfuscate` 解 RN bundle |
| sign 在 Java 层可看到 | `rev-frida` 单独搞定 |
| sign 入参在 Java 但值在 native 注入 | `rev-frida` + `rev-idapython` 双工具 |
| 加壳 (classes.dex 反编译异常) | `rev-dex-dumper` |

## 推测优先级 (基于 known-failures pre-004)

商业 OTA app sign 在 native 是大概率,因此**默认按 rev-frida + rev-idapython** 双工具准备。

如果实战发现 sign 居然在 Java 层 (惊喜路径),记得回填 route-decisions.md 把这个观察固化。

## 接口路由 (serviceCode → 业务) — 仅 1 条已知

| serviceCode | 业务 | 来源 |
|---|---|---|
| 17100101 | 酒店列表 | [AlienwareHe/awesome-reverse](https://github.com/AlienwareHe/awesome-reverse/blob/main/android/mt-ctrip-hook-capture.md) |
| ?xxxxxxx | 注册 send_sms | **未知** |
| ?xxxxxxx | 注册 verify_sms | **未知** |
| ?xxxxxxx | 创建账号 | **未知** |

实战阶段 A 第一件事: **抓全注册流程的 3-4 个 serviceCode,回填到本表**。

## Rules

- Official page route beats guessed API route. (实战时以抓包优先,推测仅供参考)
- Missing office/market/config errors can indicate wrong route.
- A route decision is not the same as fare availability.
- **本目录路由全部 `Decision: unknown`,因为未实战;真接入后逐条改为具体值**
