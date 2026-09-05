from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from app.audits.repository import AuditoriaRepository
from app.audits.service import procesar_imagen, simular_auditoria
from app.inventory.loader import FIXTURES_DIR, ROOT_DIR, cargar_zonas
from app.inventory.schemas import FuenteAuditoria, model_to_dict


st.set_page_config(page_title="Auditoria Visual de Inventario", layout="wide")
st.title("Auditoria Visual de Inventario")


@st.cache_data(show_spinner=False)
def _cargar_zonas_cached() -> dict:
    return cargar_zonas()


@st.cache_data(show_spinner=False)
def _listar_fixtures() -> list[str]:
    return sorted(path.name for path in FIXTURES_DIR.glob("detecciones*.json"))


@st.cache_data(ttl=10, show_spinner=False)
def _listar_auditorias() -> list[dict]:
    return [model_to_dict(a) for a in AuditoriaRepository().listar()]


@st.cache_data(show_spinner=False)
def _cargar_auditoria(auditoria_id: str) -> dict:
    return model_to_dict(AuditoriaRepository().cargar(auditoria_id))


zonas = _cargar_zonas_cached()
fixtures = _listar_fixtures()
api_base = os.environ.get("API_BASE", "http://127.0.0.1:8000")

with st.sidebar:
    st.header("Simulacion")
    zona_sim = st.selectbox(
        "Zona (simulacion)",
        options=list(zonas.keys()),
        format_func=lambda z: zonas[z].nombre,
    )
    fixture = st.selectbox("Fixture de detecciones", options=fixtures)
    ejecutar = st.button("Simular auditoria", type="primary")

with st.sidebar:
    st.divider()
    st.header("Deteccion real")
    zona_img = st.selectbox(
        "Zona (imagen)",
        options=list(zonas.keys()),
        format_func=lambda z: zonas[z].nombre,
    )
    archivo_subido = st.file_uploader("Imagen del estante", type=["jpg", "jpeg", "png"])
    procesar = st.button("Procesar imagen", type="secondary")

with st.sidebar:
    st.divider()
    st.header("Video en vivo (RTC)")
    zona_viva = st.selectbox(
        "Zona (video)",
        options=list(zonas.keys()),
        format_func=lambda z: zonas[z].nombre,
    )
    mostrar_vivo = st.toggle(
        "Mostrar vista de camara",
        value=st.session_state.get("mostrar_vivo", False),
        key="mostrar_vivo",
        help="Requiere el backend corriendo (uvicorn) y permiso de camara en el navegador.",
    )

with st.sidebar:
    st.divider()
    if st.button("Recargar auditorias", help="Limpia la cache y relee outputs/auditorias"):
        st.cache_data.clear()
        st.rerun()

repo = AuditoriaRepository()

if ejecutar:
    with st.spinner("Simulando auditoria..."):
        auditoria = simular_auditoria(zona_id=zona_sim, fixture=fixture, fuente=FuenteAuditoria.IMAGEN)
    st.success(f"Auditoria generada: {auditoria.auditoria_id}")

if procesar:
    if archivo_subido is None:
        st.warning("Selecciona una imagen para procesar.")
    else:
        destino = Path("outputs/tmp_upload") / archivo_subido.name
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(archivo_subido.getvalue())
        try:
            with st.spinner("Procesando imagen (inferencia con el modelo, puede tardar)..."):
                auditoria = procesar_imagen(
                    zona_id=zona_img,
                    ruta_imagen=destino,
                    fuente=FuenteAuditoria.IMAGEN,
                )
            st.success(f"Auditoria generada: {auditoria.auditoria_id}")
        finally:
            destino.unlink(missing_ok=True)
        st.cache_data.clear()

if mostrar_vivo:
    st.subheader("Video en vivo")
    st.caption(
        "El navegador envia la camara al backend; detecciones con bounding boxes se "
        "superponen sobre el video. Al tocar 'Detener y guardar' (alli) queda un resumen "
        "en el dashboard."
    )
    st.components.v1.html(
        f'<iframe src="{api_base}/rtc?zona_id={zona_viva}" '
        'allow="camera; microphone" width="100%" height="620" '
        'style="border:0;border-radius:.5rem"></iframe>',
        height=640,
    )

