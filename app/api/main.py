from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_detection import router
from app.api.routes_rtc import router as router_rtc


app = FastAPI(
    title="Auditoria Visual de Inventario",
    description="POC IACKATON CDA para inventario por vision computacional.",
    version="0.1.0",
)
app.include_router(router)
app.include_router(router_rtc)

