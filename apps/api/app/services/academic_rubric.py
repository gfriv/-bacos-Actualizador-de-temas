from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.models import DocumentSection, Project
from app.research.schemas import SearchResult
from app.research.source_policy import assess_evidence


@dataclass(frozen=True)
class RubricFinding:
    code: str
    severity: str
    section_id: int | None
    section_title: str
    message: str
    recommendation: str


@dataclass(frozen=True)
class AcademicRubricResult:
    score: int
    findings: tuple[RubricFinding, ...]
    official_evidence_count: int
    academic_evidence_count: int
    generic_evidence_count: int

    @property
    def high_risk_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == "high")


STALE_LEGAL_MARKERS = ("logse", "loe ", "lomce", "ley orgánica 2/2006", "ley organica 2/2006")
UNVERIFIED_LANGUAGE = (
    "actualmente",
    "estudios recientes",
    "nuevas investigaciones",
    "últimas investigaciones",
    "ultimas investigaciones",
    "hoy en día",
    "hoy en dia",
)
CURRICULAR_TERMS = ("competencia", "criterio", "saber", "currículo", "curriculo", "evaluación", "evaluacion")
SCIENTIFIC_TERMS = ("evidencia", "investigación", "investigacion", "estudio", "modelo", "teoría", "teoria")
YEAR_PATTERN = re.compile(r"\b(19\d{2}|20\d{2})\b")


def evaluate_academic_rubric(
    project: Project,
    sections: list[DocumentSection],
    evidence: list[SearchResult],
) -> AcademicRubricResult:
    current_year = datetime.now(UTC).year
    findings: list[RubricFinding] = []
    normalized_project = _normalize(
        f"{project.area} {project.educational_level} {project.legal_framework} {project.bibliography_notes or ''}"
    )

    if not sections:
        findings.append(
            RubricFinding(
                code="no_sections",
                severity="high",
                section_id=None,
                section_title="Documento",
                message="No hay secciones analizables.",
                recommendation="Revisar la extracción del documento antes de generar informes.",
            )
        )

    if not (project.bibliography_notes or "").strip():
        findings.append(
            RubricFinding(
                code="missing_bibliography",
                severity="medium",
                section_id=None,
                section_title="Proyecto",
                message="No se ha indicado bibliografía base.",
                recommendation="Añadir bibliografía base o marcar expresamente que no existe.",
            )
        )

    if "oposicion" in normalized_project or "oposiciones" in normalized_project:
        if not any(marker in normalized_project for marker in ("convocatoria", "276/2007", "decreto", "orden")):
            findings.append(
                RubricFinding(
                    code="opposition_framework_incomplete",
                    severity="medium",
                    section_id=None,
                    section_title="Marco de oposiciones",
                    message="El proyecto parece orientado a oposiciones, pero no detalla convocatoria o norma aplicable.",
                    recommendation="Aportar convocatoria, cuerpo, especialidad y comunidad autónoma antes de cerrar el informe curricular.",
                )
            )

    official_count = 0
    academic_count = 0
    generic_count = 0
    for result in evidence:
        assessment = assess_evidence(result)
        if assessment.source_kind == "official":
            official_count += 1
        elif assessment.source_kind in {"academic", "publisher"}:
            academic_count += 1
        elif assessment.source_kind == "generic":
            generic_count += 1

    if _needs_curriculum_context(project, sections) and official_count == 0:
        findings.append(
            RubricFinding(
                code="no_official_curriculum_evidence",
                severity="high",
                section_id=None,
                section_title="Marco curricular",
                message="El tema requiere contraste curricular, pero no hay fuentes oficiales asociadas.",
                recommendation="Recuperar BOE/DOE/convocatoria o solicitar normativa al profesor.",
            )
        )

    for section in sections:
        section_text = _normalize(f"{section.title} {section.content}")
        section_len = len(section.content.split())
        if section_len < 40:
            findings.append(
                RubricFinding(
                    code="short_section",
                    severity="low",
                    section_id=section.id,
                    section_title=section.title,
                    message="La sección es breve para justificar una actualización autónoma.",
                    recommendation="Revisar si debe fusionarse con otra sección o ampliarse antes de generar recursos.",
                )
            )
        if any(marker in section_text for marker in STALE_LEGAL_MARKERS):
            findings.append(
                RubricFinding(
                    code="possible_outdated_law_reference",
                    severity="high",
                    section_id=section.id,
                    section_title=section.title,
                    message="La sección contiene referencias legales potencialmente desactualizadas.",
                    recommendation="Contrastar con LOMLOE, normativa autonómica vigente y convocatoria aplicable.",
                )
            )
        old_years = [
            int(match.group(1))
            for match in YEAR_PATTERN.finditer(section_text)
            if int(match.group(1)) < current_year - 8
        ]
        if old_years and any(term in section_text for term in UNVERIFIED_LANGUAGE):
            findings.append(
                RubricFinding(
                    code="dated_claim_with_current_language",
                    severity="medium",
                    section_id=section.id,
                    section_title=section.title,
                    message="Aparecen años antiguos junto a lenguaje de actualidad.",
                    recommendation="Verificar si la afirmación sigue vigente o marcarla como revisión pendiente.",
                )
            )
        if any(term in section_text for term in SCIENTIFIC_TERMS) and academic_count == 0:
            findings.append(
                RubricFinding(
                    code="scientific_claim_without_academic_evidence",
                    severity="medium",
                    section_id=section.id,
                    section_title=section.title,
                    message="Hay lenguaje científico sin evidencia académica o editorial asociada.",
                    recommendation="Contrastar con bibliografía base o fuentes científicas antes de afirmar actualización.",
                )
            )

    score = max(0, 100 - sum(_penalty(finding.severity) for finding in findings))
    return AcademicRubricResult(
        score=score,
        findings=tuple(findings),
        official_evidence_count=official_count,
        academic_evidence_count=academic_count,
        generic_evidence_count=generic_count,
    )