auditorias = _listar_auditorias()

if auditorias:
    ultima = auditorias[-1]
    metricas = ultima["metricas"]
    cols = st.columns(6)
    cols[0].metric("Total esperado", metricas["total_esperado"])
    cols[1].metric("Total detectado", metricas["total_detectado"])
    cols[2].metric("Discrepancias", metricas["cantidad_discrepancias"])
    cols[3].metric("Coincidencia", f'{metricas["porcentaje_coincidencia"]}%')
    cols[4].metric("Confianza prom.", f'{metricas["confianza_promedio"]:.2f}')
    cols[5].metric("A revisar", metricas["items_a_revisar"])
    st.caption(
        f'Ultima auditoria: {ultima["auditoria_id"]} - zona {ultima["zona_id"]} - '
        f'fecha {ultima["fecha_hora"]} - fuente {ultima.get("fuente", "imagen")}'
    )

    st.divider()
    st.subheader("Metricas ejecutivas")
    try:
        costo_hora = float(os.environ.get("COSTO_AUDITOR_HORA", "15"))
    except ValueError:
        costo_hora = 15.0
    ahorro_total = sum(a["metricas"]["tiempo_ahorrado_minutos"] for a in auditorias)
    con_discrepancia = sum(1 for a in auditorias if a["metricas"]["cantidad_discrepancias"] > 0)
    pct_ok = 100.0 * (1 - con_discrepancia / len(auditorias)) if auditorias else 0.0
    unidades_detectadas = sum(a["metricas"]["total_detectado"] for a in auditorias)

    cols2 = st.columns(4)
    cols2[0].metric("Auditorias realizadas", len(auditorias))
    cols2[1].metric(
        "Ahorro total de tiempo",
        f'{ahorro_total:.0f} min',
        help="Suma del tiempo manual estimado (0.25 min/unidad) menos el tiempo de procesamiento de la IA.",
    )
    cols2[2].metric(
        "ROI estimado",
        f"${(ahorro_total / 60) * costo_hora:,.0f}",
        help=f"Estimacion POC a un costo de auditoria de ${costo_hora:,.0f}/hora.",
    )
    cols2[3].metric("Auditorias OK (sin discrepancias)", f"{pct_ok:.0f}%")

    if auditorias:
        st.caption(f"Unidades detectadas acumuladas: {unidades_detectadas}")
        por_zona: dict[str, int] = {}
        for a in auditorias:
            zona = a["zona_id"]
            por_zona[zona] = por_zona.get(zona, 0) + 1
        st.markdown("**Auditorias por zona**")
        st.dataframe(
            [{"zona": zonas[z].nombre, "zona_id": z, "auditorias": n} for z, n in por_zona.items()],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Detalle de auditoria")
    seleccion = st.selectbox(
        "Auditoria",
        options=[a["auditoria_id"] for a in auditorias],
        format_func=lambda aid: (
            f"{aid} - {zonas[next(a['zona_id'] for a in auditorias if a['auditoria_id'] == aid)].nombre}"
        ),
        key="audit_seleccion",
    )
    detalle = _cargar_auditoria(seleccion)

    evidencia = ROOT_DIR / (detalle.get("evidencia_path") or "")
    col_ev, col_det = st.columns([3, 2])
    with col_ev:
        st.markdown("**Evidencia anotada**")
        if evidencia.exists():
            st.image(str(evidencia), caption=detalle.get("evidencia_path"), use_container_width=True)
        else:
            st.info(f"No se encontro la evidencia: {evidencia}")
        st.caption(f"Fuente: {detalle.get('fuente', 'imagen')}. Origen: {detalle.get('archivo_original')}")

    with col_det:
        st.markdown("**Discrepancias**")
        if detalle["discrepancias"]:
            st.dataframe(detalle["discrepancias"], use_container_width=True)
        else:
            st.info("Sin discrepancias para esta auditoria.")
        with st.expander("JSON completo"):
            st.json(detalle)
else:
    st.info("Todavia no hay auditorias. Ejecuta una simulacion desde la barra lateral.")

with st.expander("Fixtures disponibles"):
    st.code(json.dumps([str(Path("tests/fixtures") / name) for name in fixtures], indent=2), language="json")