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

st.title("📋 Tabla de Clientes")

# --- Consulta simple ---
response = supabase.table("cliente").select("*").execute()
st.write(response)
data = response.data if response.data else []

# --- Convertir a DataFrame ---
df_clientes = pd.DataFrame(data)

# --- Mostrar tabla ---
if df_clientes.empty:
    st.info("No hay clientes registrados")
    st.dataframe(
        pd.DataFrame(columns=[
            "id", "nombre", "codigo",
            "tipo_cobro"
        ]),
        use_container_width=True
    )
else:
    st.dataframe(df_clientes, use_container_width=True)
