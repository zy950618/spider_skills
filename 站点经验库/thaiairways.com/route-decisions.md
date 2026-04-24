# Thai Airways Route Decisions

| Date | Market | Stage | Official Page Route | API Route | Decision | Evidence |
|---|---|---|---|---|---|---|
| prior | TH/BKK | search | new API likely | `/v2/search/air-bounds` | new-api-enabled | BKK-MNL returned airBoundGroups. |
| prior | CN/PVG | search | uncertain/mixed | `/flight/auth` or `/v2/search/air-bounds` | route-needs-check | Office ID and WAF symptoms observed. |

## Decision Rule

Check official page route, market config, rollout, and route allowlist before calling auth/search APIs.

