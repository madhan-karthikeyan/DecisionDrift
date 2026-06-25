# DecisionDrift Evaluation Report

**Test Corpus:** 21 patches (13 violations, 8 non-violations)

## Retrieval Accuracy

| Metric | Value |
|--------|-------|
| Patches tested | 21 |
| Recall@5 | 20/21 (**95.2%**) |
| Recall@1 | 18/21 (**85.7%**) |

**Note:** Retrieval measures whether the expected ADR(s) appear in the top findings. No LLM required — purely keyword-based weighted overlap scoring.

### Per-Patch Retrieval

| Patch | Expected ADR | Top-5 Hit | Top-1 Hit |
|-------|-------------|-----------|-----------|
| App Factory Violation | ADR-0012, ADR-0001 | ✅ | ❌ |
| Blueprint Addition | ADR-0004 | ✅ | ✅ |
| Blueprint Violation | ADR-0004 | ✅ | ✅ |
| Celery Beat Violation | ADR-0011, ADR-0005 | ✅ | ✅ |
| Celery Refactor | ADR-0005 | ✅ | ✅ |
| Celery Violation | ADR-0005 | ✅ | ✅ |
| Clean Change | ADR-0002, ADR-0008 | ✅ | ✅ |
| Factory Usage | ADR-0012, ADR-0001 | ✅ | ❌ |
| Flask Framework Violation | ADR-0001 | ❌ | ❌ |
| Jwt Valid Change | ADR-0003 | ✅ | ✅ |
| Jwt Violation | ADR-0003 | ✅ | ✅ |
| Notification Usage | ADR-0009 | ✅ | ✅ |
| Notification Violation | ADR-0009, ADR-0005 | ✅ | ✅ |
| Razorpay Violation | ADR-0010 | ✅ | ✅ |
| Rbac Cleanup | ADR-0007, ADR-0003 | ✅ | ✅ |
| Rbac Doctor Violation | ADR-0003, ADR-0007 | ✅ | ✅ |
| Rbac Violation | ADR-0007, ADR-0004 | ✅ | ✅ |
| Redis Valid Usage | ADR-0006 | ✅ | ✅ |
| Redis Violation | ADR-0006 | ✅ | ✅ |
| Sqlalchemy Violation | ADR-0002, ADR-0008 | ✅ | ✅ |
| Uuid Violation | ADR-0008 | ✅ | ✅ |

### Miss Analysis

**Flask Framework Violation (Recall@5 miss):** The patch uses raw `http.server.BaseHTTPRequestHandler` — no mention of "flask" anywhere in the diff. Keyword-based retrieval cannot detect this because the search terms extracted from `BaseHTTPRequestHandler` (via camelCase splitting) produce `["Base", "H", "T", "T", "P", "Request", "Handler"]` — none of which match ADR-0001's keywords (`flask`, `web framework`, `application`, `http`). This is a known limitation of keyword-only retrieval. Embedding-based retrieval would catch this via semantic similarity.

**App Factory Violation / Factory Usage (Recall@1 miss):** Both patches expect ADR-0012 (Use Application Factory Pattern) but retrieve it at position 2–5 rather than position 1. The keyword overlap with ADR-0002 (Use SQLAlchemy as ORM) is stronger due to broader keyword coverage. Still correctly retrieved within top-5.

## Classification Accuracy

**Note:** The classification tests require an LLM API key with available quota. During the Groq rate-limit window (100K tokens/day), all LLM calls fall back to `needs_human_review`. Run `pytest tests/evaluation/test_evaluation.py -k classification` with a fresh API quota to populate these metrics.

Requires `DECISIONDRIFT_LLM_API_KEY` to be set. Run the evaluation suite with an LLM provider configured to populate these metrics.

| Metric | Value |
|--------|-------|
| True Positives | — |
| False Positives | — |
| False Negatives | — |
| True Negatives | — |
| Precision | — |
| Recall | — |
| F1 Score | — |

## End-to-End Summary

| Component | Metric | Score |
|-----------|--------|-------|
| Retrieval | Recall@5 | 95.2% |
| Retrieval | Recall@1 | 85.7% |
| Classification | Precision | _requires LLM key_ |
| Classification | Recall | _requires LLM key_ |
| Classification | F1 | _requires LLM key_ |

---

*DecisionDrift evaluation report. Generated from 21 test patches against the HMS-V2 ADR corpus (12 ADRs).*
