# WAF Testing

## Success Ladder

1. challenge script extracted
2. challenge JS runs locally
3. token/cookie returned by challenge endpoint
4. protected business API accepts the request
5. repeated requests remain in the same result class

Do not stop at step 3.

## Diagnostics

Report:

- protection marker
- host/domain
- token length only, not full token
- cookie names only, not full cookie values
- target API status and content type
- x-iinfo or equivalent response header
- retry count and refresh reason

