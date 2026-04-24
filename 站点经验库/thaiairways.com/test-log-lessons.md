# Thai Airways Test Log Lessons

## Pattern: Date/Input Mismatch

- symptom: user supplied one date but logs showed another date.
- class: test-data / payload-mapping
- action: log original input, normalized date, final upstream payload date, and session_id.

## Pattern: WAF HTML In JSON Flow

- symptom: endpoint expected JSON but returned Incapsula HTML.
- class: waf
- action: classify by content type and markers; do not JSON-fallback into empty success.

## Pattern: Stage-Specific Protection

- symptom: search/cart/order may behave differently, purchase can trigger separate protection.
- class: waf / payment-risk
- action: test each stage independently and record exact stage of block.

