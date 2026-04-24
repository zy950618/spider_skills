# Thai Airways Market Matrix

| Domain | Market | Locale | Currency | Stage | Route | Protection | Last Result | Notes |
|---|---|---|---|---|---|---|---|---|
| thaiairways.com | CN | zh-CN/en | CNY | search | mixed/new-vs-legacy | possible WAF | PVG-MNL previously hit Office ID / WAF path | Do not assume BKK result applies. |
| thaiairways.com | TH | en-TH | THB | search | new API observed | lower for search | BKK-MNL returned groups in previous tests | Still retest current route. |
| thaiairways.com | JP | ja-JP/en | JPY | search | unknown | unknown | not tested | Treat as separate market. |
| thaiairways.com | US | en-US | USD | search | unknown | unknown | not tested | Treat as separate market. |

## Rule

Same domain does not mean same API route, Office ID, currency, fare availability, WAF behavior, or payment method.

