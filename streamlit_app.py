import streamlit as st
import pandas as pd
from supabase import create_client

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(page_title="Sistema de Clientes", layout="wide")
st.title("💧 Sistema de Clientes – Vista General")

# ======================================================
# CONEXIÓN SUPABASE
# ======================================================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_anon_key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# CONSULTA PRINCIPAL (JOIN REAL – TU VERSIÓN)
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

# ======================================================
# MAPEO CLIENTES (AUNQUE NO TENGAN RELACIONES)
# ======================================================
clientes_map = {c["nombre"]: c for c in clientes_data} if clientes_data else {}

# ======================================================
# LAYOUT
# ======================================================
col1, col2 = st.columns([1, 2])

# ======================================================
# COLUMNA 1 – CAPTURA / SELECCIÓN (SIEMPRE VISIBLE)
# ======================================================
with col1:
    st.subheader("👤 Cliente")

    if clientes_map:
        cliente_nombre = st.selectbox(
            "Selecciona cliente",
            clientes_map.keys()
        )
        cliente = clientes_map[cliente_nombre]
    else:
        st.info("No hay clientes registrados")
        cliente = {}

    st.text_input("Código", cliente.get("codigo", ""), disabled=True)
    st.text_input("Teléfono", cliente.get("telefono", ""), disabled=True)
    st.text_input("Tipo de cobro", cliente.get("tipo_cobro", ""), disabled=True)

# ======================================================
# COLUMNA 2 – DATAFRAME CONSOLIDADO
# ======================================================
with col2:
    st.subheader("📊 Información consolidada")

    if cliente:
        lectura = cliente.get("Lectura", [])
        fijo = cliente.get("Fijo", [])
        estado = cliente.get("Estado", [])

        row = {
            "Cliente": cliente["nombre"],
            "Estado": estado[0]["estatus"] if estado else None,
            "Lectura inicial": lectura[0]["lectura_i"] if lectura else None,
            "Lectura actual": lectura[0]["lectura_a"] if lectura else None,
            "Consumo (m³)": lectura[0]["metros"] if lectura else None,
            "Tarifa": fijo[0]["Tarifa"] if fijo else None,
            "Fecha lectura": lectura[0]["created_at"] if lectura else None
        }

        df = pd.DataFrame([row])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Selecciona un cliente para ver información")

