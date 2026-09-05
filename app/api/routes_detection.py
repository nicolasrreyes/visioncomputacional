from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.audits.repository import AuditoriaRepository
from app.audits.service import procesar_imagen, simular_auditoria
from app.config import settings
from app.detection.real_inference import ModeloNoDisponibleError, _DETECTOR_COMPARTIDO
from app.inventory.loader import cargar_productos, cargar_zonas, stock_por_zona
from app.inventory.schemas import (
    Auditoria,
    FuenteAuditoria,
    Producto,
    SimularAuditoriaRequest,
    StockEsperado,
    Zona,
)


router = APIRouter()

MAX_UPLOAD_BYTES = settings.max_upload_mb * 1024 * 1024


@router.get("/health")
def health() -> dict[str, object]:
    modelo_cargado = False
    if _DETECTOR_COMPARTIDO is not None and _DETECTOR_COMPARTIDO._model is not None:
        modelo_cargado = True
    zonas = len(cargar_zonas())
    auditorias = len(AuditoriaRepository().listar())
    return {
        "status": "ok",
        "modelo_cargado": modelo_cargado,
        "zonas": zonas,
        "auditorias_guardadas": auditorias,
        "disco_libre_bytes": shutil.disk_usage(".").free,
    }


@router.get("/zonas", response_model=list[Zona])
def zonas() -> list[Zona]:
    return list(cargar_zonas().values())


@router.get("/productos", response_model=list[Producto])
def productos() -> list[Producto]:
    return list(cargar_productos().values())


@router.get("/stock/{zona_id}", response_model=list[StockEsperado])
def stock(zona_id: str) -> list[StockEsperado]:
    if zona_id not in cargar_zonas():
        raise HTTPException(status_code=404, detail=f"Zona desconocida: {zona_id}")
    return stock_por_zona(zona_id)


@router.post("/auditorias/simular", response_model=Auditoria)
def simular(request: SimularAuditoriaRequest) -> Auditoria:
    try:
        return simular_auditoria(
            zona_id=request.zona_id,
            fixture=request.fixture,
            fuente=request.fuente,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auditorias/imagen", response_model=Auditoria)
def auditoria_desde_imagen(
    zona_id: str = Form(...),
    fuente: FuenteAuditoria = Form(FuenteAuditoria.IMAGEN),
    archivo: UploadFile = File(...),
) -> Auditoria:
    if zona_id not in cargar_zonas():
        raise HTTPException(status_code=400, detail=f"Zona desconocida: {zona_id}")
    if not archivo.content_type or not archivo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")
    sufijo = Path(archivo.filename or "").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as temporal:
        total_leido = 0
        with archivo.file as entrada:
            while chunk := entrada.read(1024 * 512):
                total_leido += len(chunk)
                if total_leido > MAX_UPLOAD_BYTES:
                    temporal.close()
                    Path(temporal.name).unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Archivo demasiado grande (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
                    )
                temporal.write(chunk)
        ruta_temporal = Path(temporal.name)
    try:
        auditoria = procesar_imagen(
            zona_id=zona_id,
            ruta_imagen=ruta_temporal,
            fuente=fuente,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ModeloNoDisponibleError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        ruta_temporal.unlink(missing_ok=True)
    return auditoria


@router.get("/auditorias", response_model=list[Auditoria])
def listar_auditorias(zona_id: str | None = None) -> list[Auditoria]:
    repo = AuditoriaRepository()
    return repo.listar(zona_id=zona_id)


@router.get("/auditorias/{auditoria_id}", response_model=Auditoria)
def obtener_auditoria(auditoria_id: str) -> Auditoria:
    repo = AuditoriaRepository()
    try:
        return repo.cargar(auditoria_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

