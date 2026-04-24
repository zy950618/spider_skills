from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def has_negative_eval(evals: list[Path]) -> bool:
    for path in evals:
        text = read_text(path).lower()
        if "expect_skill: false" in text or "negative" in path.name.lower():
            return True
    return False


def criteria_count(evals: list[Path]) -> int:
    total = 0
    for path in evals:
        total += len(re.findall(r"(?m)^\s*-\s+", read_text(path)))
    return total


def has_regression_eval(evals: list[Path]) -> bool:
    for path in evals:
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


def has_real_metrics_artifact(skill: Path) -> bool:
    artifact_names = {
        "metrics",
        "reports",
        "results",
        "history",
        "real-tasks",
        "task-metrics",
    }
    for child in skill.iterdir():
        if child.name.lower() in artifact_names:
            return True
    return False


def build_evidence(text: str, ref_text: str, evals: list[Path], refs: list[Path], agents_exists: bool) -> list[str]:
    evidence: list[str] = []
    if text:
        evidence.append("存在 SKILL.md")
    if "name:" in extract_frontmatter(text) and "description:" in extract_frontmatter(text):
        evidence.append("frontmatter 完整")
    if agents_exists:
        evidence.append("存在 agents/openai.yaml")
    if len(refs) >= 2:
        evidence.append(f"references 数量={len(refs)}")
    if len(evals) >= 3:
        evidence.append(f"evals 数量={len(evals)}")
    if has_negative_eval(evals):
        evidence.append("包含负例 eval")
    if has_regression_eval(evals):
        evidence.append("包含回归/边界 eval")
    if "站点经验库" in text or "site memory" in text.lower() or "site memory" in ref_text.lower():
        evidence.append("包含经验沉淀要求")
    return evidence


def build_gaps(skill: Path, text: str, ref_text: str, evals: list[Path], refs: list[Path]) -> list[str]:
    gaps: list[str] = []
    if len(refs) < 2:
        gaps.append("references 偏少，细节沉淀不足")
    if len(evals) < 3:
        gaps.append("eval 数量不足，回测覆盖偏弱")
    if not has_negative_eval(evals):
        gaps.append("缺少负例 eval，误触发风险较高")
    if not has_regression_eval(evals):
        gaps.append("缺少回归/边界 eval，漂移风险较高")
    if not has_real_metrics_artifact(skill):
        gaps.append("缺少真实任务命中率/完成率统计产物")
        gaps.append("缺少按周期记录的漂移指标与历史结果")
    if "known failures" not in ref_text.lower() and "test log" not in ref_text.lower() and "eval backlog" not in ref_text.lower() and "market matrix" not in ref_text.lower():
        gaps.append("缺少更强的失败模式与站点记忆证据")
    return gaps


def score_structure(skill: Path, text: str, ref_text: str, refs: list[Path], evals: list[Path], agents_exists: bool) -> tuple[int, dict[str, int]]:
    score = 0
    checks: dict[str, int] = {}

    skill_md_score = 8 if text else 0
    frontmatter_score = 8 if "name:" in extract_frontmatter(text) and "description:" in extract_frontmatter(text) else 0
    agents_score = 5 if agents_exists else 0
    references_score = 7 if len(refs) >= 2 else min(len(refs) * 3, 7)
    evals_score = 5 if len(evals) >= 3 else min(len(evals) * 2, 5)
    governance_score = 3 if (skill / "references" / "governance.md").exists() else 0
    maintainability_score = 4
    if not extract_version(text, ref_text):
        maintainability_score -= 2
    if "change log" not in text.lower() and "change log" not in ref_text.lower():
        maintainability_score -= 2
    maintainability_score = max(0, maintainability_score)

    checks["skill_md"] = skill_md_score
    checks["frontmatter"] = frontmatter_score
    checks["agents"] = agents_score
    checks["references"] = references_score
    checks["eval_layout"] = evals_score
    checks["governance"] = governance_score
    checks["maintainability"] = maintainability_score

    score = sum(checks.values())
    return min(score, 40), checks


