from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.audits.repository import AuditoriaRepository
from app.audits.service import simular_auditoria
from app.inventory.loader import cargar_productos, cargar_zonas, stock_por_zona
from app.inventory.schemas import SimularAuditoriaRequest, model_to_dict


router = APIRouter()


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

