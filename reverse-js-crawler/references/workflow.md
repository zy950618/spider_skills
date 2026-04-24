# Reverse Workflow

## Inputs

Accept any of:

- page URL
- API URL
- JavaScript file or bundle
- packet capture summary
- existing Python/Node script
- error response from a protected endpoint

## Deliverable Shape

Prefer this project split:

```text
project/
  config/
  reverse/
  crypto/
  scraper/
  tests/
  main.py or main.js
```

Keep responsibilities clear:

- `reverse`: source scripts, notes, extracted snippets
- `crypto`: sign/token/cookie generation
- `scraper`: request templates, pagination, retries
- `tests`: single request, pagination, stability, negative cases

## Analysis Checklist

- real data endpoint identified
- request dependencies listed
- encrypted parameters mapped to source
- environment dependencies identified
- one-shot request reproduced
- repeated request tested
- batch flow tested
- failure classes documented

## Failure Classes

Report failures as one of:

- business error
- auth/session error
- token/sign mismatch
- environment mismatch
- WAF/challenge
- IP/proxy block
- data unavailable
- implementation bug

