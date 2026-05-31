import base64
import json

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.llm.schemas import AIProviderConfig
from app.llm.session_store import get_ai_session

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación requerida.")
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no válido.")
    try:
        user_id = int(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no vÃ¡lido.") from exc
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado.")
    return user


def get_ai_provider_config(
    encoded_config: str | None = Header(default=None, alias="X-Abacos-AI-Config"),
    ai_session_id: str | None = Header(default=None, alias="X-Abacos-AI-Session"),
) -> AIProviderConfig | None:
    if ai_session_id:
        config = get_ai_session(ai_session_id)
        if config is None:
            raise HTTPException(status_code=400, detail="Sesion de IA no valida o caducada.")
        return config
    if not encoded_config:
        return None
    try:
        padded = encoded_config + "=" * (-len(encoded_config) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        return AIProviderConfig.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ConfiguraciÃ³n de IA no vÃ¡lida.") from exc
