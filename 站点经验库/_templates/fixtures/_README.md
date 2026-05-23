# fixtures/ — 站点逆向产出与真实响应的一致性证据

每个 domain 的 `fixtures/` 目录是"我方接口"与"真实网页/App"对齐的物证。脚本写,人工 review,CI 重放。

## 目录布局

```
站点经验库/<domain>/fixtures/
├── snapshots/                          # 标准化快照(脚本读写)
│   ├── <METHOD>_<endpoint-slug>.req.json    # 请求(method/url/headers/body)
│   ├── <METHOD>_<endpoint-slug>.resp.json   # 响应(status/headers/body)
│   └── <METHOD>_<endpoint-slug>.meta.yaml   # 元数据/豁免/容忍度
├── recordings/                         # 原始录制(保留 30 天)
│   ├── <YYYY-MM-DD>-<session>.har          # HAR 文件
│   └── <YYYY-MM-DD>-<session>.jsonl        # CloakBrowser CDP 录制
└── reports/                            # 重放比对报告(脚本写)
    ├── <YYYY-MM-DD>-replay.md
    └── trend.json                          # 历史一致率趋势
```

## 文件命名约定

snapshot 三件套必须文件名前缀一致:

- `GET_search-airports.req.json`
- `GET_search-airports.resp.json`
- `GET_search-airports.meta.yaml`

slug 规则: `<METHOD>_<path-segments-kebab-case>`。

例:
- `GET /api/v1/airports/list` → `GET_api-v1-airports-list`
- `POST /search/flight?cabin=ECONOMY` → `POST_search-flight`(query 不进 slug,放进 .req.json 的 url 字段)

## meta.yaml 字段

见 `meta-template.yaml`。核心字段:

| 字段 | 必填 | 说明 |
|---|---|---|
| `endpoint` | ✓ | 接口语义名(人读) |
| `recorded_at` | ✓ | ISO 时间戳 |
| `expires_at` | ✓ | 30 天后 ISO 时间戳,过期必须重录 |
| `category` | ✓ | `public-read` / `search` / `detail` / `list` (**不允许** `payment` / `order-create`) |
| `volatile_fields` | - | 本接口要豁免的字段名(覆盖默认表) |
| `tolerance` | - | 业务字段容忍度规则(如 price ±10%) |
| `sensitive` | - | true 时 CI 不打印响应体 |
| `requires_auth` | - | true 时重放需要 session cookie |
| `notes` | - | 录制条件 / 触发该接口的业务动作 |

## 红线

1. **支付 / 扣款 / 真实下单接口绝对不录** — CLAUDE.md 红线,违反直接删除
2. **登录态接口录前清空 cookie / 用测试账号** — 别把生产 token 落盘
3. **响应里有 PII(用户名/手机/邮箱/身份证) → meta.yaml 标 `sensitive: true`** — CI 跑时不打印
4. **fixtures 提交前过一遍 `tools/replayer/snapshot_lint.py`** — 自动扫 sensitive 标记缺失

## 与 known-failures.md 的关系

- known-failures: 流程类失败(WAF / 会话 / 路由 / 支付边界)
- **fixtures: 数据类失败(我方返回 vs 真实返回字段对不上)**

两者互补。一致性 < 90% 的失败模式要写进 known-failures.md。

## 重放与漂移

- 本地重放:`python tools/replayer/snapshot_replay.py --domain X --target <adapter-base-url>`
- CI 重放:每周二 + PR 触发,见 `.github/workflows/consistency-replay.yml`
- 漂移阈值:一致率 < 90% 自动开 issue
