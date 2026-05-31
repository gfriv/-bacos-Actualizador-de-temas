from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.models import DocumentSection, Project


class ClaimType(str, enum.Enum):
    scientific = "scientific"
    legal = "legal"
    curricular = "curricular"
    bibliographic = "bibliographic"
    didactic = "didactic"


@dataclass(frozen=True)
class DocumentClaim:
    id: str
    section_id: int | None
    section_title: str
    text: str
    claim_type: ClaimType
    review_priority: str
    trigger_terms: tuple[str, ...]
    search_terms: tuple[str, ...]
    needs_official_source: bool = False
    needs_recent_source: bool = False


@dataclass(frozen=True)
class SectionProfile:
    section_id: int | None
    title: str
    section_type: str
    key_terms: tuple[str, ...]
    risk_flags: tuple[str, ...]


LEGAL_TERMS = (
    "lomloe",
    "lomce",
    "loe",
    "logse",
    "real decreto",
    "decreto",
    "orden",
    "ley organica",
    "ley organica",
    "boe",
    "doe",
    "convocatoria",
)
CURRICULAR_TERMS = (
    "competencia",
    "criterio",
    "saberes basicos",
    "saber basico",
    "curriculo",
    "curricular",
    "evaluacion",
)
SCIENTIFIC_TERMS = (
    "estudios recientes",
    "investigaciones recientes",
    "evidencia",
    "modelo",
    "teoria",
    "aprendizaje",
    "investigacion",
    "neurociencia",
)
BIBLIO_TERMS = ("bibliografia", "autor", "doi", "manual", "referencia", "cita", "segun")
DIDACTIC_TERMS = ("actividad", "metodologia", "situacion de aprendizaje", "evaluacion", "rubrica")
CURRENTNESS_TERMS = ("actualmente", "hoy en dia", "reciente", "vigente", "ultimas")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")
WORD_PATTERN = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_-]{3,}\b")


def extract_claims(project: Project, sections: list[DocumentSection], limit_per_section: int = 6) -> list[DocumentClaim]:
    claims: list[DocumentClaim] = []
    for section in sections:
        section_claims: list[DocumentClaim] = []
        for index, sentence in enumerate(_sentences(section.content)):
            claim_type = _classify_claim(sentence)
            if claim_type is None:
                continue
            normalized = _normalize(sentence)
            trigger_terms = _trigger_terms(normalized, claim_type)
            priority = _priority(normalized, claim_type)
            section_claims.append(
                DocumentClaim(
                    id=f"s{section.id or section.order_index}-{index}-{claim_type.value}",
                    section_id=section.id,
                    section_title=section.title,
                    text=sentence.strip(),
                    claim_type=claim_type,
                    review_priority=priority,
                    trigger_terms=trigger_terms,
                    search_terms=_search_terms(project, section, sentence, claim_type),
                    needs_official_source=claim_type in {ClaimType.legal, ClaimType.curricular},
                    needs_recent_source=_needs_recent_source(sentence, claim_type),
                )
            )
        claims.extend(_prioritized(section_claims)[:limit_per_section])
    return _dedupe_claims(claims)


def profile_sections(sections: list[DocumentSection]) -> list[SectionProfile]:
    return [_profile_section(section) for section in sections]


def format_claims_markdown(claims: list[DocumentClaim], limit: int = 12) -> str:
    if not claims:
        return "- No se han detectado afirmaciones revisables."
    return "\n".join(
        (
            f"- **{claim.section_title}** · {claim.claim_type.value} · prioridad {claim.review_priority}: "
            f"{_compact(claim.text, 220)}"
        )
        for claim in claims[:limit]
    )


def _sentences(text: str) -> list[str]:
    candidates = [item.strip(" -\t") for item in SENTENCE_SPLIT.split(text) if item.strip()]
    if not candidates and text.strip():
        return [text.strip()]
    return [candidate for candidate in candidates if len(candidate.split()) >= 5]


