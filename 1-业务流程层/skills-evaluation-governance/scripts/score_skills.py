from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SITE_MEMORY_ROOT = REPO_ROOT / "站点经验库"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def is_todo_placeholder(path: Path) -> bool:
    try:
        text = read_text(path)
    except Exception:
        return False
    for line in text.splitlines()[:5]:
        stripped = line.strip()
        if stripped.lower().startswith("name:"):
            value = stripped.split(":", 1)[1].strip()
            if value.upper().startswith("TODO"):
                return True
            return False
    return False


def real_evals(evals: list[Path]) -> list[Path]:
    return [p for p in evals if not is_todo_placeholder(p)]


def has_negative_eval(evals: list[Path]) -> bool:
    for path in real_evals(evals):
        text = read_text(path).lower()
        if "expect_skill: false" in text or "negative" in path.name.lower():
            return True
    return False


def criteria_count(evals: list[Path]) -> int:
    total = 0
    for path in real_evals(evals):
        total += len(re.findall(r"(?m)^\s*-\s+", read_text(path)))
    return total


def has_regression_eval(evals: list[Path]) -> bool:
    for path in real_evals(evals):
        text = read_text(path).lower()
        name = path.name.lower()
        if "regression" in text or "boundary" in text or "regression" in name or "boundary" in name:
            return True
    return False


def extract_frontmatter(text: str) -> str:
    if text.startswith("---") and text.count("---") >= 2:
        return text.split("---", 2)[1]
    return ""


def extract_version(text: str, ref_text: str) -> str | None:
    patterns = [
        r"Version:\s*([0-9]+\.[0-9]+\.[0-9]+)",
        r"Current version:\s*([0-9]+\.[0-9]+\.[0-9]+)",
    ]
    for source in (text, ref_text):
        for pattern in patterns:
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                return match.group(1)
    return None


REAL_METRICS_NUMBER_PATTERNS = [
    re.compile(r"任务总数[:：\s]*(\d+)"),
    re.compile(r"任务下限[:：\s]*(\d+)"),
    re.compile(r"任务数[:：\s]*(\d+)"),
    re.compile(r"真实任务下限[:：\s]*(\d+)"),
    re.compile(r"成功率[:：\s]*(\d+)\s*%"),
    re.compile(r"命中率[:：\s]*(\d+)\s*%"),
    re.compile(r"通过率[:：\s]*(\d+)\s*%"),
]
REAL_METRICS_TABLE_DATE = re.compile(r"\|\s*\d{4}-\d{2}-\d{2}\s*\|")
ARTIFACT_DIR_NAMES = {
    "metrics", "reports", "results", "history", "real-tasks", "task-metrics",
}


def has_real_metrics_artifact(skill: Path) -> bool:
    if not skill.is_dir():
        return False
    for child in skill.iterdir():
        if not child.is_dir() or child.name.lower() not in ARTIFACT_DIR_NAMES:
            continue
        for path in child.rglob("*.md"):
            try:
                text = read_text(path)
            except Exception:
                continue
            for pat in REAL_METRICS_NUMBER_PATTERNS:
                match = pat.search(text)
                if not match:
                    continue
                try:
                    if int(match.group(1)) > 0:
                        return True
                except ValueError:
                    continue
            if REAL_METRICS_TABLE_DATE.search(text):
                return True
    return False


def _parse_expiry(meta_text: str) -> datetime.datetime | None:
    m = re.search(r'expires_at["\']?\s*:\s*["\']?([0-9T:\-Z+.]+)', meta_text)
    if not m:
        return None
    raw = m.group(1).strip().rstrip("Z") + "+00:00" if m.group(1).endswith("Z") else m.group(1).strip()
    try:
        return datetime.datetime.fromisoformat(raw)
    except Exception:
        return None


VALID_PLATFORMS = {"web", "h5", "app", "mini-program", "cross-platform"}


