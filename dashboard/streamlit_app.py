from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from app.audits.repository import AuditoriaRepository
from app.audits.service import simular_auditoria
from app.inventory.loader import FIXTURES_DIR, cargar_zonas
from app.inventory.schemas import FuenteAuditoria, model_to_dict


st.set_page_config(page_title="Auditoria Visual de Inventario", layout="wide")
st.title("Auditoria Visual de Inventario")

zonas = cargar_zonas()
fixtures = sorted(path.name for path in FIXTURES_DIR.glob("detecciones*.json"))

with st.sidebar:
    st.header("Simulacion")
    zona_id = st.selectbox("Zona", options=list(zonas.keys()), format_func=lambda z: zonas[z].nombre)
    fixture = st.selectbox("Fixture de detecciones", options=fixtures)
    ejecutar = st.button("Simular auditoria", type="primary")

repo = AuditoriaRepository()

if ejecutar:
    auditoria = simular_auditoria(zona_id=zona_id, fixture=fixture, fuente=FuenteAuditoria.IMAGEN)
    st.success(f"Auditoria generada: {auditoria.auditoria_id}")

auditorias = repo.listar()
ultima = auditorias[-1] if auditorias else None

if ultima:
    metricas = ultima.metricas
    cols = st.columns(6)
    cols[0].metric("Total esperado", metricas.total_esperado)
    cols[1].metric("Total detectado", metricas.total_detectado)
    cols[2].metric("Discrepancias", metricas.cantidad_discrepancias)
    cols[3].metric("Coincidencia", f"{metricas.porcentaje_coincidencia}%")
    cols[4].metric("Confianza prom.", f"{metricas.confianza_promedio:.2f}")
    cols[5].metric("A revisar", metricas.items_a_revisar)

    st.subheader("Discrepancias")
    st.dataframe([model_to_dict(item) for item in ultima.discrepancias], use_container_width=True)

    st.subheader("Auditorias guardadas")
    st.dataframe(
        [
            {
                "auditoria_id": a.auditoria_id,
                "fecha_hora": a.fecha_hora,
                "zona_id": a.zona_id,
                "coincidencia": a.metricas.porcentaje_coincidencia,
                "discrepancias": a.metricas.cantidad_discrepancias,
            }
            for a in auditorias
        ],
        use_container_width=True,
    )

    seleccion = st.selectbox("Detalle", options=[a.auditoria_id for a in auditorias])
    st.json(model_to_dict(repo.cargar(seleccion)))
else:
    st.info("Todavia no hay auditorias. Ejecuta una simulacion desde la barra lateral.")

with st.expander("Fixtures disponibles"):
    st.code(json.dumps([str(Path("tests/fixtures") / name) for name in fixtures], indent=2), language="json")

