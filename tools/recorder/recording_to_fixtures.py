"""CloakBrowser 录制 jsonl → fixtures/snapshots/

读 cloak_recorder.py 产出的 jsonl,按 url/method 配对 request+response,
按 url path 切 slug, 输出 fixtures/snapshots/ 标准三件套。

用法:
  python tools/recorder/recording_to_fixtures.py \\
      --recording 站点经验库/thaiairways.com/fixtures/recordings/2026-05-23-session.jsonl \\
      --domain thaiairways.com \\
      --apply

行为:
  1. 读 jsonl, 把 request 与下一个同 url/method 的 response 配对
  2. 跳静态资源 / OPTIONS / status >= 400
  3. 同 slug 重复时, 保留最后一次(覆盖)
  4. 输出 snapshots/<METHOD>_<slug>.req.json / .resp.json / .meta.yaml
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"

STATIC_EXT = {
    ".js", ".mjs", ".css", ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp",
    ".mp4", ".webm", ".mp3", ".wav", ".m4a",
    ".map",
}

SLUG_SEG_RE = re.compile(r"[^a-zA-Z0-9]+")


def slugify_path(path: str) -> str:
    segs = [s for s in path.split("/") if s]
    if not segs:
        return "root"
    out = []
    for s in segs:
        s = SLUG_SEG_RE.sub("-", s).strip("-")
        if not s:
            continue
        if len(s) > 32:
            s = s[:32]
        out.append(s)
    slug = "-".join(out)
    return slug[:80] if slug else "root"


def is_static(url: str) -> bool:
    p = urlparse(url).path.lower()
    for ext in STATIC_EXT:
        if p.endswith(ext):
            return True
    return False


def render_meta(method: str, url: str, path: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    exp = now + datetime.timedelta(days=30)
    return f"""endpoint: "TODO: human-readable name for {method} {path}"
recorded_at: "{now.isoformat().replace('+00:00', 'Z')}"
expires_at: "{exp.isoformat().replace('+00:00', 'Z')}"
category: "public-read"   # TODO: confirm
sensitive: false           # TODO: true if response contains PII
requires_auth: false       # TODO: true if needs login cookie
volatile_fields: []
tolerance: {{}}
notes: |
  Auto-extracted from CloakBrowser recording. Review and edit before committing.
  Source URL: {url}
"""


def detect_body(text: str | None, content_type: str) -> tuple[object, str]:
    if text is None:
        return None, "none"
    ct = (content_type or "").lower()
    if "json" in ct:
        try:
            return json.loads(text), "json"
        except Exception:
            return text, "text"
    return text, "text"


def detect_req_body(post_data: str | None, content_type: str) -> tuple[object, str]:
    if not post_data:
        return None, "none"
    ct = (content_type or "").lower()
    if "json" in ct:
        try:
            return json.loads(post_data), "json"
        except Exception:
            return post_data, "text"
    return post_data, "text"


def main() -> int:
    parser = argparse.ArgumentParser(description="CloakBrowser jsonl → snapshots/")
    parser.add_argument("--recording", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--skip-status-ge", type=int, default=400)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rec = Path(args.recording)
    if not rec.exists():
        print(f"ERROR: recording not found: {rec}", file=sys.stderr)
        return 1

    out_dir = SITE_ROOT / args.domain / "fixtures" / "snapshots"
    if args.apply:
        out_dir.mkdir(parents=True, exist_ok=True)

    pending_req: dict = {}
    pairs: list[tuple[dict, dict]] = []

    with rec.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            t = ev.get("type")
            key = (ev.get("method", ""), ev.get("url", ""))
            if t == "request":
                pending_req[key] = ev
            elif t == "response":
                req = pending_req.pop(key, None)
                pairs.append((req or {}, ev))

    print(f"recording entries: {len(pairs)} request/response pairs")

    stats = {"total": 0, "static": 0, "options": 0, "status_skip": 0,
             "write": 0, "skip_exist": 0}

    seen: set[str] = set()

    for req_ev, resp_ev in pairs:
        stats["total"] += 1
        method = (resp_ev.get("method") or req_ev.get("method") or "").upper()
        url = resp_ev.get("url") or req_ev.get("url") or ""
        status = int(resp_ev.get("status") or 0)
        if not url or not method:
            continue
        if method == "OPTIONS":
            stats["options"] += 1
            continue
        if is_static(url):
            stats["static"] += 1
            continue
        if status >= args.skip_status_ge:
            stats["status_skip"] += 1
            continue

        path = urlparse(url).path or "/"
        slug = slugify_path(path)
        prefix = f"{method}_{slug}"

        req_headers = req_ev.get("headers") or {}
        resp_headers = resp_ev.get("headers") or {}
        req_ct = req_headers.get("content-type") or req_headers.get("Content-Type") or ""
        resp_ct = resp_headers.get("content-type") or resp_headers.get("Content-Type") or ""

        req_body, req_enc = detect_req_body(req_ev.get("post_data"), req_ct)
        resp_body, resp_enc = detect_body(resp_ev.get("body_text"), resp_ct)

        req_file = out_dir / f"{prefix}.req.json"
        resp_file = out_dir / f"{prefix}.resp.json"
        meta_file = out_dir / f"{prefix}.meta.yaml"

        if not args.apply:
            print(f"  [dry-run] {method} {path} -> {prefix}")
            stats["write"] += 1
            continue

        if prefix in seen:
            pass
        else:
            seen.add(prefix)

        if req_file.exists() and not args.overwrite and prefix in seen:
            stats["skip_exist"] += 1
            continue

        parsed = urlparse(url)
        req_doc = {
            "method": method,
            "url": url,
            "headers": {k.lower(): v for k, v in req_headers.items()},
            "body": req_body,
            "_meta": {
                "host": parsed.hostname or "",
                "path": parsed.path or "/",
                "query": parsed.query,
                "body_encoding": req_enc,
            },
        }
        resp_doc = {
            "status": status,
            "headers": {k.lower(): v for k, v in resp_headers.items()},
            "body": resp_body,
            "_meta": {
                "body_encoding": resp_enc,
                "body_size_bytes": len(resp_ev.get("body_text") or ""),
            },
        }
        req_file.write_text(json.dumps(req_doc, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        resp_file.write_text(json.dumps(resp_doc, ensure_ascii=False, indent=2),
                             encoding="utf-8")
        if not meta_file.exists() or args.overwrite:
            meta_file.write_text(render_meta(method, url, parsed.path or "/"),
                                 encoding="utf-8")
        stats["write"] += 1
        print(f"  [write] {prefix}")

    print(f"\nstats: {stats}")
    if not args.apply:
        print("\n加 --apply 真正写文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
