from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Literal, Any

from ai_consensus_clone.core.domain.paper import Paper
from ai_consensus_clone.core.reasoning.llm_client import LLMClient
from ai_consensus_clone.core.config.settings import Settings


StanceLabel = Literal["support", "contradict", "neutral"]
StrengthLabel = Literal["weak", "moderate", "strong"]

# Cache en memoria: (paper_id, question) -> PaperStance
# Evita recalcular stance para el mismo paper+pregunta en la misma sesión
_STANCE_CACHE: dict[tuple[str, str], "PaperStance"] = {}


@dataclass
class PaperStance:
    paper_id: str
    stance: StanceLabel
    strength: StrengthLabel
    evidence: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _truncate_text(text: str, max_chars: int = 2000) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _safe_json_load(raw: str) -> dict[str, Any]:
    if not raw:
        return {}

    raw = raw.strip()

    # Intento 1: JSON directo
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Intento 2: extraer entre { }
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw[start:end + 1])
    except Exception:
        pass

    # Intento 3: el modelo omitió las llaves externas
    # Caso: '\n  "stance": "support",\n  "strength": "weak",...'
    try:
        candidate = "{" + raw + "}"
        return json.loads(candidate)
    except Exception:
        pass

    # Intento 4: regex campo a campo
    try:
        stance_match = re.search(r'"stance"\s*:\s*"([^"]+)"', raw)
        strength_match = re.search(r'"strength"\s*:\s*"([^"]+)"', raw)
        evidence_match = re.search(r'"evidence"\s*:\s*"([^"]*)"', raw)
        rationale_match = re.search(r'"rationale"\s*:\s*"([^"]*)"', raw)

        if stance_match:
            return {
                "stance": stance_match.group(1),
                "strength": strength_match.group(1) if strength_match else "weak",
                "evidence": evidence_match.group(1) if evidence_match else "",
                "rationale": rationale_match.group(1) if rationale_match else "",
            }
    except Exception:
        pass

    return {}


def _normalize_stance(value: str) -> StanceLabel:
    value = (value or "").strip().lower()

    SUPPORT_ALIASES = {
        "support", "supports", "positive", "yes", "agree",
        "confirms", "confirm", "consistent", "favor", "favors",
        "beneficial", "effective", "true", "affirm", "endorses",
    }
    CONTRADICT_ALIASES = {
        "contradict", "contradicts", "negative", "no", "disagree",
        "refutes", "refute", "against", "oppose", "opposes",
        "ineffective", "false", "deny", "denies", "disprove",
    }

    if value in SUPPORT_ALIASES:
        return "support"
    if value in CONTRADICT_ALIASES:
        return "contradict"
    return "neutral"


def _normalize_strength(value: str) -> StrengthLabel:
    value = (value or "").strip().lower()

    STRONG_ALIASES = {
        "strong", "high", "significant", "substantial", "robust",
        "clear", "definitive", "compelling", "conclusive", "convincing",
    }
    MODERATE_ALIASES = {
        "moderate", "medium", "partial", "mixed", "some",
        "limited", "suggestive", "possible", "probable",
    }

    if value in STRONG_ALIASES:
        return "strong"
    if value in MODERATE_ALIASES:
        return "moderate"
    return "weak"


def _heuristic_stance(text: str, question: str) -> tuple[str, str]:
    """Clasificador heurístico de emergencia cuando el LLM falla."""
    t = text.lower()
    q = question.lower()

    POSITIVE_CUES = (
        "significantly increased", "significantly improved", "greater increase",
        "higher", "improved", "increase", "enhanced", "benefit", "gain",
        "augmented", "demonstrates", "confirms", "supports",
    )
    NEGATIVE_CUES = (
        "no significant", "no effect", "did not improve", "did not increase",
        "no difference", "not associated", "contradict", "refutes",
        "equivocal", "inconsistent", "limited", "not supported",
    )
    SAFETY_NEGATIVE_CUES = (
        "safe", "no adverse", "no kidney", "no renal damage", "well tolerated",
        "no harm", "no significant side effects",
    )

    pos = sum(1 for c in POSITIVE_CUES if c in t)
    neg = sum(1 for c in NEGATIVE_CUES if c in t)

    is_safety_question = any(w in q for w in ("safe", "unsafe", "damage", "harm", "risk", "cause"))
    safety_neg = sum(1 for c in SAFETY_NEGATIVE_CUES if c in t)

    if is_safety_question and safety_neg >= 1:
        return "contradict", "moderate" if safety_neg >= 2 else "weak"

    if pos > neg and pos >= 1:
        strength = "strong" if pos >= 3 else "moderate" if pos >= 2 else "weak"
        return "support", strength
    if neg > pos and neg >= 1:
        strength = "strong" if neg >= 3 else "moderate" if neg >= 2 else "weak"
        return "contradict", strength
    if pos >= 1 and neg >= 1:
        return "neutral", "weak"

    return "neutral", "weak"


