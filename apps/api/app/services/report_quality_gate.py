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
PLACEHOLDER_PATTERN = re.compile(r"(?:\[object Object\]|undefined|null|null\.|TODO|CHANGE_ME|dev-secret)", re.IGNORECASE)
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

    if PLACEHOLDER_PATTERN.search(text):
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
    return QualityGateResult(ok=not blocking_issues, score=score, issues=tuple(issues))


def assert_export_quality(content: str, **kwargs: object) -> QualityGateResult:
    result = evaluate_export_quality(content, **kwargs)
    if not result.ok:
        reasons = "; ".join(issue.message for issue in result.issues if issue.blocking)
        raise ValueError(f"El artefacto no supera la puerta de calidad: {reasons}")
    return result


def _penalty(severity: str) -> int:
    return {"critical": 45, "high": 30, "medium": 15, "low": 5}.get(severity, 10)
