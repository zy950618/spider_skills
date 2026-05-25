# Trip.com Market Matrix

> 来源: [Trip.com 官方介绍](https://www.trip.com/) + [Grokipedia](https://grokipedia.com/page/Trip.com) 公开信息。

| Domain | Market | Locale | Currency | Stage | Route | Protection | Last Test | Result | Notes |
|---|---|---|---|---|---|---|---|---|---|
| trip.com | GLOBAL | en-US | USD | register | mobile-app-reverse-delivery | (推测) SSL pin + root detect + native sign | never | unknown | 主市场,英文 |
| trip.com | HK | zh-HK | HKD | register | mobile-app-reverse-delivery | 同上 | never | unknown | |
| trip.com | TW | zh-TW | TWD | register | mobile-app-reverse-delivery | 同上 | never | unknown | |
| trip.com | SG | en-SG | SGD | register | mobile-app-reverse-delivery | 同上 | never | unknown | |
| trip.com | TH | th-TH | THB | register | mobile-app-reverse-delivery | 同上 | never | unknown | |
| trip.com | JP | ja-JP | JPY | register | mobile-app-reverse-delivery | 同上 | never | unknown | |
| trip.com | KR | ko-KR | KRW | register | mobile-app-reverse-delivery | 同上 | never | unknown | |

## Rules

- Test each market separately. (Trip.com 多市场风控可能不同)
- Record route decisions separately from API response errors.
- Currency can affect fare availability and payment method.
- Locale can affect page config and API route.

## 公司架构

- Trip.com Group Limited (新加坡注册)
- 中国大陆主体: 上海携程
- 服务覆盖 220+ 国家和地区

## 端 → domain 映射 (重要)

| 端 | domain | 包名 | 本目录覆盖? |
|---|---|---|---|
| 国际 Android | trip.com | `ctrip.english` | **✓ 当前目录** |
| 国际 iOS | trip.com | (App Store id705079220) | ✗ |
| 国内 Android | ctrip.com | `ctrip.android.view` | ✗ (拆独立目录) |
| 国内 iOS | ctrip.com | (App Store) | ✗ |
| 国际 Web | trip.com | N/A | ✗ (拆独立目录,platform=web) |
| 国内 Web | ctrip.com | N/A | ✗ |

**关键**: Trip.com (国际) 与 携程 (国内) **不同包不同协议**,即使 sign 算法相似也不能假设兼容。本目录仅覆盖 `ctrip.english` Android。

## 业务线

- 机票 (国际 + 国内)
- 酒店 (全球)
- 火车票 (重点中国 12306 + 部分国家)
- 用车 / 接送机
- 旅行套餐 (打包)
- 旅游攻略

## 注册接口业务边界

- Trip.com 国际版支持手机号 / 邮箱 / 第三方 (Apple / Google) 注册
- 注册成功后通常自动登录 + 给优惠券
- 注册涉及 KYC 类信息: 手机号 + 国家区号 + 邮箱 + 密码

## 风控强度估计 (推测)

- 国际版风控**弱于**国内携程 (国内更受国内反爬 SDK 厂商影响)
- 但国际版 vs 全球航司直营 app: 大约**强于** ThaiAirways (本仓 web 试点),**弱于** Vietjet (业务上 less 敏感)