def _build_stance_client(base_client: LLMClient) -> LLMClient:
    """
    Devuelve un LLMClient con el modelo de stance (más pequeño y rápido).
    Si LLM_STANCE_MODEL está definido en settings lo usa; si no, usa 7b por defecto.
    """
    stance_settings = Settings()
    # Usa LLM_STANCE_MODEL si existe, si no fuerza 7b
    stance_model = getattr(stance_settings, "llm_stance_model", None)
    if not stance_model:
        # Derivar modelo 7b a partir del modelo principal
        base_model = stance_settings.llm_model or ""
        if "32b" in base_model:
            stance_model = base_model.replace("32b", "7b")
        elif "70b" in base_model:
            stance_model = base_model.replace("70b", "7b")
        else:
            stance_model = base_model  # ya es pequeño, usar tal cual
    stance_settings.llm_model = stance_model
    return LLMClient(settings=stance_settings)


def classify_paper_stance(
    llm_client: LLMClient,
    question: str,
    paper: Paper,
    prompt_template: str,
    max_chars: int = 2000,
) -> PaperStance:
    paper_id = getattr(paper, "paper_id", "")

    # Cache lookup
    cache_key = (paper_id, question[:120])
    if cache_key in _STANCE_CACHE:
        print(f"[STANCE CACHE HIT] paper_id={paper_id}")
        return _STANCE_CACHE[cache_key]

    source_text = (
        getattr(paper, "full_text", None)
        or getattr(paper, "abstract", None)
        or ""
    ).strip()

    if not source_text:
        result = PaperStance(
            paper_id=paper_id,
            stance="neutral",
            strength="weak",
            evidence="",
            rationale="No text available to classify stance.",
        )
        _STANCE_CACHE[cache_key] = result
        return result

    source_text = _truncate_text(source_text, max_chars=max_chars)

    # Escapar llaves literales del template para que .format() no las interprete
    safe_template = prompt_template.replace("{", "{{").replace("}", "}}")
    safe_template = (
        safe_template
        .replace("{{question}}", "{question}")
        .replace("{{title}}", "{title}")
        .replace("{{text}}", "{text}")
    )

    prompt = safe_template.format(
        question=(question or "").strip(),
        title=(getattr(paper, "title", None) or "").strip(),
        text=source_text,
    )
    prompt += (
        "\n\nCRITICAL: The 'stance' field MUST be exactly one of these three words: "
        "support, contradict, neutral. No other words allowed. "
        "The 'strength' field MUST be exactly one of: weak, moderate, strong."
    )

    raw_output = llm_client.generate(prompt)
    print(f"[STANCE RAW] paper_id={paper_id} raw={repr(raw_output[:200])}")
    parsed = _safe_json_load(raw_output)

    if not parsed or "stance" not in parsed:
        heuristic_stance, heuristic_strength = _heuristic_stance(source_text, question)
        result = PaperStance(
            paper_id=paper_id,
            stance=heuristic_stance,
            strength=heuristic_strength,
            evidence="[heuristic fallback]",
            rationale="LLM unavailable; classified via keyword heuristics.",
        )
        _STANCE_CACHE[cache_key] = result
        return result

    stance = _normalize_stance(parsed.get("stance", "neutral"))
    strength = _normalize_strength(parsed.get("strength", "weak"))
    evidence = (parsed.get("evidence") or "").strip()
    rationale = (parsed.get("rationale") or "").strip()

    result = PaperStance(
        paper_id=paper_id,
        stance=stance,
        strength=strength,
        evidence=evidence,
        rationale=rationale,
    )
    _STANCE_CACHE[cache_key] = result
    return result


def classify_papers_stances(
    llm_client: LLMClient,
    question: str,
    papers: list[Paper],
    prompt_template: str,
    max_chars: int = 3000,
    max_workers: int = 3,
) -> list[PaperStance]:
    """
    Clasifica el stance de una lista de papers en paralelo.
    Usa un modelo más pequeño (7b) para mayor velocidad.
    """
    # Construir cliente con modelo pequeño para stance
    stance_client = _build_stance_client(llm_client)
    print(f"[STANCE] usando modelo: {stance_client.settings.llm_model}")
    print(f"[STANCE] max_workers={max_workers}, max_chars={max_chars}")

    def _classify_one(indexed_paper: tuple[int, Paper]) -> tuple[int, PaperStance]:
        idx, paper = indexed_paper
        try:
            result = classify_paper_stance(
                llm_client=stance_client,
                question=question,
                paper=paper,
                prompt_template=prompt_template,
                max_chars=max_chars,
            )
        except Exception as exc:
            result = PaperStance(
                paper_id=getattr(paper, "paper_id", ""),
                stance="neutral",
                strength="weak",
                evidence="",
                rationale=f"Stance classification failed: {exc}",
            )
        return idx, result

    indexed_papers = list(enumerate(papers))
    results: list[PaperStance | None] = [None] * len(papers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_classify_one, ip): ip for ip in indexed_papers}
        for future in as_completed(futures):
            idx, stance = future.result()
            results[idx] = stance

    return [r for r in results if r is not None]
