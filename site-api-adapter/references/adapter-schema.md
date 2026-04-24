# Adapter Schema

Recommended fields:

```yaml
site:
  id:
  name:
  base_urls:
  markets:
entry:
  page_url:
  api_hosts:
routes:
  - name:
    method:
    path:
    flow:
    request_schema:
    response_schema:
dependencies:
  headers:
  cookies:
  storage:
  crypto:
  environment:
protection:
  type:
  markers:
  token_strategy:
tests:
  smoke:
  stability:
  negative:
```

Keep secrets out of adapter files.

