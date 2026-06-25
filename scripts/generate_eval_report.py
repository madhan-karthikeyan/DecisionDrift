"""Generate docs/evaluation.md from evaluation metrics."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EVAL_DIR = REPO_ROOT / "tests" / "evaluation"


def _fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def _fmt_ratio(hits: int, total: int) -> str:
    return f"{hits}/{total} ({_fmt_pct(hits / total)})" if total else "N/A"


def _fmt_score(v: float) -> str:
    return f"{v:.3f}"


def _short_patch_name(name: str) -> str:
    """Convert snake_case to readable title."""
    return name.replace("_", " ").title()


def generate():
    # Import after path setup
    import sys

    sys.path.insert(0, str(REPO_ROOT))
    from tests.evaluation.test_evaluation_metrics import compute_classification_metrics, compute_retrieval_metrics

    print("Computing retrieval metrics...")
    retrieval = compute_retrieval_metrics()

    print("Computing classification metrics...")
    classification = compute_classification_metrics()

    lines = [
        "# DecisionDrift Evaluation Report",
        "",
        "**Generated:** _(auto-generated)_",
        "",
        f"**Test Corpus:** {retrieval['total']} patches ({sum(1 for d in retrieval['details'] if 'violation' in d['name'] or d['name'] in ('sqlalchemy_violation', 'jwt_violation', 'celery_violation', 'rbac_violation', 'redis_violation', 'notification_violation', 'razorpay_violation', 'celery_beat_violation', 'app_factory_violation', 'flask_framework_violation', 'uuid_violation', 'blueprint_violation', 'rbac_doctor_violation'))} violations, "
        f"{sum(1 for d in retrieval['details'] if 'violation' not in d['name'] and d['name'] not in ('sqlalchemy_violation', 'jwt_violation', 'celery_violation', 'rbac_violation', 'redis_violation', 'notification_violation', 'razorpay_violation', 'celery_beat_violation', 'app_factory_violation', 'flask_framework_violation', 'uuid_violation', 'blueprint_violation', 'rbac_doctor_violation'))} non-violations)",
        "",
        "## Retrieval Accuracy",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Patches tested | {retrieval['total']} |",
        f"| Recall@5 | {_fmt_ratio(retrieval['top5_hits'], retrieval['total'])} |",
        f"| Recall@1 | {_fmt_ratio(retrieval['top1_hits'], retrieval['total'])} |",
        "",
        "**Note:** Retrieval measures whether the expected ADR(s) appear in the top findings. "
        "No LLM required — purely keyword-based scoring.",
        "",
        "### Per-Patch Retrieval",
        "",
        "| Patch | Expected ADR | Retrieved ADRs | Hit@5 | Hit@1 |",
        "|-------|-------------|----------------|-------|-------|",
    ]

    for d in sorted(retrieval["details"], key=lambda x: x["name"]):
        lines.append(
            f"| {_short_patch_name(d['name'])} | {', '.join(d['expected'])} | "
            f"{', '.join(d['retrieved'][:5])} | "
            f"{'✅' if d['top5_hit'] else '❌'} | {'✅' if d['top1_hit'] else '❌'} |"
        )

    lines.extend(
        [
            "",
            "## Classification Accuracy",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| True Positives | {classification['tp']} |",
            f"| False Positives | {classification['fp']} |",
            f"| False Negatives | {classification['fn']} |",
            f"| True Negatives | {classification['tn']} |",
            f"| Precision | {_fmt_score(classification['precision'])} |",
            f"| Recall | {_fmt_score(classification['recall'])} |",
            f"| F1 Score | {_fmt_score(classification['f1'])} |",
            "",
            "**Note:** Classification requires DECISIONDRIFT_LLM_API_KEY. "
            "Metrics reflect the configured LLM's performance.",
            "",
            "### Per-Patch Classification",
            "",
            "| Patch | Type | Primary ADR | Classification | Correct? |",
            "|-------|------|-------------|---------------|----------|",
        ]
    )

    for d in sorted(classification["details"], key=lambda x: x["name"]):
        cls_strs = []
        for adr_id, cls in d["classifications"].items():
            if adr_id == d["primary_adr"]:
                cls_strs.append(f"{adr_id}:{cls}")
        cls_display = "; ".join(cls_strs[:3]) if cls_strs else "N/A"
        ptype = "violation" if d["is_violation"] else "clean"
        correct = (d["is_violation"] and d["found_in_violations"]) or (
            not d["is_violation"] and not d["found_in_violations"]
        )
        lines.append(
            f"| {_short_patch_name(d['name'])} | {ptype} | {d['primary_adr'] or 'N/A'} | "
            f"{cls_display} | {'✅' if correct else '❌'} |"
        )

    lines.extend(
        [
            "",
            "## End-to-End Summary",
            "",
            "| Component | Metric | Score |",
            "|-----------|--------|-------|",
            f"| Retrieval | Recall@5 | {_fmt_pct(retrieval['recall_at_5'])} |",
            f"| Retrieval | Recall@1 | {_fmt_pct(retrieval['recall_at_1'])} |",
            f"| Classification | Precision | {_fmt_score(classification['precision'])} |",
            f"| Classification | Recall | {_fmt_score(classification['recall'])} |",
            f"| Classification | F1 | {_fmt_score(classification['f1'])} |",
            "",
            "---",
            "",
            "*DecisionDrift evaluation report.*",
            "",
        ]
    )

    eval_md = REPO_ROOT / "docs" / "evaluation.md"
    eval_md.write_text("\n".join(lines))
    print(f"Written to {eval_md}")


if __name__ == "__main__":
    generate()
