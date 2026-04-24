# Delivery Checklist

## Required Outputs

For a full website-to-API task, deliver:

- route matrix
- dependency matrix
- crypto/WAF classification
- adapter.yaml or equivalent adapter notes
- service implementation
- API endpoints
- test file
- stability result
- known failure boundaries
- skill/eval update proposal

## Business Stage Checklist

Search:

- route enabled check
- market/country/language
- date format
- passenger counts
- cabin/fare family
- response count summary

Cart:

- selected bound / fare / offer
- cart session id
- host/domain cookie consistency
- idempotency behavior

Order:

- traveler data
- contact data
- add-ons
- order id / booking id
- status and expiration

Payment:

- payment methods
- payment initialization
- redirect or tokenization
- 3DS / challenge
- dry-run or sandbox confirmation
- no real charge without explicit approval

## Acceptance

A stage is accepted only when the target service accepts the request and returns the expected stage-specific data. Local token generation, local payload construction, or a browser-side page transition is not enough.

