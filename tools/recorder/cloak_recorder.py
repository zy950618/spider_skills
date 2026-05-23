"""CloakBrowser 启动 + record_har_path 自动录 HAR(含完整 body)→ HAR 文件。

修复了 v0.3.6 的 bug: page.on('response') 同步回调拿不到 body。
改用 browser.new_context(record_har_path=...) 让 cloakbrowser 自己录,body 100% 完整。

用法:
  python tools/recorder/cloak_recorder.py \\
      --domain thaiairways.com \\
      --start-url https://www.thaiairways.com/ \\
      --duration 120

  # 录完用 har_to_fixtures.py 转(har 是 Playwright 录的标准格式)
  python tools/recorder/har_to_fixtures.py \\
      --har 站点经验库/thaiairways.com/fixtures/recordings/<date>-session.har \\
      --domain thaiairways.com --apply

设计:
  - 启动 cloakbrowser (反指纹) 而非 playwright
  - new_context(record_har_path=...) 让 cloakbrowser 自动录完整请求/响应/body 到 HAR
  - 仍保留 page.on listener 只做实时计数日志
  - --duration 秒后或 Ctrl+C 时 context.close() 触发 HAR 写盘

CloakBrowser API 与 Playwright 兼容,需 pip install cloakbrowser + python -m cloakbrowser install
"""
from __future__ import annotations

import argparse
import datetime
import signal
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_ROOT = REPO_ROOT / "站点经验库"


def try_import_cloak():
    try:
        from cloakbrowser import launch  # type: ignore
        return launch
    except ImportError:
        print("ERROR: cloakbrowser 未安装。装一下:", file=sys.stderr)
        print("  pip install cloakbrowser", file=sys.stderr)
        print("  python -m cloakbrowser install", file=sys.stderr)
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="CloakBrowser 录请求/响应到 HAR (含完整 body)")
    parser.add_argument("--domain", required=True, help="站点经验库 domain")
    parser.add_argument("--start-url", required=True, help="起点 URL")
    parser.add_argument("--duration", type=int, default=180,
                        help="最长录制时长 (秒), 默认 180")
    parser.add_argument("--headless", action="store_true",
                        help="无头模式 (默认 false, 因为需要人手动跳转)")
    parser.add_argument("--humanize", action="store_true",
                        help="启用 CloakBrowser humanize 模式")
    parser.add_argument("--proxy", default=None, help="代理 URL")
    args = parser.parse_args()

    launch = try_import_cloak()
    if launch is None:
        return 1

    rec_dir = SITE_ROOT / args.domain / "fixtures" / "recordings"
    rec_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    har_file = rec_dir / f"{ts}-session.har"

    print(f"[recorder] CloakBrowser launching (headless={args.headless})...")
    print(f"[recorder] start: {args.start_url}")
    print(f"[recorder] output HAR: {har_file}")
    print(f"[recorder] duration: {args.duration}s  (Ctrl+C 提前停止)")
    print(f"[recorder] **不要进登录/订单/支付链路**")

    launch_kwargs: dict = {"headless": args.headless}
    if args.humanize:
        launch_kwargs["humanize"] = True
    if args.proxy:
        launch_kwargs["proxy"] = args.proxy

    browser = launch(**launch_kwargs)
    # 关键修复: record_har_path 让 cloakbrowser 自己录,含完整 body
    context = browser.new_context(
        record_har_path=str(har_file),
        record_har_content="embed",   # body 内嵌进 HAR (而非外部文件)
        record_har_mode="full",       # full = 所有 request/response (而非 minimal)
    )
    page = context.new_page()

    counter = {"req": 0, "resp": 0}

    def on_request(_):
        counter["req"] += 1

    def on_response(_):
        counter["resp"] += 1

    page.on("request", on_request)
    page.on("response", on_response)

    stop = {"flag": False}

    def handle_sigint(_sig, _frame):
        print("\n[recorder] Ctrl+C, 停止...")
        stop["flag"] = True
    signal.signal(signal.SIGINT, handle_sigint)

    try:
        page.goto(args.start_url, timeout=60_000)
    except Exception as e:
        print(f"[recorder] goto failed: {e}", file=sys.stderr)

    deadline = time.time() + args.duration
    last_print = 0
    while time.time() < deadline and not stop["flag"]:
        time.sleep(1)
        # 每 5 秒打一次进度
        if time.time() - last_print >= 5:
            elapsed = int(time.time() - (deadline - args.duration))
            print(f"[recorder] {elapsed}s/{args.duration}s req={counter['req']} resp={counter['resp']}")
            last_print = time.time()

    # 关键: context.close() 触发 HAR 写盘
    try:
        context.close()
    except Exception as e:
        print(f"[recorder] context.close warn: {e}", file=sys.stderr)
    try:
        browser.close()
    except Exception:
        pass

    if not har_file.exists():
        print(f"[recorder] WARN: HAR file not created: {har_file}", file=sys.stderr)
        return 2

    har_size = har_file.stat().st_size
    print(f"\n[recorder] done. req={counter['req']} resp={counter['resp']}")
    print(f"[recorder] HAR: {har_file} ({har_size:,} bytes)")
    print(f"[recorder] next: python tools/recorder/har_to_fixtures.py "
          f"--har \"{har_file}\" --domain {args.domain} --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
