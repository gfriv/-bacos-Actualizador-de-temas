from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.core.rate_limit import is_rate_limited

app = FastAPI(title="Ábacos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Abacos-AI-Config", "X-Abacos-AI-Session"],
)


@app.middleware("http")
async def security_and_abuse_middleware(request: Request, call_next):
    if is_rate_limited(request):
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Espera un momento antes de continuar."},
        )
    response = await call_next(request)
    if settings.security_headers_enabled:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
    return response


app.include_router(router, prefix="/api")
