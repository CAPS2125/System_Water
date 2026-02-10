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
# CONSULTA CLIENTES
# ======================================================
clientes_data = supabase.table("cliente") \
    .select("""
        id,
        nombre,
        codigo,
        telefono,
        correo,
        calle,
        lote,
        manzana,
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

clientes_map = {c["nombre"]: c for c in clientes_data} if clientes_data else {}

# ======================================================
# LAYOUT
# ======================================================
col1, col2 = st.columns([1, 2])

# ======================================================
# COLUMNA 1 – ALTA + SELECCIÓN
# ======================================================
with col1:
    st.subheader("➕ Alta de cliente")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre del cliente")
        codigo = st.text_input("Código")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo electrónico")

        st.markdown("**Dirección**")
        calle = st.text_input("Calle")
        lote = st.number_input("Lote")
        manzana = st.number_input("Manzana")

        tipo_cobro = st.selectbox("Tipo de cobro", ["Fijo", "Medidor"])

        guardar = st.form_submit_button("Guardar cliente")

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

            st.success("✅ Cliente registrado")
            st.rerun()

    st.divider()

    st.subheader("👤 Clientes registrados")

    if clientes_map:
        cliente_nombre = st.selectbox(
            "Selecciona cliente",
            clientes_map.keys()
        )
        cliente = clientes_map[cliente_nombre]
    else:
        cliente = None
        st.info("Aún no hay clientes")

# ======================================================
# COLUMNA 2 – VISTA CONSOLIDADA
# ======================================================
with col2:
    st.subheader("📊 Información del cliente")

    if cliente:
        lectura = cliente.get("Lectura", [])
        fijo = cliente.get("Fijo", [])
        estado = cliente.get("Estado", [])

        df = pd.DataFrame([{
            "Cliente": cliente["nombre"],
            "Estado": estado[0]["estatus"] if estado else None,
            "Lectura inicial": lectura[0]["lectura_i"] if lectura else None,
            "Lectura actual": lectura[0]["lectura_a"] if lectura else None,
            "Consumo (m³)": lectura[0]["metros"] if lectura else None,
            "Tarifa": fijo[0]["Tarifa"] if fijo else None,
            "Fecha lectura": lectura[0]["created_at"] if lectura else None
        }])

        st.dataframe(df, use_container_width=True)
    else:
        st.info("Selecciona o registra un cliente")
