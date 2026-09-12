# SGSITS Rulebook Auditor

> Ask any question about SGSITS Indore's academic regulations and get a traceable answer — not a confident guess.

Every response is one of exactly three states:

| State | Meaning |
|---|---|
| ✅ **RESOLVED** | The rulebook clearly answers this. Exact clause cited. |
| 🔇 **SILENT** | The rulebook doesn't cover this. No extrapolation made. |
| ⚡ **CONTRADICTION** | Two clauses give incompatible answers. Both shown side by side. |

---

## How It Works

```
User Question
     │
     ▼
BM25 Retriever  →  ranks all corpus chunks by keyword relevance
     │
     ▼
Pre-filter  →  if top score < threshold, immediately return SILENT
     │
     ▼
Gemini LLM  →  reads only the retrieved passages (not its training memory)
     │           classifies the result, quotes verbatim, flags conflicts
     ▼
JSON Response  →  { state, answer, citations[], conflict_details }
```

The LLM is given a strict system prompt: it cannot invent, infer, or extrapolate. If the answer isn't in the passages, the state is SILENT. If two passages disagree, the state is CONTRADICTION.

---

## The Corpus

Three documents, ~6,800 words total:

| File | Contents |
|---|---|
| `sgsits_ordinance_ug.md` | B.Tech academic rules: attendance, grading, backlogs, UFM, branch change |
| `fee_schedule_deadlines.md` | Semester fee deadlines, late fines, refund policy |
| `sgsits_hostel_handbook.md` | Hostel rules: curfew, leave, mess rebate, prohibited items, discipline |

### Three Planted Contradictions

These are real logical conflicts buried across the documents:

| # | Conflict | Where |
|---|---|---|
| A | Exam attendance floor: Director's absolute bar at **60%** vs Academic Council override at **50%** — same document, never reconciled | Clause 4.10.4 vs Clause 4.12.3 in `sgsits_ordinance_ug.md` |
| B | Branch-change fees: fee schedule says **non-refundable after Round 2**; ordinance says surplus fees **must be adjusted pro-rata** | `fee_schedule_deadlines.md` Line 14 vs Clause 2.4.2 in `sgsits_ordinance_ug.md` |
| C | Unapproved overnight leave: Rule 7.2 says **₹500 fine**; Rule 11.4 says **two-week suspension, explicitly no monetary penalty** | Both in `sgsits_hostel_handbook.md`, seven sections apart |

See [`contradictions.md`](contradictions.md) for verbatim quotes and full analysis.

---

## The Eval Suite

`data/test_cases.json` has 40 test cases:

- **12 RESOLVED** — questions the corpus plainly answers
- **3 CONTRADICTION** — the three planted conflicts above
- **25 SILENT** — hard near-misses the corpus cannot answer

The 25 SILENT questions are specifically designed to be *plausible and adjacent*, not absurd. Examples:
- *"Can I attend exams if my attendance shortage was due to a family wedding?"* — corpus covers medical/sports absence only
- *"Can a student retake a passed subject to improve their CGPA?"* — corpus covers backlogs only, not voluntary retakes
- *"Are electric kettles allowed in senior hostels with a utility surcharge?"* — listed as prohibited; no surcharge exception exists

Run the eval (with the server running):
```bash
python eval.py
```

Outputs a machine-readable score. Exit code `0` = overall accuracy ≥ 70%, `1` = below.

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy .env.example to .env and add your Gemini API key
#    Get a free key at: https://aistudio.google.com/apikey
cp .env.example .env

# 3. Build the search index
python engine/indexer.py

# 4. Start the server
python -m uvicorn engine.app:app --port 8000
```

Open **http://localhost:8000**

---

## Stack

- **Retrieval** — BM25, pure Python, zero ML dependencies, fully offline
- **LLM** — Gemini `gemini-1.5-flash` (free tier)
- **Backend** — FastAPI
- **Frontend** — Vanilla HTML / CSS / JS

---

*Created by **Ayush Gurjar***
