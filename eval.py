#!/usr/bin/env python3
"""
eval.py — Deterministic evaluation script for the SGSITS Rulebook Auditor.

Usage:
    python eval.py [--api-url http://localhost:8000] [--test-file data/test_cases.json]

Output: machine-readable JSON report + human-readable summary to stdout.
Exit code: 0 if overall accuracy >= 70%, else 1.
"""

import json
import sys
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List


# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TEST_FILE = Path(__file__).parent / "data" / "test_cases.json"
REPORT_PATH = Path(__file__).parent / "data" / "eval_report.json"
PASS_THRESHOLD = 0.70   # 70% overall accuracy to exit 0


# ─── HTTP Helper ──────────────────────────────────────────────────────────────

def post_query(api_url: str, question: str) -> Dict[str, Any]:
    """Send a question to the /query endpoint and return the parsed JSON response."""
    payload = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(
        f"{api_url}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return {"state": "ERROR", "answer": f"HTTP {e.code}: {body}", "citations": [], "conflict_details": None}
    except Exception as e:
        return {"state": "ERROR", "answer": str(e), "citations": [], "conflict_details": None}


# ─── Scoring Logic ────────────────────────────────────────────────────────────

def score_test(test: Dict, response: Dict) -> Dict[str, Any]:
    """Score a single test case. Returns a result dict."""
    expected_state = test["expected_state"]
    pred_state = response.get("state", "ERROR")
    state_correct = pred_state == expected_state

    result = {
        "id": test["id"],
        "question": test["question"],
        "expected_state": expected_state,
        "predicted_state": pred_state,
        "state_correct": state_correct,
        "citation_correct": False,
        "conflict_clauses_matched": False,
        "notes": test.get("notes", ""),
    }

    if expected_state == "RESOLVED" and state_correct:
        expected_section = test.get("expected_section", "")
        citations = [c.get("section", "") for c in response.get("citations", [])]
        # Citation correct if any citation string contains the expected section marker
        result["citation_correct"] = any(
            expected_section.split("/")[0].strip() in c
            for c in citations
        ) if expected_section else True

    elif expected_state == "CONTRADICTION" and state_correct:
        expected_conflicts = test.get("expected_conflicts", [])
        conflict = response.get("conflict_details") or {}
        clause_a = conflict.get("clause_a", "")
        clause_b = conflict.get("clause_b", "")
        all_clauses_text = clause_a + " " + clause_b

        # Check if both expected conflict markers appear anywhere in the conflict details
        matched = all(exp in all_clauses_text for exp in expected_conflicts)
        result["conflict_clauses_matched"] = matched

    return result


# ─── Main Eval Runner ─────────────────────────────────────────────────────────

def run_eval(api_url: str, test_file: Path) -> Dict[str, Any]:
    with open(test_file, "r", encoding="utf-8") as f:
        tests: List[Dict] = json.load(f)

    metrics = {
        "total": len(tests),
        "correct_state": 0,
        "resolved": {"total": 0, "correct_state": 0, "citation_correct": 0},
        "silent": {"total": 0, "correct_state": 0, "false_positives": 0},
        "contradiction": {"total": 0, "correct_state": 0, "clauses_matched": 0},
        "errors": 0,
    }

    results = []
    print(f"\n{'='*60}")
    print(f"  SGSITS RULEBOOK AUDITOR - EVAL SUITE")
    print(f"  API: {api_url} | Tests: {len(tests)}")
    print(f"{'='*60}\n")

    for i, test in enumerate(tests, 1):
        q = test["question"]
        expected = test["expected_state"]
        print(f"[{i:02d}/{len(tests)}] {test['id']} — {q[:70]}{'...' if len(q)>70 else ''}")
        print(f"       Expected: {expected}", end=" | ")

        response = post_query(api_url, q)
        time.sleep(0.3)   # Be gentle with the API

        scored = score_test(test, response)
        results.append({**scored, "response": response})

        pred = scored["predicted_state"]
        correct = "✓" if scored["state_correct"] else "✗"
        print(f"Got: {pred} {correct}")

        if scored["state_correct"]:
            metrics["correct_state"] += 1

        # Per-category tracking
        cat = expected.lower()
        if cat in ("resolved", "silent", "contradiction"):
            key = cat if cat != "resolved" else "resolved"
            if cat == "resolved":
                metrics["resolved"]["total"] += 1
                if scored["state_correct"]:
                    metrics["resolved"]["correct_state"] += 1
                    if scored["citation_correct"]:
                        metrics["resolved"]["citation_correct"] += 1
            elif cat == "silent":
                metrics["silent"]["total"] += 1
                if scored["state_correct"]:
                    metrics["silent"]["correct_state"] += 1
                else:
                    metrics["silent"]["false_positives"] += 1
            elif cat == "contradiction":
                metrics["contradiction"]["total"] += 1
                if scored["state_correct"]:
                    metrics["contradiction"]["correct_state"] += 1
                    if scored["conflict_clauses_matched"]:
                        metrics["contradiction"]["clauses_matched"] += 1

        if pred == "ERROR":
            metrics["errors"] += 1

    overall_acc = metrics["correct_state"] / max(metrics["total"], 1)

    print(f"\n{'='*60}")
    print(f"  TEST SUITE REPORT")
    print(f"{'='*60}")
    print(f"  Total Test Cases:        {metrics['total']}")
    print(f"  Overall State Accuracy:  {metrics['correct_state']}/{metrics['total']}  ({overall_acc*100:.1f}%)")
    print(f"{'-'*60}")
    print(f"  RESOLVED   state correct: {metrics['resolved']['correct_state']}/{metrics['resolved']['total']}")
    print(f"  RESOLVED   citations ok:  {metrics['resolved']['citation_correct']}/{metrics['resolved']['correct_state']}")
    print(f"{'-'*60}")
    print(f"  SILENT     state correct: {metrics['silent']['correct_state']}/{metrics['silent']['total']}")
    print(f"  SILENT     false positives (answered when should be silent): {metrics['silent']['false_positives']}")
    print(f"{'-'*60}")
    print(f"  CONTRADICTION detected:  {metrics['contradiction']['correct_state']}/{metrics['contradiction']['total']}")
    print(f"  CONTRADICTION clauses:   {metrics['contradiction']['clauses_matched']}/{metrics['contradiction']['correct_state']}")
    print(f"{'-'*60}")
    print(f"  API Errors:              {metrics['errors']}")
    print(f"{'='*60}")
    verdict = "PASS" if overall_acc >= PASS_THRESHOLD else "FAIL"
    print(f"  VERDICT: {verdict}  (threshold: {PASS_THRESHOLD*100:.0f}%)")
    print(f"{'='*60}\n")

    report = {
        "api_url": api_url,
        "test_file": str(test_file),
        "metrics": metrics,
        "overall_accuracy": round(overall_acc, 4),
        "verdict": verdict,
        "pass_threshold": PASS_THRESHOLD,
        "results": results,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Full report saved → {REPORT_PATH}\n")

    return report


# ─── CLI Entry ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eval script for SGSITS Rulebook Auditor")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Base URL of the running API server")
    parser.add_argument("--test-file", default=str(DEFAULT_TEST_FILE), help="Path to test_cases.json")
    args = parser.parse_args()

    report = run_eval(args.api_url, Path(args.test_file))
    sys.exit(0 if report["verdict"] == "PASS" else 1)