def _classify_claim(sentence: str) -> ClaimType | None:
    normalized = _normalize(sentence)
    if YEAR_PATTERN.search(normalized) and _contains(normalized, CURRENTNESS_TERMS):
        return ClaimType.bibliographic
    if _contains(normalized, LEGAL_TERMS):
        return ClaimType.legal
    if _contains(normalized, CURRICULAR_TERMS):
        return ClaimType.curricular
    if _contains(normalized, SCIENTIFIC_TERMS):
        return ClaimType.scientific
    if _contains(normalized, BIBLIO_TERMS):
        return ClaimType.bibliographic
    if _contains(normalized, DIDACTIC_TERMS):
        return ClaimType.didactic
    return None


def _profile_section(section: DocumentSection) -> SectionProfile:
    text = _normalize(f"{section.title} {section.content}")
    if _contains(text, LEGAL_TERMS):
        section_type = "normative"
    elif _contains(text, SCIENTIFIC_TERMS):
        section_type = "scientific"
    elif _contains(text, CURRICULAR_TERMS):
        section_type = "curricular"
    elif _contains(text, DIDACTIC_TERMS):
        section_type = "didactic"
    else:
        section_type = "content"
    flags: list[str] = []
    if "lomce" in text or "logse" in text:
        flags.append("possible_outdated_law")
    if YEAR_PATTERN.search(text) and _contains(text, CURRENTNESS_TERMS):
        flags.append("dated_currentness_claim")
    return SectionProfile(
        section_id=section.id,
        title=section.title,
        section_type=section_type,
        key_terms=tuple(_keywords(text)[:8]),
        risk_flags=tuple(flags),
    )


def _priority(sentence: str, claim_type: ClaimType) -> str:
    current_year = datetime.now(UTC).year
    years = [int(match.group(1)) for match in YEAR_PATTERN.finditer(sentence)]
    if claim_type in {ClaimType.legal, ClaimType.curricular}:
        return "high"
    if any(year < current_year - 8 for year in years) and _contains(sentence, CURRENTNESS_TERMS):
        return "high"
    if claim_type in {ClaimType.scientific, ClaimType.bibliographic}:
        return "medium"
    return "low"


def _trigger_terms(sentence: str, claim_type: ClaimType) -> tuple[str, ...]:
    terms_by_type = {
        ClaimType.legal: LEGAL_TERMS,
        ClaimType.curricular: CURRICULAR_TERMS,
        ClaimType.scientific: SCIENTIFIC_TERMS,
        ClaimType.bibliographic: BIBLIO_TERMS,
        ClaimType.didactic: DIDACTIC_TERMS,
    }
    return tuple(term for term in terms_by_type[claim_type] if term in sentence)


def _search_terms(project: Project, section: DocumentSection, sentence: str, claim_type: ClaimType) -> tuple[str, ...]:
    base = [
        project.area,
        project.educational_level,
        section.title,
        *_keywords(_normalize(sentence))[:6],
    ]
    if claim_type in {ClaimType.legal, ClaimType.curricular}:
        base.append(project.legal_framework)
    if claim_type == ClaimType.scientific:
        base.extend(["revision", "evidencia", str(datetime.now(UTC).year)])
    return tuple(item for item in dict.fromkeys(" ".join(base).split()) if len(item) > 2)[:14]


def _needs_recent_source(sentence: str, claim_type: ClaimType) -> bool:
    normalized = _normalize(sentence)
    return claim_type in {ClaimType.scientific, ClaimType.bibliographic} or _contains(normalized, CURRENTNESS_TERMS)


def _prioritized(claims: list[DocumentClaim]) -> list[DocumentClaim]:
    weight = {"high": 0, "medium": 1, "low": 2}
    return sorted(claims, key=lambda claim: (weight.get(claim.review_priority, 9), claim.claim_type.value))


def _dedupe_claims(claims: list[DocumentClaim]) -> list[DocumentClaim]:
    seen: set[str] = set()
    deduped: list[DocumentClaim] = []
    for claim in claims:
        key = _normalize(claim.text)[:180]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(claim)
    return deduped


def _keywords(text: str) -> list[str]:
    stop = {
        "para",
        "como",
        "este",
        "esta",
        "tema",
        "debe",
        "deben",
        "sobre",
        "desde",
        "entre",
        "segun",
        "actualmente",
    }
    return [word for word in dict.fromkeys(WORD_PATTERN.findall(text.lower())) if word not in stop]


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _normalize(text: str) -> str:
    replacements = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    return " ".join(text.translate(replacements).lower().split())


def _compact(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else f"{clean[:limit]}..."
