from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EstadoOperativo(str, Enum):
    OK = "OK"
    FALTANTE = "faltante"
    SOBRANTE = "sobrante"
    REVISAR = "revisar"


class FuenteAuditoria(str, Enum):
    IMAGEN = "imagen"
    VIDEO = "video"
    CAMARA_VIVA = "camara_viva"


class Producto(BaseModel):
    id: str
    nombre: str
    descripcion: str = ""
    prompts_deteccion: list[str] = Field(default_factory=list)
    umbral_confianza: float = Field(ge=0, le=1)
    color_bbox: str | None = None


class Zona(BaseModel):
    id: str
    nombre: str
    descripcion: str = ""
    productos_permitidos: list[str] = Field(default_factory=list)


class StockEsperado(BaseModel):
    zona_id: str
    producto_id: str
    cantidad_esperada: int = Field(ge=0)
    ubicacion_exacta: str = ""
    fecha_ultimo_recuento: str = ""
    notas: str = ""


class Deteccion(BaseModel):
    producto_id: str
    label: str
    confianza: float = Field(ge=0, le=1)
    bbox: list[float] = Field(min_length=4, max_length=4)
    estado_visual: str = "desconocido"


class ResultadoConteo(BaseModel):
    conteos: dict[str, int]
    detecciones_validas: list[Deteccion]
    detecciones_a_revisar: list[Deteccion]


class Discrepancia(BaseModel):
    producto_id: str
    cantidad_esperada: int
    cantidad_detectada: int
    diferencia: int
    estado_operativo: EstadoOperativo
    confianza_promedio: float = 0
    requiere_revision: bool = False


class MetricasAuditoria(BaseModel):
    total_esperado: int
    total_detectado: int
    diferencia_total: int
    cantidad_discrepancias: int
    porcentaje_coincidencia: float
    confianza_promedio: float
    items_a_revisar: int
    tiempo_ahorrado_minutos: float


class Auditoria(BaseModel):
    auditoria_id: str
    fecha_hora: str
    zona_id: str
    fuente: FuenteAuditoria
    archivo_original: str | None = None
    evidencia_path: str | None = None
    duracion_proceso_segundos: float = 0
    detecciones: list[Deteccion]
    conteos: dict[str, int]
    discrepancias: list[Discrepancia]
    metricas: MetricasAuditoria

    @classmethod
    def nueva(
        cls,
        auditoria_id: str,
        zona_id: str,
        fuente: FuenteAuditoria,
        duracion_proceso_segundos: float,
        detecciones: list[Deteccion],
        conteos: dict[str, int],
        discrepancias: list[Discrepancia],
        metricas: MetricasAuditoria,
        archivo_original: str | None = None,
        evidencia_path: str | None = None,
    ) -> "Auditoria":
        return cls(
            auditoria_id=auditoria_id,
            fecha_hora=datetime.now(timezone.utc).isoformat(),
            zona_id=zona_id,
            fuente=fuente,
            archivo_original=archivo_original,
            evidencia_path=evidencia_path,
            duracion_proceso_segundos=duracion_proceso_segundos,
            detecciones=detecciones,
            conteos=conteos,
            discrepancias=discrepancias,
            metricas=metricas,
        )


class SimularAuditoriaRequest(BaseModel):
    zona_id: str
    fixture: str = "detecciones_estanteria_a.json"
    fuente: FuenteAuditoria = FuenteAuditoria.IMAGEN


def model_to_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")

