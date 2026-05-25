# Trip.com Domain Memory

> **⚠️ Evidence Provenance Notice**
>
> 本目录所有内容来源为 **公开技术资料** (GitHub awesome-reverse repo / Medium 技术博客 / CSDN 行业文章 / Ctrip 官方隐私政策),**不是**本仓自身的抓包/逆向产出。
>
> 整体 confidence: **LOW-MEDIUM**。每条具体陈述在 known-failures.md 标注 `source` + `confidence`。
>
> 真实接入需用户自备 root Android + Frida + IDA/Ghidra 环境。预案性数据用于:
> 1. 真正动手前的可行性评估
> 2. 接入时撞到的坑可以快速对照已知模式
> 3. 评分体系把 trip.com 列入 `applicable_domains` 时给到 mobile skill 一份**打折的** evidence (而非 0)

---

## Site

- domain: trip.com
- aliases: Trip.com 国际版,Ctrip 国际版 (与国内 ctrip.com 拆开)
- official entry pages: https://www.trip.com/ , Google Play `ctrip.english`
- API hosts: 推测 m.trip.com / api.trip.com (未实测)
- framework target: standalone (mobile app,非 314)
- Android 包名: `ctrip.english`
- 公司: Trip.com Group Limited (上海携程 + 新加坡注册)
- 跨平台架构: 部分 H5/RN/Donut 混合 (来源:Trip Tech Donut 公开博客)

## Markets

| Market | Locale | Currency | Status | Notes |
|---|---|---|---|---|
| GLOBAL | en-US | USD | unknown | 主市场 |
| HK | en-HK / zh-HK | HKD | unknown | |
| TW | zh-TW | TWD | unknown | |
| SG | en-SG | SGD | unknown | |
| TH | th-TH | THB | unknown | |
| JP | ja-JP | JPY | unknown | |
| KR | ko-KR | KRW | unknown | |

## Stages (注册流程预期 3 步)

| Stage | Status | Skill | Notes |
|---|---|---|---|
| send_sms | not started | mobile-app-reverse-delivery | 推测 serviceCode 1xxxxxxx |
| verify_sms | not started | mobile-app-reverse-delivery | 推测独立 sign |
| create_account | not started | mobile-app-reverse-delivery | 完成注册 |

## Protection (推测)

- WAF: 未知 (推测有自研风控,见余炜 CSDN 文章)
- JS crypto: 部分 (Donut 引擎部分页面是 H5/RN)
- browser environment: 不适用 (主体是 Android native)
- captcha: 推测有 (注册类接口商业 OTA 通用)
- proxy/IP sensitivity: 推测高 (KYC + 风控)
- 设备指纹: Android ID 限频 ≤2/打开 (Ctrip 隐私政策证实)
- SSL pinning: 推测 100% 有
- Root detection: 推测有 RootBeer-style
- Anti-Frida: 推测有

## 关键加密入口 (推测)

| 层 | 位置 | 来源 | confidence |
|---|---|---|---|
| Java | `ctrip.business.comm.ProcoltolHandle.buileRequest` | [AlienwareHe/awesome-reverse](https://github.com/AlienwareHe/awesome-reverse/blob/main/android/mt-ctrip-hook-capture.md) | HIGH |
| Java | `realServiceCode` 路由 key (例 17100101=酒店列表) | 同上 | HIGH |
| Native | `libcomponent-base.so` / `libcommon.so` 之类 | 商业 OTA 通用模式 | LOW |

## Current Rules

- Do not assume one market works because another market works. (Trip.com 多市场风控可能不同)
- Do not treat token generation as business success. (sign 算出来 ≠ 注册成功,后端还会校验设备/IP/手机号)
- Do not submit real payment without explicit approval. (本接入为纯算法研究,不发真 SMS,不创建真账号)
- 阶段 A 协议判别完成前,不允许跳到阶段 B/C (mobile-app-reverse-delivery 强制)
- 凡 source: external research 的条目,**不能作为 "已验证" evidence 输出给评分体系**

## 入仓 Checklist (用户实战时按此清点)

- [ ] root Android 真机 + Magisk + Frida server 16.x
- [ ] mitmproxy CA 已装 + objection ssl-pinning bypass 跑通
- [ ] APKTool 解包,jadx 看 `ctrip.business.comm.ProcoltolHandle` 类
- [ ] Frida hook `buileRequest`,跑一次 send_sms,dump 入参
- [ ] 对比 mitmproxy 抓到的实际 HTTP 包,确认 sign 字段位置
- [ ] 写到 known-failures.md (此时 source 改为 `local experiment`,confidence 升 HIGH)
