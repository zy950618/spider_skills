# Architecture

## Separation

Use three layers:

- `anti_bot/<vendor>`: challenge extraction, token generation, cache, fingerprint profile
- `reverse/<vendor>`: extracted JS, Node runners, browser-environment patches
- `services/<vendor>`: search/cart/order/business payloads only

Do not put challenge JS or browser patches into business services.

## Cache Identity

Cache token state by:

- protection type
- host/domain
- proxy/IP
- user agent and client hints
- market/language
- session or flow id

Force refresh on protection markers.

## Browser Policy

Use fresh isolated profiles for diagnostics. Production should use simulated stable profiles or explicit fallback, not a human user's local Chrome session.