def format_academic_rubric_markdown(result: AcademicRubricResult) -> str:
    if not result.findings:
        findings_block = "- No se han detectado riesgos académicos automáticos relevantes."
    else:
        findings_block = "\n".join(
            (
                f"- **{finding.section_title}** · {finding.severity.upper()} · "
                f"{finding.message} Recomendación: {finding.recommendation}"
            )
            for finding in result.findings[:12]
        )
    return (
        "## Rúbrica académica automática\n\n"
        f"- Puntuación técnica: **{result.score}/100**.\n"
        f"- Fuentes oficiales: **{result.official_evidence_count}**.\n"
        f"- Fuentes académicas/editoriales: **{result.academic_evidence_count}**.\n"
        f"- Fuentes genéricas: **{result.generic_evidence_count}**.\n\n"
        "## Riesgos detectados\n\n"
        f"{findings_block}\n\n"
        "## Interpretación\n\n"
        "- Esta rúbrica no valida el contenido por sí misma.\n"
        "- Sirve para priorizar la revisión docente y localizar aspectos a verificar.\n"
        "- Una puntuación alta no autoriza consolidación automática."
    )


def select_section_for_code(
    result: AcademicRubricResult,
    sections: list[DocumentSection],
    preferred_codes: set[str],
    fallback_index: int = 0,
) -> DocumentSection:
    section_by_id = {section.id: section for section in sections}
    for finding in result.findings:
        if finding.code in preferred_codes and finding.section_id in section_by_id:
            return section_by_id[finding.section_id]
    return sections[min(fallback_index, len(sections) - 1)]


def _needs_curriculum_context(project: Project, sections: list[DocumentSection]) -> bool:
    text = _normalize(
        " ".join([project.educational_level, project.legal_framework, *[section.content for section in sections]])
    )
    return any(term in text for term in CURRICULAR_TERMS)


def _penalty(severity: str) -> int:
    return {"high": 22, "medium": 12, "low": 5}.get(severity, 8)


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())