def _read_domain_platform(domain_dir: Path) -> str:
    """读 _platform.yaml,返回 platform 字符串(默认 web)。"""
    yaml_file = domain_dir / "_platform.yaml"
    if not yaml_file.is_file():
        return "web"
    try:
        text = yaml_file.read_text(encoding="utf-8")
    except Exception:
        return "web"
    m = re.search(r"(?m)^platform\s*:\s*([a-z-]+)", text)
    if not m:
        return "web"
    val = m.group(1).strip().lower()
    if val in VALID_PLATFORMS and val != "cross-platform":
        return val
    return "web"


def _parse_skill_platforms(text: str) -> list[str]:
    """从 SKILL.md frontmatter 抽 platforms 字段。
    支持 `platforms: [a, b]` 单行格式;无字段时默认 [cross-platform] (不限制)。
    """
    fm = extract_frontmatter(text)
    if not fm:
        return ["cross-platform"]
    m = re.search(r"(?m)^platforms\s*:\s*\[([^\]]*)\]", fm)
    if not m:
        return ["cross-platform"]
    parts = [p.strip().strip("'\"").lower() for p in m.group(1).split(",")]
    parts = [p for p in parts if p in VALID_PLATFORMS]
    return parts or ["cross-platform"]


VALID_CATEGORIES = {"foundation", "execution", "guideline"}


def _parse_skill_category(text: str) -> str:
    """从 SKILL.md frontmatter 抽 category 字段。
    枚举: foundation / execution / guideline。默认 execution。
    """
    fm = extract_frontmatter(text)
    if not fm:
        return "execution"
    m = re.search(r"(?m)^category\s*:\s*['\"]?([a-z-]+)['\"]?", fm)
    if not m:
        return "execution"
    val = m.group(1).strip().lower()
    if val in VALID_CATEGORIES:
        return val
    return "execution"


def _platforms_match(skill_platforms: list[str], domain_platform: str) -> bool:
    """skill 与 domain 是否平台匹配。cross-platform skill 任意 domain 都匹配。"""
    if "cross-platform" in skill_platforms:
        return True
    return domain_platform in skill_platforms


def _empty_consistency() -> dict:
    return {
        "fixtures_present": False,
        "snapshots_count": 0,
        "any_expiry_ok": False,
        "recent_report": False,
        "latest_rate": None,
        "domains": [],
        "domain_platforms": {},
    }


