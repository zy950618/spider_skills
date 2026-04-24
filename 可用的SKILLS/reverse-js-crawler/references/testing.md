# Reverse Testing

## Minimum Tests

- Static syntax check for generated code.
- One known-good request with expected response shape.
- One invalid-parameter request to verify error handling.
- Pagination or repeated request loop when the task is collection.
- Data schema check for required fields.

## Stability Claims

Do not say stable unless repeated runs show the same class of result.

Example:

```text
route A x3: code=200, items=20 each
route B x3: code=403, protection=waf-html each
```

## Logging

Log:

- input parameters
- trace/session id
- endpoint and method
- status code
- business code/message
- elapsed time
- response summary

Do not print full tokens or sensitive cookies in normal logs.