def score_operational(skill: Path, text: str, ref_text: str, evals: list[Path]) -> tuple[int, dict[str, int]]:
    score = 0
    checks: dict[str, int] = {}
    frontmatter = extract_frontmatter(text)
    criteria_total = criteria_count(evals)
    lower_text = text.lower()
    lower_refs = ref_text.lower()

    trigger_score = 0
    if "trigger" in frontmatter.lower():
        trigger_score += 4
    if any(ord(ch) > 127 for ch in frontmatter):
        trigger_score += 2
    if has_negative_eval(evals):
        trigger_score += 2
    trigger_score = min(trigger_score, 8)

    workflow_score = 0
    for term in ("Workflow", "Success Criteria", "Boundaries", "Governance"):
        workflow_score += 2 if term in text else 0
    workflow_score = min(workflow_score, 8)

    eval_quality_score = 0
    eval_quality_score += 3 if len(evals) >= 3 else min(len(evals), 3)
    eval_quality_score += 3 if criteria_total >= max(len(evals) * 3, 1) else 1 if criteria_total else 0
    eval_quality_score += 2 if has_regression_eval(evals) else 0
    eval_quality_score = min(eval_quality_score, 8)

    routing_score = 0
    if "orchestrator" in lower_text or "切到" in text or "use `" in lower_text:
        routing_score += 3
    if "不负责" in text or "not responsible" in lower_text or "不是" in text:
        routing_score += 3
    routing_score = min(routing_score, 6)

    evidence_score = 0
    if "site memory" in lower_text or "站点经验库" in text:
        evidence_score += 2
    if "testing" in lower_refs or "test log" in lower_refs or "delivery-checklist" in lower_refs:
        evidence_score += 2
    if "known failures" in lower_refs or "market matrix" in lower_refs or "eval backlog" in lower_refs or "site-memory-scoring" in lower_refs:
        evidence_score += 2
    evidence_score = min(evidence_score, 6)

    metrics_score = 4 if has_real_metrics_artifact(skill) else 0

    checks["trigger_clarity"] = trigger_score
    checks["workflow_behavior"] = workflow_score
    checks["eval_quality"] = eval_quality_score
    checks["routing_boundaries"] = routing_score
    checks["evidence_writeback"] = evidence_score
    checks["real_task_metrics"] = metrics_score

    score = sum(checks.values())
    return min(score, 40), checks


def score_drift(skill: Path, text: str, ref_text: str, evals: list[Path]) -> tuple[int, dict[str, int]]:
    score = 0
    checks: dict[str, int] = {}
    lower_text = text.lower()
    lower_refs = ref_text.lower()

    drift_policy_score = 0
    if "drift" in lower_text or "漂移" in text:
        drift_policy_score += 3
    if "drift" in lower_refs or "漂移" in ref_text:
        drift_policy_score += 3
    drift_policy_score = min(drift_policy_score, 6)

    regression_score = 6 if has_regression_eval(evals) else 0

    governance_score = 0
    if extract_version(text, ref_text):
        governance_score += 2
    if "change log" in lower_text or "change log" in lower_refs:
        governance_score += 2
    governance_score = min(governance_score, 4)

    historical_score = 4 if has_real_metrics_artifact(skill) else 0

    checks["drift_policy"] = drift_policy_score
    checks["regression_coverage"] = regression_score
    checks["version_change_log"] = governance_score
    checks["historical_metrics"] = historical_score

    score = sum(checks.values())
    return min(score, 20), checks


def rating_for(score: int) -> str:
    if score >= 90:
        return "高可用，待补真实统计"
    if score >= 80:
        return "可用基线，待补实战证据"
    if score >= 70:
        return "候选，需要补强"
    if score >= 50:
        return "偏笔记化，需要重构"
    return "原始材料"


def score_skill(skill: Path) -> dict:
    skill_md = skill / "SKILL.md"
    agents = skill / "agents" / "openai.yaml"
    refs = sorted((skill / "references").glob("*.md")) if (skill / "references").exists() else []
    evals = sorted((skill / "evals").glob("*.yaml")) if (skill / "evals").exists() else []
    text = read_text(skill_md) if skill_md.exists() else ""
    ref_text = "\n".join(read_text(path) for path in refs)
    version = extract_version(text, ref_text)

    structure, structure_checks = score_structure(skill, text, ref_text, refs, evals, agents.exists())
    operational, operational_checks = score_operational(skill, text, ref_text, evals)
    drift, drift_checks = score_drift(skill, text, ref_text, evals)
    total = structure + operational + drift

    return {
        "skill": skill.name,
        "version": version or "unknown",
        "scores": {
            "structure": structure,
            "operational": operational,
            "drift": drift,
            "total": total,
        },
        "rating": rating_for(total),
        "evals": len(evals),
        "references": len(refs),
        "has_negative_eval": has_negative_eval(evals),
        "has_regression_eval": has_regression_eval(evals),
        "criteria_count": criteria_count(evals),
        "evidence": build_evidence(text, ref_text, evals, refs, agents.exists()),
        "gaps": build_gaps(skill, text, ref_text, evals, refs),
        "checks": {
            "structure": structure_checks,
            "operational": operational_checks,
            "drift": drift_checks,
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: score_skills.py <skills-root>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    skills = [path for path in root.iterdir() if path.is_dir() and (path / "SKILL.md").exists()]
    results = [score_skill(skill) for skill in sorted(skills, key=lambda path: path.name)]

    if results:
        overall_structure = round(sum(item["scores"]["structure"] for item in results) / len(results), 2)
        overall_operational = round(sum(item["scores"]["operational"] for item in results) / len(results), 2)
        overall_drift = round(sum(item["scores"]["drift"] for item in results) / len(results), 2)
        overall_total = round(sum(item["scores"]["total"] for item in results) / len(results), 2)
    else:
        overall_structure = 0
        overall_operational = 0
        overall_drift = 0
        overall_total = 0

    print(
        json.dumps(
            {
                "overall": {
                    "structure": overall_structure,
                    "operational": overall_operational,
                    "drift": overall_drift,
                    "total": overall_total,
                },
                "skills": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
