"""HAR → fixtures/snapshots/

读 Chrome/Edge/Firefox DevTools 导出的 HAR 文件,按 URL/method 拆成
fixtures/snapshots/ 下的标准三件套(req.json / resp.json / meta.yaml)。

回退方案: 任何浏览器都能抓 HAR,不需要 CloakBrowser。
适合首次录制 / 公开页面 / 不带反爬的接口。

用法:
  python tools/recorder/har_to_fixtures.py \\
      --har recordings/2026-05-23-session.har \\
      --domain thaiairways.com \\
      --include-host "*.thaiairways.com" \\
      --apply

行为:
  1. 解析 HAR entries
  2. 用 --include-host glob 过滤(默认只保留 domain 主机的请求)
  3. 跳过静态资源(.js/.css/.png/.woff 等)
  4. 跳过 OPTIONS preflight
  5. 每个 entry 生成 slug + 三件套写到 站点经验库/<domain>/fixtures/snapshots/
  6. 同 slug 已存在 → 默认跳过,加 --overwrite 才覆盖
  7. meta.yaml 写默认值(category=public-read, expires_at +30 天),需要人工 review
"""
from __future__ import annotations

import argparse
import base64
import datetime
import fnmatch
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


def host_matches(host: str, patterns: list[str]) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(host, pat) for pat in patterns)


def normalize_headers(har_headers: list[dict]) -> dict:
    out = {}
    for h in har_headers:
        name = h.get("name", "").lower()
        value = h.get("value", "")
        if not name or name.startswith(":"):
            continue
        out[name] = value
    return out


def extract_body(content: dict | None, post_data: dict | None) -> tuple[object, str]:
    if post_data:
        text = post_data.get("text")
        mime = post_data.get("mimeType", "")
        if text is not None:
            if "json" in mime.lower():
                try:
                    return json.loads(text), "json"
                except Exception:
                    return text, "text"
            return text, "text"
        return None, "none"

    if not content:
        return None, "none"
    text = content.get("text")
    encoding = content.get("encoding")
    mime = content.get("mimeType", "")
    if text is None:
        return None, "none"
    if encoding == "base64":
        if "json" in mime.lower():
            try:
                return json.loads(base64.b64decode(text).decode("utf-8")), "json"
            except Exception:
                return text, "base64"
        return text, "base64"
    if "json" in mime.lower():
        try:
            return json.loads(text), "json"
        except Exception:
            return text, "text"
    return text, "text"


def render_meta(method: str, url: str, host: str, path: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    exp = now + datetime.timedelta(days=30)
    return f"""endpoint: "TODO: human-readable name for {method} {path}"
recorded_at: "{now.isoformat().replace('+00:00', 'Z')}"
expires_at: "{exp.isoformat().replace('+00:00', 'Z')}"
category: "public-read"   # TODO: confirm. allowed: public-read / search / detail / list
sensitive: false           # TODO: true if response contains PII
requires_auth: false       # TODO: true if needs login cookie
volatile_fields: []
tolerance: {{}}
notes: |
  Auto-extracted from HAR. Review and edit before committing.
  Source URL: {url}
"""


def write_files(out_dir: Path, slug: str, method: str, url: str, headers: dict,
                req_body: object, req_encoding: str, status: int, resp_headers: dict,
                resp_body: object, resp_encoding: str, resp_size: int,
                overwrite: bool) -> tuple[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{method}_{slug}"
    req = out_dir / f"{prefix}.req.json"
    resp = out_dir / f"{prefix}.resp.json"
    meta = out_dir / f"{prefix}.meta.yaml"

    if req.exists() and not overwrite:
        return "skip", 0

    parsed = urlparse(url)
    req_doc = {
        "method": method,
        "url": url,
        "headers": headers,
        "body": req_body,
        "_meta": {
            "host": parsed.hostname or "",
            "path": parsed.path or "/",
            "query": parsed.query,
            "body_encoding": req_encoding,
        },
    }
    resp_doc = {
        "status": status,
        "headers": resp_headers,
        "body": resp_body,
        "_meta": {
            "body_encoding": resp_encoding,
            "body_size_bytes": resp_size,
        },
    }
    req.write_text(json.dumps(req_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    resp.write_text(json.dumps(resp_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    meta.write_text(render_meta(method, url, parsed.hostname or "", parsed.path or "/"),
                    encoding="utf-8")
    return "write", 3


def main() -> int:
    parser = argparse.ArgumentParser(description="HAR → fixtures/snapshots/")
    parser.add_argument("--har", required=True, help="HAR 文件路径")
    parser.add_argument("--domain", required=True, help="目标 domain (例: thaiairways.com)")
    parser.add_argument("--include-host", action="append", default=[],
                        help="只保留这些 host(glob),可多次。默认: *.<domain> 和 <domain>")
    parser.add_argument("--skip-status-ge", type=int, default=400,
                        help="跳过 HTTP status >= 此值的响应(默认 400)")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的 snapshot")
    parser.add_argument("--apply", action="store_true", help="真正写文件(默认 dry-run)")
    args = parser.parse_args()

    har_path = Path(args.har)
    if not har_path.exists():
        print(f"ERROR: HAR not found: {har_path}", file=sys.stderr)
        return 1

    try:
        har = json.loads(har_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: parse HAR: {e}", file=sys.stderr)
        return 1

    entries = har.get("log", {}).get("entries", [])
    print(f"HAR entries: {len(entries)}")

    include_hosts = args.include_host or [f"*.{args.domain}", args.domain]
    print(f"include-host patterns: {include_hosts}")

    out_dir = SITE_ROOT / args.domain / "fixtures" / "snapshots"
    print(f"output dir: {out_dir}")

    stats = {"total": 0, "static": 0, "options": 0, "host_skip": 0,
             "status_skip": 0, "write": 0, "skip_exist": 0}

    for entry in entries:
        stats["total"] += 1
        req = entry.get("request", {})
        resp = entry.get("response", {})
        method = (req.get("method") or "").upper()
        url = req.get("url") or ""
        status = int(resp.get("status") or 0)

        if not url or not method:
            continue
        if method == "OPTIONS":
            stats["options"] += 1
            continue
        if is_static(url):
            stats["static"] += 1
            continue

        host = urlparse(url).hostname or ""
        if not host_matches(host, include_hosts):
            stats["host_skip"] += 1
            continue
        if status >= args.skip_status_ge:
            stats["status_skip"] += 1
            continue

        path = urlparse(url).path or "/"
        slug = slugify_path(path)

        req_headers = normalize_headers(req.get("headers") or [])
        resp_headers = normalize_headers(resp.get("headers") or [])
        req_body, req_enc = extract_body(None, req.get("postData"))
        resp_body, resp_enc = extract_body(resp.get("content"), None)
        resp_size = int((resp.get("content") or {}).get("size") or 0)

        if not args.apply:
            print(f"  [dry-run] {method} {host}{path} -> {slug}")
            stats["write"] += 1
            continue

        action, _ = write_files(out_dir, slug, method, url, req_headers,
                                 req_body, req_enc, status, resp_headers,
                                 resp_body, resp_enc, resp_size, args.overwrite)
        if action == "skip":
            stats["skip_exist"] += 1
        else:
            stats["write"] += 1
            print(f"  [write] {method}_{slug}")

    print(f"\nstats: {stats}")
    if not args.apply:
        print("\n加 --apply 真正写文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
