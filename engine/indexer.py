import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict

RULEBOOK_DIR = Path(__file__).parent.parent / "rulebook"
INDEX_PATH = Path(__file__).parent.parent / "data" / "corpus_index.json"

# Each chunk is ~400 words with 80-word overlap so neighboring chunks share context.
# This helps BM25 find relevant passages even when a clause spans a section boundary.
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def chunk_text(text: str, source: str, section_hint: str = "") -> List[Dict]:
    words = text.split()
    chunks = []
    i = 0
    chunk_index = 0
    while i < len(words):
        chunk_words = words[i: i + CHUNK_SIZE]
        chunk_id = hashlib.md5(f"{source}_{chunk_index}".encode()).hexdigest()[:12]
        chunks.append({
            "id": chunk_id,
            "source": source,
            "section_hint": section_hint,
            "text": " ".join(chunk_words),
            "word_count": len(chunk_words),
        })
        i += CHUNK_SIZE - CHUNK_OVERLAP
        chunk_index += 1
    return chunks


def extract_section_hint(header: str) -> str:
    return header.strip("#").strip()


def parse_markdown(filepath: Path) -> List[Dict]:
    """
    Splits a Markdown file at heading boundaries so each chunk carries its
    section label as metadata. This label appears in citations shown to the user.
    """
    source = filepath.name
    lines = filepath.read_text(encoding="utf-8").splitlines()

    sections = []
    current_header = "Preamble"
    current_lines = []

    for line in lines:
        if re.match(r"^#{1,4}\s", line):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_header, body))
            current_header = extract_section_hint(line)
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append((current_header, body))

    all_chunks = []
    for header, body in sections:
        all_chunks.extend(chunk_text(f"[{header}]\n{body}", source, section_hint=header))

    return all_chunks


def parse_table_doc(filepath: Path) -> List[Dict]:
    # Fee schedule is short enough to keep as a single block so the
    # table rows don't get split across chunks and lose their context.
    source = filepath.name
    text = filepath.read_text(encoding="utf-8")
    return chunk_text(text, source, section_hint="Fee Schedule Table")


def build_index():
    all_chunks: List[Dict] = []

    for filepath in sorted(RULEBOOK_DIR.glob("*")):
        ext = filepath.suffix.lower()
        print(f"  Indexing: {filepath.name}")

        if ext == ".md":
            if "fee_schedule" in filepath.name:
                chunks = parse_table_doc(filepath)
            else:
                chunks = parse_markdown(filepath)
        else:
            print(f"    Skipped: {filepath.name}")
            continue

        all_chunks.extend(chunks)
        print(f"    -> {len(chunks)} chunks")

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Index built: {len(all_chunks)} total chunks -> {INDEX_PATH}")
    return all_chunks


if __name__ == "__main__":
    build_index()
