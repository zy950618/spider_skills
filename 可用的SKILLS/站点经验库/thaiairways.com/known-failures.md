# Thai Airways Known Failures

## Failure: Office ID On Wrong Route

- domain: `thaiairways.com`
- market: CN
- stage: search
- message: `Unable to find required Office ID`
- failure class: route-decision
- root cause: route may be forced into a new API/auth flow that official frontend does not use for that market/departure.
- correct handling: check official frontend rollout/config and route decision before changing payload or hard-coding office id.
- related skill: `website-314-api-delivery`, `site-api-adapter`
- eval status: should be regression eval.

## Failure: Reese84 Token OK But API Still Blocked

- domain: `thaiairways.com`
- stage: search/cart/order
- marker: `incapsula-html`, `_Incapsula_Resource`, `x-iinfo`
- failure class: waf
- root cause: challenge endpoint returned a token, but protected business API did not accept the fingerprint/session/cookie set.
- correct handling: treat as WAF protection failure; refresh bounded token cache and align fingerprint/cookie domain; do not return business success.
- related skill: `imperva-waf-reese84`
- eval status: already covered in WAF eval, keep adding site-specific variants.

## Failure: Shared Browser Session Under Concurrency

- domain: `thaiairways.com`
- stage: cart/order
- failure class: session-cache
- root cause: shared browser/session/cookie jar can trigger WAF risk across unrelated requests.
- correct handling: isolate by proxy/IP + UA + market + host + session scope.
- related skill: `imperva-waf-reese84`

## Failure: Payment Success Confusion

- domain: `thaiairways.com`
- stage: order/payment
- failure class: payment-risk
- root cause: order/profile/cart success does not mean purchase/payment success.
- correct handling: separate order creation, payment initialization, payment submit, and ticketing confirmation. Use dry-run/sandbox unless explicitly authorized.
- related skill: `website-314-api-delivery`

