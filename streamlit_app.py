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


st.title("💧 Sistema de Clientes y Lecturas")

# ======================
# LAYOUT
# ======================
col1, col2 = st.columns([1, 2])

# ======================================================
# COLUMNA 1 — ALTA DE CLIENTE
# ======================================================
with col1:
    st.subheader("➕ Alta de Cliente")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre *")
        codigo = st.text_input("Código *")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo")

        st.markdown("**Dirección**")
        calle = st.text_input("Calle")
        lote = st.text_input("Lote")
        manzana = st.text_input("Manzana")

        tipo_cobro = st.selectbox("Tipo de cobro", ["Fijo", "Medidor"])

        guardar = st.form_submit_button("Guardar")

    if guardar:
        if not nombre or not codigo:
            st.error("Nombre y código son obligatorios")
        else:
            supabase.table("cliente").insert({
                "nombre": nombre,
                "codigo": codigo,
                "telefono": telefono,
                "correo": correo,
                "calle": calle,
                "lote": lote,
                "manzana": manzana,
                "tipo_cobro": tipo_cobro
            }).execute()

            st.success("Cliente registrado correctamente")
            st.rerun()

# ======================================================
# COLUMNA 2 — TABLA CLIENTES + JOIN
# ======================================================
with col2:
    st.subheader("📊 Clientes y Datos Asociados")

    clientes_data = supabase.table("cliente") \
        .select("""
            id,
            nombre,
            codigo,
            telefono,
            tipo_cobro,
            lectura(
                lectura_i,
                lectura_a,
                metros,
                created_at
            ),
            fijo(
                tarifa
            ),
            estado(
                estatus
            )
        """) \
        .order("id") \
        .execute().data

    df = pd.json_normalize(clientes_data)

    if df.empty:
        st.info("No hay clientes registrados")
    else:
        st.dataframe(df, use_container_width=True)
