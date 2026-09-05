from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_detection import router
from app.api.routes_rtc import router as router_rtc
from app.config import settings
from app.logging_config import configurar_logging

configurar_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Auditoria Visual de Inventario",
    description="POC IACKATON CDA para inventario por vision computacional.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(router_rtc)

logger.info("App iniciada | CORS: %s | RTC intervalo: %.1fs", settings.cors_origins, settings.rtc_intervalo_seg)

