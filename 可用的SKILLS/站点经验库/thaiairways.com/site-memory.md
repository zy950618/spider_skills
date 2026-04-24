# Thai Airways Site Memory

## Site

- domain: `thaiairways.com`
- official entry pages:
  - `https://www.thaiairways.com/en-th/`
- API hosts observed:
  - `api-des.thaiairways.com`
  - `www.thaiairways.com`
  - `ibooking.thaiairways.com`
- framework target: 314 when requested

## Markets

| Market | Locale | Currency | Status | Notes |
|---|---|---|---|---|
| CN | zh-CN / en | CNY | partial | PVG routes may not follow same new DAPI flow as BKK. |
| TH | en-TH | THB | partial | BKK-MNL search produced real airBoundGroups in prior tests. |
| JP | ja-JP / en | JPY | unknown | Must test separately. |
| US | en-US | USD | unknown | Must test separately. |

## Stages

| Stage | Status | Skill | Notes |
|---|---|---|---|
| search | mixed | website-314-api-delivery / reverse-js-crawler | Route decision matters before auth/search. |
| cart | protected | website-314-api-delivery / imperva-waf-reese84 | Browser/session reuse can increase WAF risk. |
| order | partial | website-314-api-delivery | 201/200 order stage does not equal payment success. |
| payment | high-risk | website-314-api-delivery | Use dry-run/sandbox unless explicit approval exists. |

## Protection

- Reese84 / Incapsula appears on protected hosts.
- Token generation success is not protected API acceptance.
- Purchase/order submit can have separate Incapsula layer from search/cart.
- Cache by proxy + UA + market + host + session scope.

