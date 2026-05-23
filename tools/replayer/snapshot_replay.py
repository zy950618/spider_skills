"""重放 fixtures/snapshots/*.req.json 到本方接口 (adapter),落 actual。

用法:
  python tools/replayer/snapshot_replay.py \\
      --domain thaiairways.com \\
      --target https://my-adapter.local

  # 重放某一个 endpoint
  python tools/replayer/snapshot_replay.py \\
      --domain thaiairways.com \\
      --target https://my-adapter.local \\
      --filter "GET_search-airports"

  # 直接重放回原站(诊断用,默认禁用)
  python tools/replayer/snapshot_replay.py --domain X --target original

行为:
  1. 读 snapshots/*.req.json 与对应 meta.yaml
  2. 检查 meta.expires_at 未过期(过期 warn 但不跳)
  3. 重写 URL host 为 --target
  4. 发请求 (用 stdlib urllib,零依赖)
  5. 落 actual/<prefix>.actual.json (同 resp.json 结构)
  6. 不做 diff,diff 由 consistency_report 调
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse, urlunparse

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from field_rules import load_meta


def parse_target(target: str) -> str | None:
    """返回 target host (例 'my-adapter.local:8080'),或 None 表示重放回原站。"""
    if target.lower() == "original":
        return None
    p = urlparse(target if "://" in target else f"https://{target}")
    return p.netloc or None


def rewrite_url(original: str, target_netloc: str | None) -> str:
    if not target_netloc:
        return original
    p = urlparse(original)
    return urlunparse(("https", target_netloc, p.path, p.params, p.query, p.fragment))


def check_expiry(meta: dict, prefix: str) -> bool:
    exp = meta.get("expires_at")
    if not exp:
        return True
    try:
        exp_dt = datetime.datetime.fromisoformat(exp.replace("Z", "+00:00"))
    except Exception:
        return True
    now = datetime.datetime.now(datetime.timezone.utc)
    if exp_dt < now:
        print(f"  WARN: {prefix} expired at {exp} (recorded > 30 days ago, re-record recommended)")
        return False
    return True


def send_request(method: str, url: str, headers: dict, body: object,
                 timeout: int = 30) -> dict:
    if isinstance(body, (dict, list)):
        body_bytes = json.dumps(body).encode("utf-8")
        if "content-type" not in {k.lower() for k in headers}:
            headers = {**headers, "content-type": "application/json"}
    elif isinstance(body, str):
        body_bytes = body.encode("utf-8")
    elif body is None:
        body_bytes = None
    else:
        body_bytes = str(body).encode("utf-8")

    req = urllib.request.Request(url, data=body_bytes, method=method)
    # 默认 strip 压缩相关 header,让服务器返回明文(urllib 不自动解压)
    # 即使如此服务器仍可能返回 gzip,后面用 Content-Encoding 兜底解压
    skip_headers = {"host", "content-length", "connection",
                    "accept-encoding"}
    for k, v in headers.items():
        if k.lower() in skip_headers:
            continue
        req.add_header(k, v)
    req.add_header("Accept-Encoding", "identity")  # 显式要明文

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read()
    except urllib.error.HTTPError as e:
        status = e.code
        resp_headers = {k.lower(): v for k, v in (e.headers or {}).items()}
        raw = e.read() or b""
    except urllib.error.URLError as e:
        return {"status": 0, "headers": {}, "body": None,
                "_meta": {"error": str(e), "body_encoding": "none"}}

    # 服务器无视 Accept-Encoding:identity 时,按 Content-Encoding 解压
    content_enc = resp_headers.get("content-encoding", "").lower().strip()
    if content_enc == "gzip":
        import gzip
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    elif content_enc == "deflate":
        import zlib
        try:
            raw = zlib.decompress(raw)
        except Exception:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)
            except Exception:
                pass
    elif content_enc in ("br", "brotli"):
        try:
            import brotli  # type: ignore
            raw = brotli.decompress(raw)
        except ImportError:
            print(f"    WARN: brotli encoding but `pip install brotli` missing, body will be binary",
                  file=sys.stderr)
        except Exception:
            pass

    content_type = resp_headers.get("content-type", "").lower()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        import base64
        return {"status": status, "headers": resp_headers,
                "body": base64.b64encode(raw).decode("ascii"),
                "_meta": {"body_encoding": "base64", "body_size_bytes": len(raw)}}

    if "json" in content_type:
        try:
            return {"status": status, "headers": resp_headers, "body": json.loads(text),
                    "_meta": {"body_encoding": "json", "body_size_bytes": len(raw)}}
        except Exception:
            pass
    return {"status": status, "headers": resp_headers, "body": text,
            "_meta": {"body_encoding": "text", "body_size_bytes": len(raw)}}


def main() -> int:
    parser = argparse.ArgumentParser(description="重放 snapshots → actual")
    parser.add_argument("--domain", required=True)
    parser.add_argument("--target", required=True,
                        help="本方 adapter base URL, 或 'original' 重放回原站(危险)")
    parser.add_argument("--filter", default=None,
                        help="只重放 prefix 匹配的 snapshot")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--allow-original", action="store_true",
                        help="允许 --target original (默认禁用)")
    args = parser.parse_args()

    target_netloc = parse_target(args.target)
    if target_netloc is None and not args.allow_original:
        print("ERROR: --target original 危险,默认禁用。加 --allow-original 才用。", file=sys.stderr)
        return 2

    fixtures_dir = SITE_ROOT / args.domain / "fixtures"
    snap_dir = fixtures_dir / "snapshots"
    if not snap_dir.is_dir():
        print(f"ERROR: {snap_dir} not found", file=sys.stderr)
        return 1

    actual_dir = fixtures_dir / "actual"
    actual_dir.mkdir(parents=True, exist_ok=True)

    req_files = sorted(snap_dir.glob("*.req.json"))
    print(f"snapshots: {len(req_files)}, target: {args.target}, filter: {args.filter}")

    stats = {"total": 0, "replayed": 0, "filtered": 0, "expired": 0, "failed": 0}

    for req_file in req_files:
        prefix = req_file.stem[:-4]  # strip ".req"
        if args.filter and args.filter not in prefix:
            stats["filtered"] += 1
            continue
        stats["total"] += 1

        try:
            req_doc = json.loads(req_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ERROR parse {req_file.name}: {e}")
            stats["failed"] += 1
            continue

        meta_file = snap_dir / f"{prefix}.meta.yaml"
        meta = load_meta(meta_file) if meta_file.exists() else {}
        if not check_expiry(meta, prefix):
            stats["expired"] += 1

        method = req_doc.get("method", "GET")
        url = rewrite_url(req_doc.get("url", ""), target_netloc)
        headers = req_doc.get("headers") or {}
        body = req_doc.get("body")

        print(f"  → {method} {url}")
        actual_doc = send_request(method, url, headers, body, args.timeout)
        actual_doc["_meta"]["replayed_at"] = (
            datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        )
        actual_doc["_meta"]["replay_target"] = args.target

        out_file = actual_dir / f"{prefix}.actual.json"
        out_file.write_text(json.dumps(actual_doc, ensure_ascii=False, indent=2),
                            encoding="utf-8")
        stats["replayed"] += 1
        if actual_doc["status"] == 0:
            stats["failed"] += 1
            print(f"    FAILED: {actual_doc['_meta'].get('error')}")

    print(f"\nstats: {stats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
