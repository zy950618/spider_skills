# Route Decisions Template

| Date | Domain | Market | Locale | Currency | Stage | Official Page Route | API Route | Decision | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | search | | | unknown | |

## Decision Values

- new-api-enabled
- legacy-flow
- route-disabled
- no-real-flight
- market-not-supported
- waf-blocked
- unknown

## Rules

- Official page route beats guessed API route.
- Missing office/market/config errors can indicate wrong route.
- A route decision is not the same as fare availability.

