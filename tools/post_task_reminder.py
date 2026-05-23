"""Stop hook: 任务结束时检测是否需要沉淀提醒。

读 stdin 的 hook payload,扫 transcript 提取 domain。
若对话涉及网站逆向但没看到沉淀动作,把提示写到 stderr 并以退出码 2 退出,
让 Claude 接到反馈、酌情提醒用户补沉淀步骤。

设计原则:
- 异常静默(任何失败都退出码 0),不影响主任务
- repo_root 从 __file__ 推断,不依赖 cwd,支持任意工作目录调用
- 每次触发写一条 stats 到 tools/.reminder-stats.jsonl,为词表校准提供真实数据
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
STATS_FILE = SCRIPT_DIR / ".reminder-stats.jsonl"
SITE_MEMORY_DIR = "站点经验库"

DOMAIN_RE = re.compile(
    r"(?<![\w.\-/])(?:https?://)?(?:www\.)?"
    r"([a-z0-9][a-z0-9-]{0,62}\.(?:com|net|org|cn|co|io|ai|jp|hk|tw|sg|kr|vn|th|my|id|uk|de|fr|au))"
    r"(?![\w\-])",
    re.IGNORECASE,
)

EXCLUDE_DOMAINS = {
    "github.com", "githubusercontent.com", "raw.githubusercontent.com",
    "anthropic.com", "claude.com", "claude.ai",
    "google.com", "googleapis.com", "googleusercontent.com",
    "npmjs.com", "yarnpkg.com",
    "stackoverflow.com", "stackexchange.com",
    "mozilla.org", "developer.mozilla.org",
    "python.org", "pypi.org", "pythonhosted.org",
    "nodejs.org",
    "openai.com",
    "microsoft.com", "msdn.com", "live.com",
    "wikipedia.org",
    "unpkg.com", "jsdelivr.net", "cdnjs.com",
    "example.com", "example.org", "example.net", "example-airline.com",
    "localhost",
    # v0.3.8: 代码片段误报词,从 thaiairways 试点 stats 累积
    "obfuscator.io",
    "args.th", "inputs.th", "outputs.th", "home.th",
    "text.co", "shutil.co", "e.co",
    "datetime.fr", "p.fr",
    "brotli.de", "gzip.de", "zlib.de", "raw.de",
    "re.com", "p.net",
    # v0.3.9: SKILL.md description / references / fixtures 中的引用类 domain (非任务真目标)
    "vietjetair.com",   # mobile-app-reverse-delivery 示例触发词 + workflow.md 示例
    "x.com",            # karpathy SKILL.md 引用推文链接 + thaiairways socialMedia.json 引用
    "twitter.com",      # 同上,Twitter/X 的旧域名
    "facebook.com", "instagram.com", "linkedin.com",  # 社交平台常出现在 socialMedia 配置里
    "youtube.com", "youtu.be",
}

PERSIST_MARKERS = (
    "sync_site_memory.py",
    "score_skills.py",
    "skills-evaluation-governance",
    "known-failures.md",
    "test-log-lessons.md",
    "site-memory.md",
    "站点经验库",
    "site memory",
)

REVERSE_MARKERS = (
    "逆向", "reverse", "crawler", "crawl",
    "接口还原", "接口实现", "纯接口", "签名", "加密参数",
    "sign", "x-sign", "authkey", "x-d-token", "reese84",
    "waf", "imperva", "84盾", "incapsula", "akamai",
    "find-crypto-entry", "ast-deobfuscate", "env-patch",
    "frida", "apk", "ipa", "dex", "il2cpp",
    "adapter.yaml",
)

# v0.3.7: 完成度自评 (见 99-SKILLS治理/08-完成度自评.md)
COMPLETION_MARKERS = (
    "完成", "做完", "交付", "提交", "收尾", "完工", "全部完成", "已经做完",
    "done", "delivered", "finished", "wrapped up", "shipped",
)

VERIFICATION_MARKERS = (
    "验证", "verified", "verify", "跑过", "实测", "自评", "自检", "自读",
    "端到端", "checklist", "5 维", "五维", "spot check", "smoke test",
    "dry-run pass", "5 维自评", "五维自评",
)

# v0.4.0: 治理/评分任务上下文识别。命中 >=2 个 marker 时,认为本次是治理任务而非
# 业务逆向任务,跳过 new_domains 提示和 domain mtime 硬检查 — 治理任务的"沉淀"
# 落在 metrics/scores-v*.json 与 99-SKILLS治理/ 文档,不在站点经验库。
# 阈值 >=2 是为了防止单次代码引用 (如 README 提到 99-SKILLS治理) 触发豁免。
GOVERNANCE_MARKERS = (
    "score_skills.py",
    "99-SKILLS治理",
    "metrics/scores-",
    "skills-evaluation-governance",
    "drift-history.md",
    "verify_delivery.py",
    "评分回测",
    "评分漂移",
    "Skill Bench",
    "scores-v0.",
)


def load_transcript(path: str) -> list[dict]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    events: list[dict] = []
    with p.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def extract_text(events: list[dict]) -> str:
    parts: list[str] = []
    for ev in events:
        msg = ev.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for c in content:
                if not isinstance(c, dict):
                    continue
                t = c.get("type")
                if t == "text":
                    parts.append(str(c.get("text", "")))
                elif t == "tool_use":
                    ti = c.get("input")
                    if isinstance(ti, dict):
                        for v in ti.values():
                            if isinstance(v, str):
                                parts.append(v)
                elif t == "tool_result":
                    r = c.get("content")
                    if isinstance(r, str):
                        parts.append(r)
                    elif isinstance(r, list):
                        for rr in r:
                            if isinstance(rr, dict) and rr.get("type") == "text":
                                parts.append(str(rr.get("text", "")))
    return "\n".join(parts)


def extract_domains(text: str) -> set[str]:
    found: set[str] = set()
    for m in DOMAIN_RE.finditer(text):
        d = m.group(1).lower()
        parts = d.split(".")
        if len(parts) < 2:
            continue
        main = ".".join(parts[-2:])
        if main in EXCLUDE_DOMAINS:
            continue
        # 全数字二级域名(如 04926.de) 一律视为代码字段路径,非真 domain
        if parts[-2].isdigit():
            continue
        if any(ch.isdigit() for ch in parts[-2]) and len(parts[-2]) < 4:
            continue
        found.add(main)
    return found


def has_any(text: str, markers) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in markers)


def is_governance_task(text: str, threshold: int = 2) -> bool:
    """判定 transcript 是否属于治理/评分任务。

    命中 >= threshold 个 GOVERNANCE_MARKERS 视为治理上下文。阈值默认 2
    用以排除单次引用 (如 SKILL.md 描述里出现 99-SKILLS治理 链接)。
    """
    lower = text.lower()
    hits = sum(1 for k in GOVERNANCE_MARKERS if k.lower() in lower)
    return hits >= threshold


def list_site_memory_dirs() -> set[str]:
    site = REPO_ROOT / SITE_MEMORY_DIR
    if not site.exists():
        return set()
    return {
        d.name.lower()
        for d in site.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    }


def check_domain_freshness(domain: str, transcript_path: str) -> tuple[bool, str]:
    """硬检查: 任务期间 domain 目录下是否有新写入。

    以 transcript 文件 mtime 为锚, task_start = mtime - 7200s (前 2 小时窗口)。
    若 test-log-lessons.md 或 known-failures.md 任一 mtime > task_start, 视为有新写入。

    Returns:
        (True, "")           freshness OK
        (False, "提示文字")   未检测到新写入, 附建议路径

    设计:
    - 任何异常 → (True, "") 静默放行, 不让硬检查反向 crash hook
    - transcript_path 缺失或文件不存在 → 视为放行 (无锚点无法判断)
    """
    try:
        if not transcript_path:
            return (True, "")
        tp = Path(transcript_path)
        if not tp.exists():
            return (True, "")
        # 2 小时窗口: 覆盖中长任务, 同时排除几天前的旧产物
        task_start = tp.stat().st_mtime - 7200

        domain_dir = REPO_ROOT / SITE_MEMORY_DIR / domain
        if not domain_dir.exists():
            # domain 目录不存在 → 让现有的 new_domains 逻辑去提示, 这里不重复
            return (True, "")

        targets = ["test-log-lessons.md", "known-failures.md"]
        fresh = False
        missing: list[str] = []
        for name in targets:
            fp = domain_dir / name
            try:
                if fp.exists() and fp.stat().st_mtime > task_start:
                    fresh = True
                    break
                if not fp.exists():
                    missing.append(f"{SITE_MEMORY_DIR}/{domain}/{name}")
            except Exception:
                continue

        if fresh:
            return (True, "")

        if missing:
            hint = " / ".join(missing)
        else:
            hint = f"{SITE_MEMORY_DIR}/{domain}/test-log-lessons.md 或 known-failures.md"
        return (False, hint)
    except Exception:
        return (True, "")


def write_stats(
    payload: dict,
    reverse_hit: bool,
    domains: set[str],
    persisted: bool,
    exit_code: int,
    governance_hit: bool = False,
) -> None:
    try:
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": payload.get("session_id", ""),
            "cwd": payload.get("cwd", ""),
            "reverse_hit": reverse_hit,
            "governance_hit": governance_hit,
            "domains": sorted(domains),
            "persisted": persisted,
            "exit_code": exit_code,
        }
        with STATS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    if payload.get("stop_hook_active"):
        return 0

    transcript_path = payload.get("transcript_path", "")

    try:
        events = load_transcript(transcript_path)
    except Exception:
        return 0
    if not events:
        return 0

    try:
        text = extract_text(events)
    except Exception:
        return 0

    reverse_hit = has_any(text, REVERSE_MARKERS)
    completion_hit = has_any(text, COMPLETION_MARKERS)
    verification_hit = has_any(text, VERIFICATION_MARKERS)
    governance_hit = is_governance_task(text)
    needs_completion_reminder = completion_hit and not verification_hit

    if not reverse_hit and not needs_completion_reminder:
        return 0

    reminders: list[str] = []
    domains: set[str] = set()
    persisted = False
    new_domains: set[str] = set()

    # v0.4.0: 治理任务里 reverse_hit 通常来自文档案例引用 (如 05 评分文档提到
    # thaiairways) 而非实际逆向工作,跳过 domain 沉淀相关检查。
    # 完成度自评 (needs_completion_reminder) 不受此影响,治理任务也该自评。
    if reverse_hit and not governance_hit:
        try:
            domains = extract_domains(text)
        except Exception:
            domains = set()

        if not domains:
            pass
        else:
            persisted = has_any(text, PERSIST_MARKERS)
            existing = list_site_memory_dirs()
            new_domains = {d for d in domains if d not in existing}

            if new_domains or not persisted:
                rev_lines = ["[my_reverse_skill] 任务结束沉淀提醒:"]
                if new_domains:
                    rev_lines.append(
                        "  - 检测到未沉淀的 domain: " + ", ".join(sorted(new_domains))
                    )
                    rev_lines.append(
                        f"    建议先从 `{SITE_MEMORY_DIR}/_templates/` 复制 7 文件模板到对应 domain 目录"
                    )
                if not persisted:
                    rev_lines.append("  - 对话中未见沉淀动作,请考虑:")
                    rev_lines.append("    1) 写 `站点经验库/<domain>/known-failures.md` 失败模式")
                    rev_lines.append("    2) 写 `站点经验库/<domain>/test-log-lessons.md` 测试教训")
                    rev_lines.append("    3) 写 `站点经验库/<domain>/change-log.md` 变更记录")
                    rev_lines.append("    4) 跑 `python tools/sync_site_memory.py --project <P> --domain <D> --apply`")
                    rev_lines.append("    5) 调用 `skills-evaluation-governance` 给本次用到的 skill 打分")
                rev_lines.append("  详见 `99-SKILLS治理/06-网页逆向标准规划.md` 阶段 E。")
                reminders.append("\n".join(rev_lines))

            # v0.3.10: 硬检查 — 当 Claude 自称完成 + 涉及 domain 时, 验证产物是否真有更新
            # 对所有 domain (含已有目录的老 domain) 跑 mtime 检查; 新 domain 因目录不存在会被
            # check_domain_freshness 内部静默放行, 由 new_domains 提示路径接管。
            if completion_hit and domains:
                hard_lines: list[str] = []
                for d in sorted(domains):
                    try:
                        ok, hint = check_domain_freshness(d, transcript_path)
                    except Exception:
                        ok, hint = (True, "")
                    if not ok:
                        hard_lines.append(
                            f"  [硬检查] 域 {d} 在本次任务期间未见新写入,请补 {hint}"
                        )
                if hard_lines:
                    reminders.append(
                        "[my_reverse_skill] domain 产物硬检查 (mtime):\n"
                        + "\n".join(hard_lines)
                    )

    if needs_completion_reminder:
        comp_lines = [
            "[my_reverse_skill] 完成度自评提醒:",
            "  你说\"完成\"了, 但 transcript 里没看到验证动作。",
            "  按 `99-SKILLS治理/08-完成度自评.md` 走 5 维自评:",
            "    1) 代码层: 主路径端到端跑过?",
            "    2) 文档层: 自读过? 抽查命令跑过?",
            "    3) 集成层: 内链查过? 触发词与 SKILL.md 一致?",
            "    4) 回归层: 改的脚本所有依赖层都跑了?",
            "    5) 诚实层: 列了\"做了什么 + 没验证什么\"?",
            "  全打勾 = 10/10; 跳一维 = -3 分; 跳 2 维+ ≤ 5 分。",
        ]
        reminders.append("\n".join(comp_lines))

    if not reminders:
        write_stats(payload, reverse_hit, domains, persisted, exit_code=0, governance_hit=governance_hit)
        return 0

    print("\n\n".join(reminders), file=sys.stderr)
    write_stats(payload, reverse_hit, domains, persisted, exit_code=2, governance_hit=governance_hit)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
