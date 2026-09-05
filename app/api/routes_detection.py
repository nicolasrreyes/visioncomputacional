from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.audits.repository import AuditoriaRepository
from app.audits.service import procesar_imagen, simular_auditoria
from app.detection.real_inference import ModeloNoDisponibleError
from app.inventory.loader import cargar_productos, cargar_zonas, stock_por_zona
from app.inventory.schemas import FuenteAuditoria, SimularAuditoriaRequest, model_to_dict


router = APIRouter()

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/zonas")
def zonas() -> list[dict]:
    return [model_to_dict(zona) for zona in cargar_zonas().values()]


@router.get("/productos")
def productos() -> list[dict]:
    return [model_to_dict(producto) for producto in cargar_productos().values()]


@router.get("/stock/{zona_id}")
def stock(zona_id: str) -> list[dict]:
    if zona_id not in cargar_zonas():
        raise HTTPException(status_code=404, detail=f"Zona desconocida: {zona_id}")
    return [model_to_dict(item) for item in stock_por_zona(zona_id)]


@router.post("/auditorias/simular")
def simular(request: SimularAuditoriaRequest) -> dict:
    try:
        auditoria = simular_auditoria(
            zona_id=request.zona_id,
            fixture=request.fixture,
            fuente=request.fuente,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return model_to_dict(auditoria)


@router.post("/auditorias/imagen")
def auditoria_desde_imagen(
    zona_id: str = Form(...),
    fuente: FuenteAuditoria = Form(FuenteAuditoria.IMAGEN),
    archivo: UploadFile = File(...),
) -> dict:
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
    return model_to_dict(auditoria)


@router.get("/auditorias")
def listar_auditorias(zona_id: str | None = None) -> list[dict]:
    repo = AuditoriaRepository()
    return [model_to_dict(auditoria) for auditoria in repo.listar(zona_id=zona_id)]


@router.get("/auditorias/{auditoria_id}")
def obtener_auditoria(auditoria_id: str) -> dict:
    repo = AuditoriaRepository()
    try:
        return model_to_dict(repo.cargar(auditoria_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

