from app.llm.model_router import ModelRouter


def document_processing_worker(project_id: int) -> dict[str, int | str]:
    return {"worker": "DocumentProcessingWorker", "project_id": project_id}


async def research_worker(project_id: int) -> dict[str, int | str]:
    await ModelRouter().generate_text("Genera informe científico mock.")
    return {"worker": "ResearchWorker", "project_id": project_id}


async def curriculum_worker(project_id: int) -> dict[str, int | str]:
    await ModelRouter().generate_text("Genera informe curricular mock.")
    return {"worker": "CurriculumWorker", "project_id": project_id}


def consolidation_worker(project_id: int) -> dict[str, int | str]:
    return {"worker": "ConsolidationWorker", "project_id": project_id}


async def resource_generation_worker(project_id: int, resource_type: str) -> dict[str, int | str]:
    await ModelRouter().generate_document_resource("Documento consolidado", resource_type)
    return {"worker": "ResourceGenerationWorker", "project_id": project_id, "resource_type": resource_type}
