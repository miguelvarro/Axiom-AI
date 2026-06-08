from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from axiom_ai.app.api.utf8_json import UTF8JSONResponse
from axiom_ai.app.api.routes.health import router as health_router
from axiom_ai.app.api.routes.search import router as search_router
from axiom_ai.app.api.routes.answer import router as answer_router
# from axiom_ai.app.api.routes.papers import router as papers_router


app = FastAPI(
    title="Axiom AI",
    default_response_class=UTF8JSONResponse,
)

# ── CORS ────────────────────────────────────────────────────────────────────
# Permite llamadas desde el frontend (archivo local o cualquier origen en dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # En producción: cambiar a la URL exacta del frontend
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── UTF-8 force ──────────────────────────────────────────────────────────────
class ForceUTF8JSONMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp: Response = await call_next(request)
        ct = resp.headers.get("content-type", "")
        if ct.startswith("application/json") and "charset=" not in ct:
            resp.headers["content-type"] = "application/json; charset=utf-8"
        return resp

app.add_middleware(ForceUTF8JSONMiddleware)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health_router, tags=["health"])
app.include_router(search_router, tags=["search"])
app.include_router(answer_router, tags=["answer"])
# app.include_router(papers_router, tags=["papers"])
