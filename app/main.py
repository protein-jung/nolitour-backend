import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.auth import router as auth_router
from app.api.routes.playgrounds import router as playgrounds_router
from app.api.routes.rankings import router as rankings_router
from app.core.config import settings
from app.core.slack import send_slack_alert

logger = logging.getLogger(__name__)

app = FastAPI(title="Nolitour API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.media_root).mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url_prefix, StaticFiles(directory=settings.media_root), name="media")

app.include_router(playgrounds_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(rankings_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    last_line = traceback.format_exception_only(type(exc), exc)[-1].strip()
    send_slack_alert(
        f":rotating_light: *Nolitour API Exception*\n"
        f"`{request.method} {request.url.path}`\n"
        f"```{last_line}```"
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/health")
def health():
    return {"status": "ok"}
