from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.brand import ABACOS_EMAIL, ABACOS_LEGAL_NAME


@dataclass(frozen=True)
class QualityIssue:
    code: str
    severity: str
    message: str
    blocking: bool = True


@dataclass(frozen=True)
class QualityGateResult:
    ok: bool
    score: int
    issues: tuple[QualityIssue, ...]
    criteria: dict[str, int | bool | str] | None = None


SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAIza[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:api[_-]?key|authorization|bearer)\s*[:=]\s*[A-Za-z0-9_.-]{12,}", re.IGNORECASE),
)
INTERNAL_PATH_PATTERN = re.compile(
    r"(?:[A-Za-z]:\\|/app/|/home/|/tmp/|apps[\\/]+api[\\/]+storage|"
    r"storage[\\/]+uploads|storage[\\/]+generated|db://|file_path|docx_path)",
    re.IGNORECASE,
)
PLACEHOLDER_PATTERNS = (
    re.compile(r"\[object Object\]"),
    re.compile(r"\bundefined\b|\bnull\b|null\.", re.IGNORECASE),
    # TODO must remain case-sensitive: "todo" is a common Spanish word in academic reports.
    re.compile(r"\bTODO\b"),
    re.compile(r"\bCHANGE_ME\b", re.IGNORECASE),
    re.compile(r"\bdev-secret\b", re.IGNORECASE),
)
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def evaluate_export_quality(
    content: str,
    *,
    artifact_type: str,
    require_brand_footer: bool = True,
    require_ai_notice: bool = True,
    require_date: bool = True,
    require_sources: bool = False,
    min_length: int = 120,
) -> QualityGateResult:
    issues: list[QualityIssue] = []
    text = content or ""

    if len(text.strip()) < min_length:
        issues.append(
            QualityIssue(
                code="too_short",
                severity="high",
                message=f"El artefacto {artifact_type} no tiene contenido suficiente para exportarse.",
            )
        )

    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        issues.append(
            QualityIssue(
                code="secret_like_value",
                severity="critical",
                message="El contenido parece incluir una clave, token o cabecera sensible.",
            )
        )

    if INTERNAL_PATH_PATTERN.search(text):
        issues.append(
            QualityIssue(
                code="internal_path",
                severity="critical",
                message="El contenido incluye rutas internas o nombres técnicos de almacenamiento.",
            )
        )

    if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
        issues.append(
            QualityIssue(
                code="placeholder",
                severity="medium",
                message="El contenido incluye placeholders o valores técnicos sin resolver.",
            )
        )

    if require_brand_footer and (ABACOS_LEGAL_NAME not in text or ABACOS_EMAIL not in text):
        issues.append(
            QualityIssue(
                code="missing_brand_footer",
                severity="medium",
                message="Falta el pie corporativo de Ábacos.",
            )
        )

    if require_ai_notice and "asistencia de ia" not in text.lower():
        issues.append(
            QualityIssue(
                code="missing_ai_notice",
                severity="medium",
                message="Falta el aviso de asistencia de IA.",
            )
        )

    if require_date and not DATE_PATTERN.search(text):
        issues.append(
            QualityIssue(
                code="missing_generation_date",
                severity="low",
                message="Falta una fecha de generación trazable.",
                blocking=False,
            )
        )

    if require_sources and "fuente" not in text.lower() and "referencia" not in text.lower():
        issues.append(
            QualityIssue(
                code="missing_sources",
                severity="high",
                message="El informe no incluye fuentes o referencias de contraste.",
            )
        )

    blocking_issues = [issue for issue in issues if issue.blocking]
    score = max(0, 100 - sum(_penalty(issue.severity) for issue in issues))
    return QualityGateResult(ok=not blocking_issues, score=score, issues=tuple(issues), criteria=None)


def evaluate_report_academic_quality(
    content: str,
    *,
    report_type: str,
    evidence_count: int = 0,
    official_evidence_count: int = 0,
    llm_degraded: bool = False,
) -> QualityGateResult:
    base = evaluate_export_quality(
        content,
        artifact_type=report_type,
        require_sources=report_type in {"scientific_update", "curriculum_mapping", "source_validation"},
    )
    text = content.lower()
    criteria: dict[str, int | bool | str] = {
        "evidence_count": evidence_count,
        "official_evidence_count": official_evidence_count,
        "has_traceability": evidence_count > 0 and ("http" in text or "fuente" in text or "referencia" in text),
        "has_human_verification": "verificaci" in text or "revision docente" in text or "revisión docente" in text,
        "has_localized_change": "seccion" in text or "sección" in text or "fragmento" in text,
        "has_confidence_language": any(term in text for term in ("confirmado", "probable", "requiere verificacion", "requiere verificación")),
        "has_academic_rubric": "rúbrica académica" in text or "rubrica academica" in text,
        "has_risk_language": "riesgo" in text or "aspecto a verificar" in text,
        "has_claim_extraction": "claim" in text or "afirmacion" in text or "afirmación" in text,
        "has_source_ranking": "ranking" in text or "puntuad" in text or "score" in text,
        "llm_degraded": llm_degraded,
    }
    issues = list(base.issues)
    if not criteria["has_traceability"]:
        issues.append(QualityIssue("academic_traceability", "high", "El informe no muestra trazabilidad suficiente."))
    if report_type == "curriculum_mapping" and official_evidence_count == 0:
        issues.append(QualityIssue("missing_official_evidence", "high", "El informe curricular no tiene fuente oficial."))
    if not criteria["has_human_verification"]:
        issues.append(QualityIssue("missing_human_validation", "medium", "Falta recordatorio de validacion docente."))
    if not criteria["has_confidence_language"]:
        issues.append(QualityIssue("missing_confidence_taxonomy", "medium", "No distingue confirmado, probable y a verificar."))
    if not criteria["has_academic_rubric"]:
        issues.append(QualityIssue("missing_academic_rubric", "medium", "No incluye rúbrica académica o criterios de riesgo."))
    if not criteria["has_risk_language"]:
        issues.append(QualityIssue("missing_risk_language", "low", "No explicita riesgos o aspectos a verificar.", blocking=False))
    if not criteria["has_claim_extraction"]:
        issues.append(
            QualityIssue(
                "missing_claim_extraction",
                "low",
                "No explicita claims o afirmaciones revisables detectadas.",
                blocking=False,
            )
        )
    if report_type in {"scientific_update", "curriculum_mapping", "source_validation"} and not criteria["has_source_ranking"]:
        issues.append(
            QualityIssue(
                "missing_source_ranking",
                "low",
                "No muestra puntuacion o ranking de fuentes.",
                blocking=False,
            )
        )
    if llm_degraded:
        issues.append(
            QualityIssue(
                "llm_degraded",
                "low",
                "El informe se genero sin sintesis LLM completa.",
                blocking=False,
            )
        )
    score = max(0, 100 - sum(_penalty(issue.severity) for issue in issues))
    blocking_issues = [issue for issue in issues if issue.blocking]
    return QualityGateResult(ok=not blocking_issues, score=score, issues=tuple(issues), criteria=criteria)


def assert_export_quality(content: str, **kwargs: object) -> QualityGateResult:
    result = evaluate_export_quality(content, **kwargs)
    if not result.ok:
        reasons = "; ".join(issue.message for issue in result.issues if issue.blocking)
        raise ValueError(f"El artefacto no supera la puerta de calidad: {reasons}")
    return result


def _penalty(severity: str) -> int:
    return {"critical": 45, "high": 30, "medium": 15, "low": 5}.get(severity, 10)
