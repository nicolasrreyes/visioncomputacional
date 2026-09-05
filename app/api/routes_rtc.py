from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.inventory.loader import ROOT_DIR


router = APIRouter(tags=["rtc"])


class RtcOfferRequest(BaseModel):
    sdp: str = Field(max_length=200_000)
    zona_id: str = Field(max_length=50)


class RtcOfferResponse(BaseModel):
    sdp: str
    type: str


@router.get("/rtc")
def vista_rtc() -> FileResponse:
    """Pagina del reproductor de video en vivo (camera -> deteccion -> overlay).

    Se sirve desde el backend para que getUserMedia tenga contexto seguro
    (localhost/HTTPS) y el signaling sea same-origin.
    """
    return FileResponse(
        ROOT_DIR / "dashboard" / "rtc_player.html",
        media_type="text/html",
        headers={"Permissions-Policy": "camera=(self), microphone=()"},
    )


@router.post("/rtc/offer", response_model=RtcOfferResponse)
async def rtc_offer(request: RtcOfferRequest) -> RtcOfferResponse:
    try:
        import aiortc  # noqa: F401

        from app.rtc.webrtc import manejar_offer
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="RTC no disponible: instalá aiortc (pip install aiortc)",
        ) from exc
    try:
        sdp = await manejar_offer(request.sdp, request.zona_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Error en signaling RTC: {exc}") from exc
    return RtcOfferResponse(sdp=sdp, type="answer")