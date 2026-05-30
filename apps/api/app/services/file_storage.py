from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import FileBlob


def uses_database_storage() -> bool:
    return settings.storage_backend.lower() in {"db", "database", "postgres", "postgresql"}


def save_managed_file(
    db: Session,
    content: bytes,
    *,
    root_dir: str,
    filename: str,
    content_type: str,
    namespace: str,
) -> str:
    safe_filename = Path(filename).name or "archivo"
    suffix = Path(safe_filename).suffix
    if uses_database_storage():
        key = f"{namespace}/{uuid4().hex}{suffix}"
        db.add(
            FileBlob(
                storage_key=key,
                filename=safe_filename,
                content_type=content_type,
                data=content,
            )
        )
        db.flush()
        return f"db://{key}"

    root = Path(root_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"{uuid4().hex}{suffix}"
    target.write_bytes(content)
    return str(target)


def managed_file_response(
    db: Session,
    stored_path: str,
    allowed_root: str,
    download_name: str,
    media_type: str,
) -> Response | FileResponse:
    safe_download_name = safe_download_filename(download_name)
    if stored_path.startswith("db://"):
        key = stored_path.removeprefix("db://")
        blob = db.scalar(select(FileBlob).where(FileBlob.storage_key == key))
        if blob is None:
            raise HTTPException(status_code=404, detail="Archivo no encontrado.")
        return Response(
            content=blob.data,
            media_type=media_type or blob.content_type,
            headers={"Content-Disposition": f'attachment; filename="{safe_download_name}"'},
        )

    root = Path(allowed_root).resolve()
    resolved = Path(stored_path).resolve()
    if not resolved.is_relative_to(root):
        raise HTTPException(status_code=403, detail="Archivo fuera del almacén permitido.")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(resolved, media_type=media_type, filename=safe_download_name)


def safe_download_filename(download_name: str) -> str:
    safe_name = Path(download_name).name.replace('"', "").replace("\r", "").replace("\n", "")
    return safe_name or "descarga"