def collect_consistency_evidence_by_domain() -> dict[str, dict]:
    """扫 站点经验库/*/fixtures/, 按 domain 分组返回证据。

    返回:
      { domain: {
          fixtures_present, snapshots_count, any_expiry_ok,
          recent_report, latest_rate, platform
      } }
    """
    out: dict[str, dict] = {}
    if not SITE_MEMORY_ROOT.is_dir():
        return out

    now = datetime.datetime.now(datetime.timezone.utc)
    thirty_days_ago = now - datetime.timedelta(days=30)

    for domain_dir in SITE_MEMORY_ROOT.iterdir():
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        fix_dir = domain_dir / "fixtures"
        if not fix_dir.is_dir():
            continue

        entry = {
            "fixtures_present": True,
            "snapshots_count": 0,
            "any_expiry_ok": False,
            "recent_report": False,
            "latest_rate": None,
            "platform": _read_domain_platform(domain_dir),
        }

        snap_dir = fix_dir / "snapshots"
        if snap_dir.is_dir():
            req_files = list(snap_dir.glob("*.req.json"))
            triplets = 0
            for req in req_files:
                prefix = req.stem[:-4]
                if (snap_dir / f"{prefix}.resp.json").exists() and (snap_dir / f"{prefix}.meta.yaml").exists():
                    triplets += 1
            entry["snapshots_count"] = triplets

            for meta in snap_dir.glob("*.meta.yaml"):
                try:
                    exp_dt = _parse_expiry(meta.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if exp_dt and exp_dt > now:
                    entry["any_expiry_ok"] = True
                    break

        reports_dir = fix_dir / "reports"
        if reports_dir.is_dir():
            for report in reports_dir.glob("*-replay.md"):
                try:
                    mtime = datetime.datetime.fromtimestamp(report.stat().st_mtime, tz=datetime.timezone.utc)
                except Exception:
                    continue
                if mtime > thirty_days_ago:
                    entry["recent_report"] = True
                    break

            trend = reports_dir / "trend.json"
            if trend.is_file():
                try:
                    t = json.loads(trend.read_text(encoding="utf-8"))
                    entries = t.get("entries") or []
                    if entries:
                        latest = entries[-1]
                        if isinstance(latest, dict) and "consistency_rate" in latest:
                            entry["latest_rate"] = float(latest["consistency_rate"])
                except Exception:
                    pass

        out[domain_dir.name] = entry
    return out


def aggregate_consistency_for_skill(
    skill_platforms: list[str],
    consistency_by_domain: dict[str, dict],
) -> dict:
    """聚合该 skill 适用的 domains 的证据 → 总体 consistency 字典。"""
    out = _empty_consistency()
    rates: list[float] = []
    for domain, entry in consistency_by_domain.items():
        if not _platforms_match(skill_platforms, entry["platform"]):
            continue
        out["fixtures_present"] = True
        out["domains"].append(domain)
        out["domain_platforms"][domain] = entry["platform"]
        out["snapshots_count"] += entry["snapshots_count"]
        if entry["any_expiry_ok"]:
            out["any_expiry_ok"] = True
        if entry["recent_report"]:
            out["recent_report"] = True
        if entry["latest_rate"] is not None:
            rates.append(entry["latest_rate"])
    if rates:
        out["latest_rate"] = max(rates)
    return out


def collect_consistency_evidence() -> dict:
    """旧接口保留:返回全量合并(等价于一个 cross-platform skill 视角)。

    用于 main() 的 overall.consistency_evidence 展示。
    """
    by_domain = collect_consistency_evidence_by_domain()
    return aggregate_consistency_for_skill(["cross-platform"], by_domain)


def build_evidence(text: str, ref_text: str, evals: list[Path], refs: list[Path], agents_exists: bool) -> list[str]:
    evidence: list[str] = []
    real_e = real_evals(evals)
    if text:
        evidence.append("存在 SKILL.md")
    if "name:" in extract_frontmatter(text) and "description:" in extract_frontmatter(text):
        evidence.append("frontmatter 完整")
    if agents_exists:
        evidence.append("存在 agents/openai.yaml")
    if len(refs) >= 2:
        evidence.append(f"references 数量={len(refs)}")
    if len(real_e) >= 3:
        evidence.append(f"真实 evals 数量={len(real_e)}")
    if has_negative_eval(evals):
        evidence.append("包含负例 eval")
    if has_regression_eval(evals):
        evidence.append("包含回归/边界 eval")
    if "站点经验库" in text or "site memory" in text.lower() or "site memory" in ref_text.lower():
        evidence.append("包含经验沉淀要求")
    return evidence


def build_gaps(skill: Path, text: str, ref_text: str, evals: list[Path], refs: list[Path],
               consistency: dict) -> list[str]:
    gaps: list[str] = []
    real_e = real_evals(evals)
    if len(refs) < 2:
        gaps.append("references 偏少，细节沉淀不足")
    if len(real_e) < 3:
        gaps.append("真实 eval 数量不足，回测覆盖偏弱")
    todo_count = len(evals) - len(real_e)
    if todo_count > 0:
        gaps.append(f"{todo_count} 个 eval 仍是 TODO 占位")
    if not has_negative_eval(evals):
        gaps.append("缺少负例 eval，误触发风险较高")
    if not has_regression_eval(evals):
        gaps.append("缺少回归/边界 eval，漂移风险较高")
    if not has_real_metrics_artifact(skill):
        gaps.append("缺少真实任务命中率/完成率统计产物")
    if "known failures" not in ref_text.lower() and "test log" not in ref_text.lower() and "eval backlog" not in ref_text.lower() and "market matrix" not in ref_text.lower():
        gaps.append("缺少更强的失败模式与站点记忆证据")
    if not consistency["fixtures_present"]:
        gaps.append("仓库无任何 domain 接入一致性验证 fixtures")
    elif consistency["snapshots_count"] < 3:
        gaps.append("一致性 fixtures 不足 3 套")
    elif consistency["latest_rate"] is None:
        gaps.append("一致性 fixtures 未经过 replay 验证")
    elif consistency["latest_rate"] < 0.90:
        gaps.append(f"最新一致率 {consistency['latest_rate']:.0%} < 90%")
    return gaps


def score_structure(skill: Path, text: str, ref_text: str, refs: list[Path],
                    evals: list[Path], agents_exists: bool) -> tuple[int, dict[str, int]]:
    """满分 25"""
    checks: dict[str, int] = {}
    real_e = real_evals(evals)
    checks["skill_md"] = 5 if text else 0
    checks["frontmatter"] = 5 if "name:" in extract_frontmatter(text) and "description:" in extract_frontmatter(text) else 0
    checks["agents"] = 3 if agents_exists else 0
    checks["references"] = 4 if len(refs) >= 2 else min(len(refs) * 2, 4)
    checks["eval_layout"] = 3 if len(real_e) >= 3 else min(len(real_e), 3)
    checks["governance"] = 2 if (skill / "references" / "governance.md").exists() else 0
    main_score = 3
    if not extract_version(text, ref_text):
        main_score -= 2
    if "change log" not in text.lower() and "change log" not in ref_text.lower():
        main_score -= 1
    checks["maintainability"] = max(0, main_score)
    return min(sum(checks.values()), 25), checks


def score_operational(skill: Path, text: str, ref_text: str,
                      evals: list[Path]) -> tuple[int, dict[str, int]]:
    """满分 25"""
    checks: dict[str, int] = {}
    frontmatter = extract_frontmatter(text)
    real_e = real_evals(evals)
    criteria_total = criteria_count(evals)
    lower_text = text.lower()
    lower_refs = ref_text.lower()

    trig = 0
    if "trigger" in frontmatter.lower():
        trig += 3
    if any(ord(ch) > 127 for ch in frontmatter):
        trig += 1
    if has_negative_eval(evals):
        trig += 1
    checks["trigger_clarity"] = min(trig, 5)

    wf = 0
    for term in ("Workflow", "Success Criteria", "Boundaries", "Governance"):
        wf += 1 if term in text else 0
    if wf >= 4:
        wf += 1
    checks["workflow_behavior"] = min(wf, 5)

    eq = 0
    eq += 2 if len(real_e) >= 3 else min(len(real_e), 2)
    eq += 2 if criteria_total >= max(len(real_e) * 3, 1) else 1 if criteria_total else 0
    eq += 1 if has_regression_eval(evals) else 0
    checks["eval_quality"] = min(eq, 5)

    rt = 0
    if "orchestrator" in lower_text or "切到" in text or "use `" in lower_text:
        rt += 2
    if "不负责" in text or "not responsible" in lower_text:
        rt += 2
    checks["routing_boundaries"] = min(rt, 4)

    ev = 0
    if "site memory" in lower_text or "站点经验库" in text:
        ev += 2
    if "known failures" in lower_refs or "market matrix" in lower_refs or "eval backlog" in lower_refs:
        ev += 2
    checks["evidence_writeback"] = min(ev, 4)

    checks["real_task_metrics"] = 2 if has_real_metrics_artifact(skill) else 0

    return min(sum(checks.values()), 25), checks


def score_consistency(consistency: dict) -> tuple[int, dict[str, int]]:
    """满分 30 — 仓库层面共享指标。

    无 fixtures → 0 分,上限封到 70。
    """
    checks: dict[str, int] = {}
    checks["fixtures_present"] = 5 if consistency["fixtures_present"] else 0
    checks["snapshots_count"] = 5 if consistency["snapshots_count"] >= 3 else min(consistency["snapshots_count"] * 2, 5)
    checks["expiry_ok"] = 5 if consistency["any_expiry_ok"] else 0
    checks["recent_report"] = 5 if consistency["recent_report"] else 0
    rate = consistency.get("latest_rate")
    if rate is None:
        checks["consistency_rate"] = 0
    else:
        checks["consistency_rate"] = int(round(rate * 10))
    return min(sum(checks.values()), 30), checks


def score_drift(skill: Path, text: str, ref_text: str,
                evals: list[Path]) -> tuple[int, dict[str, int]]:
    """满分 20"""
    checks: dict[str, int] = {}
    lower_text = text.lower()
    lower_refs = ref_text.lower()

    dp = 0
    if "drift" in lower_text or "漂移" in text:
        dp += 3
    if "drift" in lower_refs or "漂移" in ref_text:
        dp += 3
    checks["drift_policy"] = min(dp, 6)

    checks["regression_coverage"] = 6 if has_regression_eval(evals) else 0

    g = 0
    if extract_version(text, ref_text):
        g += 2
    if "change log" in lower_text or "change log" in lower_refs:
        g += 2
    checks["version_change_log"] = min(g, 4)

    checks["historical_metrics"] = 4 if has_real_metrics_artifact(skill) else 0

    return min(sum(checks.values()), 20), checks


def rating_for(score: int) -> str:
    if score >= 90:
        return "高可用,产出与真实一致"
    if score >= 80:
        return "可用,一致性证据待补"
    if score >= 70:
        return "结构就绪,缺一致性验证"
    if score >= 50:
        return "偏笔记化,需要重构"
    return "原始材料"


def score_skill(skill: Path, consistency_by_domain: dict[str, dict],
                dep_completeness: float = 0.0) -> dict:
    skill_md = skill / "SKILL.md"
    agents = skill / "agents" / "openai.yaml"
    refs = sorted((skill / "references").glob("*.md")) if (skill / "references").exists() else []
    evals = sorted((skill / "evals").glob("*.yaml")) if (skill / "evals").exists() else []
    text = read_text(skill_md) if skill_md.exists() else ""
    ref_text = "\n".join(read_text(path) for path in refs)
    version = extract_version(text, ref_text)

    skill_platforms = _parse_skill_platforms(text)
    category = _parse_skill_category(text)
    consistency = aggregate_consistency_for_skill(skill_platforms, consistency_by_domain)

    if category == "foundation":
        # foundation 类只算 structure×2 + dependency_completeness, 不绑 domain 不算 consistency/operational/drift
        structure_raw, s_checks = score_structure(skill, text, ref_text, refs, evals, agents.exists())
        structure = min(structure_raw * 2, 50)
        dep_score = int(round(dep_completeness * 50))
        total = structure + dep_score
        return {
            "skill": skill.name,
            "category": "foundation",
            "version": version or "unknown",
            "platforms": skill_platforms,
            "applicable_domains": [],
            "scores": {
                "structure": structure,
                "dependency_completeness": dep_score,
                "total": total,
            },
            "rating": rating_for(total),
            "evals": len(evals),
            "real_evals": len(real_evals(evals)),
            "references": len(refs),
            "has_negative_eval": has_negative_eval(evals),
            "has_regression_eval": has_regression_eval(evals),
            "criteria_count": criteria_count(evals),
            "evidence": build_evidence(text, ref_text, evals, refs, agents.exists()),
            "gaps": build_gaps(skill, text, ref_text, evals, refs, consistency),
            "checks": {
                "structure": s_checks,
            },
        }

    structure, s_checks = score_structure(skill, text, ref_text, refs, evals, agents.exists())
    operational, o_checks = score_operational(skill, text, ref_text, evals)
    cons, c_checks = score_consistency(consistency)
    drift, d_checks = score_drift(skill, text, ref_text, evals)
    total = structure + operational + cons + drift

    return {
        "skill": skill.name,
        "category": category,
        "version": version or "unknown",
        "platforms": skill_platforms,
        "applicable_domains": consistency["domains"],
        "scores": {
            "structure": structure,
            "operational": operational,
            "consistency": cons,
            "drift": drift,
            "total": total,
        },
        "rating": rating_for(total),
        "evals": len(evals),
        "real_evals": len(real_evals(evals)),
        "references": len(refs),
        "has_negative_eval": has_negative_eval(evals),
        "has_regression_eval": has_regression_eval(evals),
        "criteria_count": criteria_count(evals),
        "evidence": build_evidence(text, ref_text, evals, refs, agents.exists()),
        "gaps": build_gaps(skill, text, ref_text, evals, refs, consistency),
        "checks": {
            "structure": s_checks,
            "operational": o_checks,
            "consistency": c_checks,
            "drift": d_checks,
        },
    }


def _find_skill_dirs(root: Path) -> list[Path]:
    """从 root 找所有含 SKILL.md 的目录;一层 + 两层都查,去重。"""
    found: set[Path] = set()
    if (root / "SKILL.md").exists():
        found.add(root)
    if root.is_dir():
        for child in root.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            if (child / "SKILL.md").exists():
                found.add(child)
            else:
                for grand in child.iterdir() if child.is_dir() else []:
                    if grand.is_dir() and (grand / "SKILL.md").exists():
                        found.add(grand)
    return sorted(found, key=lambda p: p.name)


def main() -> int:
    args = sys.argv[1:]
    output_path: Path | None = None
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 >= len(args):
            print("--output requires a path", file=sys.stderr)
            return 2
        output_path = Path(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if not args:
        print("usage: score_skills.py [--output FILE] <skills-root> [more-roots...]", file=sys.stderr)
        return 2

    roots = [Path(arg) for arg in args]
    consistency_by_domain = collect_consistency_evidence_by_domain()

    skills: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        for s in _find_skill_dirs(r):
            key = str(s.resolve())
            if key in seen:
                continue
            seen.add(key)
            skills.append(s)

    sorted_skills = sorted(skills, key=lambda p: p.name)

    # 预扫: 按 category 分桶, 算 dependency_completeness
    skill_texts: dict[str, str] = {}
    skill_categories: dict[str, str] = {}
    for s in sorted_skills:
        skill_md = s / "SKILL.md"
        text = read_text(skill_md) if skill_md.exists() else ""
        skill_texts[str(s.resolve())] = text
        skill_categories[str(s.resolve())] = _parse_skill_category(text)

    execution_paths = [s for s in sorted_skills if skill_categories[str(s.resolve())] == "execution"]
    if execution_paths:
        hit = sum(1 for s in execution_paths if "karpathy-guidelines/SKILL.md" in skill_texts[str(s.resolve())])
        dep_completeness = hit / len(execution_paths)
    else:
        dep_completeness = 0.0

    results = [score_skill(s, consistency_by_domain, dep_completeness) for s in sorted_skills]

    execution_results = [r for r in results if r.get("category") == "execution"]
    foundation_results = [r for r in results if r.get("category") == "foundation"]
    guideline_results = [r for r in results if r.get("category") == "guideline"]

    if execution_results:
        def avg(key: str) -> float:
            vals = [item["scores"][key] for item in execution_results if key in item["scores"]]
            return round(sum(vals) / len(vals), 2) if vals else 0
        overall = {
            "structure": avg("structure"),
            "operational": avg("operational"),
            "consistency": avg("consistency"),
            "drift": avg("drift"),
            "total": avg("total"),
            "execution_count": len(execution_results),
        }
    else:
        overall = {"structure": 0, "operational": 0, "consistency": 0, "drift": 0, "total": 0,
                   "execution_count": 0}

    payload = json.dumps({
        "overall": overall,
        "dependency_completeness": dep_completeness,
        "consistency_evidence": collect_consistency_evidence(),
        "consistency_by_domain": consistency_by_domain,
        "foundation_skills": foundation_results,
        "guideline_skills": guideline_results,
        "skills": results,
    }, ensure_ascii=False, indent=2)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload + "\n", encoding="utf-8")
        print(f"wrote {output_path}", file=sys.stderr)
    else:
        # stdout 重定向时 Windows 仍会用 cp936 包装,buffer 是兜底
        try:
            sys.stdout.buffer.write(payload.encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
        except AttributeError:
            print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
