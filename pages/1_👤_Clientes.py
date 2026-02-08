import streamlit as st
import pandas as pd
from supabase_client import supabase

st.header("👤 Clientes")
st.subheader("Agregar nuevo cliente")

# =========================
# INIT SESSION STATE
# =========================
if "clientes" not in st.session_state:
    st.session_state["clientes"] = (
        supabase.table("clientes")
        .select("*")
        .order("id")
        .execute()
        .data
    )

# =========================
# FORMULARIO
# =========================
with st.form("form_cliente", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre *")
        numero_cliente = st.text_input("Número de cliente *")
        telefono = st.text_input("Teléfono")

    with col2:
        correo = st.text_input("Correo electrónico")
        calle = st.text_input("Calle *")

        col_lote, col_manzana = st.columns(2)
        lote = col_lote.text_input("Lote")
        manzana = col_manzana.text_input("Manzana")

    submitted = st.form_submit_button("Agregar cliente")

    if submitted:
        if not nombre or not numero_cliente or not calle:
            st.error("❌ Campos obligatorios: Nombre, Número de cliente y Dirección")
        else:
            existente = (
                supabase
                .table("clientes")
                .select("id")
                .eq("numero_cliente", numero_cliente)
                .execute()
                .data
            )

            if existente:
                st.warning(f"⚠️ Ya existe un cliente con el número {numero_cliente}")
            else:
                nuevo_cliente = {
                    "nombre": nombre,
                    "numero_cliente": numero_cliente,
                    "calle": calle,
                    "lote": lote,
                    "manzana": manzana,
                    "telefono": telefono,
                    "correo": correo
                }

                supabase.table("clientes").insert(nuevo_cliente).execute()
                st.session_state["clientes"].append(nuevo_cliente)

                st.success("✅ Cliente registrado correctamente")
                st.rerun()

# =========================
# TABLA DE ESTADO
# =========================
st.divider()
st.subheader("📋 Clientes registrados")

df = pd.DataFrame(st.session_state["clientes"])

if df.empty:
    st.info("Aún no hay clientes registrados")
else:
    st.dataframe(
        df[[
            "nombre",
            "numero_cliente",
            "calle",
            "lote",
            "manzana",
            "telefono",
            "correo"
        ]],
        use_container_width=True
    )
