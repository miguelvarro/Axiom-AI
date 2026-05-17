from __future__ import annotations

import re
from typing import Optional, Dict

from ai_consensus_clone.utils.text import clean_text


SECTION_PATTERNS = {
    "results": [
        r"\bresults?\b",
        r"\bfindings\b",
    ],
    "discussion": [
        r"\bdiscussion\b",
    ],
    "conclusion": [
        r"\bconclusion\b",
        r"\bconclusions\b",
        r"\bfinal conclusions?\b",
    ],
}


def normalize_full_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    text = clean_text(text)
    text = text.replace("\x00", " ")
    text = " ".join(text.split())
    text = text.strip()

    return text or None


def build_preview(text: Optional[str], max_chars: int = 4000) -> str:
    if not text:
        return ""
    text = normalize_full_text(text) or ""
    return text[:max_chars]


def ensure_non_empty_full_text(
    full_text: Optional[str],
    abstract: Optional[str],
) -> Optional[str]:
    ft = normalize_full_text(full_text)
    if ft:
        return ft

    ab = normalize_full_text(abstract)
    if ab:
        return ab

    return None


def infer_fallback_source(
    current_source: Optional[str],
    abstract: Optional[str],
) -> Optional[str]:
    if current_source:
        return current_source
    if abstract:
        return "openalex_abstract"
    return None


def _find_first_heading(text: str, patterns: list[str]) -> Optional[re.Match]:
    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m
    return None


def _find_next_section_start(text: str, start_pos: int) -> Optional[int]:
    candidates = []
    for section_patterns in SECTION_PATTERNS.values():
        for pat in section_patterns:
            for m in re.finditer(pat, text, flags=re.I):
                if m.start() > start_pos:
                    candidates.append(m.start())

    if not candidates:
        return None
    return min(candidates)


def extract_named_sections(text: Optional[str]) -> Dict[str, Optional[str]]:
    raw = normalize_full_text(text)
    if not raw:
        return {
            "results_text": None,
            "discussion_text": None,
            "conclusion_text": None,
        }

    out: Dict[str, Optional[str]] = {
        "results_text": None,
        "discussion_text": None,
        "conclusion_text": None,
    }

    for section_name, patterns in SECTION_PATTERNS.items():
        m = _find_first_heading(raw, patterns)
        if not m:
            continue

        start = m.start()
        end = _find_next_section_start(raw, start + 1)
        section_text = raw[start:end].strip() if end else raw[start:].strip()

        if len(section_text) >= 80:
            out[f"{section_name}_text"] = section_text

    return out


def build_reasoning_text(
    abstract: Optional[str],
    full_text: Optional[str],
    results_text: Optional[str],
    discussion_text: Optional[str],
    conclusion_text: Optional[str],
    max_chars: int = 6000,
) -> Optional[str]:
    parts = []

    for part in (
        conclusion_text,
        results_text,
        discussion_text,
        abstract,
        full_text,
    ):
        part_norm = normalize_full_text(part)
        if part_norm and part_norm not in parts:
            parts.append(part_norm)

    if not parts:
        return None

    merged = "\n\n".join(parts).strip()
    if len(merged) > max_chars:
        merged = merged[:max_chars]

    return merged or None
