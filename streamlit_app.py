import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(
    page_title="Sistema de Clientes",
    layout="wide"
)

st.title("💧 Sistema de Clientes – Vista General")

# ======================================================
# CONEXIÓN SUPABASE
# ======================================================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_anon_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# CONSULTA PRINCIPAL (JOIN REAL)
# ======================================================
clientes_data = supabase.table("cliente") \
    .select("""
        id,
        nombre,
        codigo,
        telefono,
        tipo_cobro,
        Lectura(
            lectura_i,
            lectura_a,
            metros,
            created_at
        ),
        Fijo(
            Tarifa
        ),
        Estado(
            estatus
        )
    """) \
    .execute().data

if not clientes_data:
    st.info("No hay clientes registrados")
    st.stop()

# ======================================================
# MAPEO CLIENTES
# ======================================================
clientes_map = {c["nombre"]: c for c in clientes_data}

# ======================================================
# LAYOUT PRINCIPAL
# ======================================================
col1, col2 = st.columns([1, 2])

# ======================================================
# COLUMNA 1 – CLIENTE
# ======================================================
with col1:
    st.subheader("👤 Cliente")

    cliente_nombre = st.selectbox(
        "Selecciona cliente",
        clientes_map.keys()
    )

    cliente = clientes_map[cliente_nombre]

    st.text_input("Código", cliente["codigo"], disabled=True)
    st.text_input("Teléfono", cliente["telefono"], disabled=True)
    st.text_input("Tipo de cobro", cliente["tipo_cobro"], disabled=True)

# ======================================================
# COLUMNA 2 – INFORMACIÓN CONSOLIDADA
# ======================================================
with col2:
    st.subheader("📄 Información Consolidada")

    # Lectura
    lectura = cliente["lectura"][0] if cliente["lectura"] else None
    consumo = lectura["metros"] if lectura else 0

    # Tarifa
    tarifa = cliente["fijo"][0]["tarifa"] if cliente["fijo"] else 0

    # Estado
    estado = cliente["estado"][0]["estatus"] if cliente["estado"] else "SIN ESTADO"

    # Deuda (estimada)
    deuda = consumo * tarifa

    st.metric("Estado del servicio", estado)
    st.metric("Consumo (m³)", consumo)
    st.metric("Tarifa aplicada", f"${tarifa}")
    st.metric("Deuda estimada", f"${deuda:.2f}")

    if lectura:
        st.caption(f"Última lectura: {lectura['created_at']}")
    else:
        st.caption("Sin lecturas registradas")
