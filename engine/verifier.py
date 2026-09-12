import os
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).parent.parent / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"

RELEVANCE_THRESHOLD = 0.5
MIN_PASSAGES = 2

SYSTEM_PROMPT = """You are a strict academic regulation auditor for SGSITS Indore (Shri G. S. Institute of Technology and Science).

Your ONLY job is to answer questions based on the provided rulebook passages. You must NEVER use general knowledge about universities or infer rules that are not explicitly stated.

You must classify every response into exactly ONE of three states:
- RESOLVED: The passages clearly and consistently answer the question. Provide the answer with citations.
- SILENT: The passages do not contain information sufficient to answer this question. Do NOT guess or extrapolate.
- CONTRADICTION: Two or more passages give incompatible answers to the same question. Identify both conflicting passages precisely.

CRITICAL RULES:
1. Do NOT invent, infer, or extrapolate. If it is not in the passages, it is SILENT.
2. Do NOT be over-cautious — if the answer is clearly in the passages, say RESOLVED.
3. If two passages give different answers to the same question, say CONTRADICTION even if one seems more authoritative.
4. Every claim in your answer must be traceable to a specific passage.
5. Your response MUST be valid JSON matching the schema below exactly.

RESPONSE SCHEMA:
{
  "state": "RESOLVED" | "SILENT" | "CONTRADICTION",
  "answer": "Plain language answer (empty string if SILENT)",
  "citations": [
    {
      "source_document": "filename",
      "section": "section/clause label",
      "verbatim_text": "exact quote from passage (max 200 chars)"
    }
  ],
  "conflict_details": {
    "clause_a": "First conflicting clause label",
    "clause_b": "Second conflicting clause label",
    "nature_of_contradiction": "One sentence describing the conflict"
  } | null,
  "confidence": 0.0-1.0
}

If state is RESOLVED or SILENT, set conflict_details to null.
If state is CONTRADICTION, still provide an answer explaining the conflict.
Always return valid JSON. Do not include markdown code fences."""

USER_PROMPT_TEMPLATE = """QUESTION: {question}

RETRIEVED PASSAGES (ranked by relevance):
{passages_text}

Analyze the passages above and respond with the JSON schema."""


def format_passages(passages: List[Dict]) -> str:
    lines = []
    for i, p in enumerate(passages, 1):
        lines.append(
            f"[{i}] SOURCE: {p['source']} | SECTION: {p.get('section_hint', 'N/A')} "
            f"| SCORE: {p.get('relevance_score', 0):.3f}\n"
            f"{p['text'][:600]}"
        )
    return "\n\n".join(lines)


def likely_silent(passages: List[Dict]) -> bool:
    """
    If BM25 can barely find anything relevant, don't bother asking the LLM.
    A model with thin evidence will guess, and guessing is worse than saying nothing.
    """
    if not passages:
        return True
    return passages[0].get("relevance_score", 0) < RELEVANCE_THRESHOLD and len(passages) < MIN_PASSAGES


def verify(question: str, passages: List[Dict]) -> Dict[str, Any]:
    if likely_silent(passages):
        return {
            "state": "SILENT",
            "answer": "",
            "citations": [],
            "conflict_details": None,
            "confidence": 0.95,
        }

    if not GEMINI_API_KEY:
        return _error_response("GEMINI_API_KEY environment variable not set.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    user_msg = USER_PROMPT_TEMPLATE.format(
        question=question,
        passages_text=format_passages(passages)
    )

    # Gemini free tier is generous but still rate-limits on burst. Retry with backoff.
    RETRY_WAITS = [5, 15, 30]
    raw = ""
    for attempt, wait in enumerate(RETRY_WAITS):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0,
                    max_output_tokens=1200,
                ),
            )

            raw = response.text.strip()
            # Strip markdown fences if model adds them despite instructions.
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            parsed = json.loads(raw)
            _validate_response(parsed)
            return parsed

        except json.JSONDecodeError as e:
            return _error_response(f"JSON parse error: {e}. Raw: {raw[:200]}")
        except Exception as e:
            err = str(e)
            is_rate_limit = "429" in err or "quota" in err.lower() or "rate" in err.lower()
            if is_rate_limit:
                print(f"[Rate limit] Waiting {wait}s before retry {attempt + 1}/{len(RETRY_WAITS)}...")
                time.sleep(wait)
                continue
            return _error_response(err)

    return _error_response("Rate limit exceeded. Please wait ~30 seconds and try again.")


def _validate_response(data: Dict):
    assert data.get("state") in ("RESOLVED", "SILENT", "CONTRADICTION"), \
        f"Invalid state: {data.get('state')}"
    assert "answer" in data, "Missing 'answer' field"
    assert "citations" in data, "Missing 'citations' field"


def _error_response(msg: str) -> Dict[str, Any]:
    return {
        "state": "ERROR",
        "answer": f"System error: {msg}",
        "citations": [],
        "conflict_details": None,
        "confidence": 0.0,
        "error": msg
    }


if __name__ == "__main__":
    import sys
    from retriever import retrieve

    q = " ".join(sys.argv[1:]) or "What is the minimum attendance to sit the exam?"
    result = verify(q, retrieve(q, top_k=8))
    print(json.dumps(result, indent=2, ensure_ascii=False))
