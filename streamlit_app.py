import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="💧 Padre Kino", layout="wide")

# ---------------------------
# SUPABASE CLIENT
# ---------------------------
supabase = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_anon_key"]
)

# ---------------------------
# SESSION STATE
# ---------------------------
if "menu" not in st.session_state:
    st.session_state.menu = "Clientes"

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.title("💧 Padre Kino")

st.session_state.menu = st.sidebar.radio(
    "Menú",
    ["Clientes", "Tipo de Servicio", "Servicios", "Lecturas", "Pagos"]
)

# ======================================================
# CLIENTES
# ======================================================
columnas_ui = [
    "nombre",
    "numero_cliente",
    "calle",
    "lote",
    "manzana",
    "telefono",
    "correo"
]

# =========================
# INIT CLIENTES DESDE SUPABASE
# =========================
if "clientes" not in st.session_state:
    response = supabase.table("clientes").select("*").execute()
    st.session_state["clientes"] = response.data or []

if st.session_state.menu == "Clientes":
    st.header("👤 Clientes")
    st.subheader("Agregar nuevo cliente")

    # =========================
    # FORMULARIO
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre *")
        numero_cliente = st.text_input("Número de cliente *")
        telefono = st.text_input("Teléfono")

    with col2:
        correo = st.text_input("Correo electrónico")
        calle = st.text_input("Calle *")

        col_lote, col_manzana = st.columns(2)
        with col_lote:
            lote = st.text_input("Lote")
        with col_manzana:
            manzana = st.text_input("Manzana")

    if st.button("Agregar cliente"):
        if not nombre or not numero_cliente or not calle:
            st.error("❌ Campos obligatorios: Nombre, Número de cliente y Dirección")
        else:
            # 1️⃣ Verificar si ya existe el número de cliente
            existente = (
                supabase
                .table("clientes")
                .select("id")
                .eq("numero_cliente", numero_cliente)
                .execute()
                .data
            )

            if existente:
                st.warning(
                    f"⚠️ Ya existe un cliente con el número {numero_cliente}"
                )
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

                # 2️⃣ Mantener frontend en sync
                st.session_state["clientes"].append(nuevo_cliente)

                st.success("✅ Cliente registrado correctamente")
                st.rerun()

    # =========================
    # TABLA DE ESTADO DEL SISTEMA
    # =========================
    st.divider()
    st.subheader("📋 Clientes registrados en el sistema")

    df_clientes = pd.DataFrame(st.session_state.get("clientes", []))

    if df_clientes.empty:
        st.info("Aún no hay clientes registrados")
    else:
        columnas_presentes = [c for c in columnas_ui if c in df_clientes.columns]
        df_clientes = df_clientes[columnas_presentes]
        st.dataframe(df_clientes, use_container_width=True)

# ======================================================
# CATÁLOGO DE SERVICIOS
# ======================================================
elif st.session_state.menu == "Tipo de servicios":
    st.header("🧾 Catálogo de Servicios")

    with st.form("form_catalogo_servicio"):
        col1, col2, col3 = st.columns(3)

        nombre = col1.text_input("Nombre del servicio *")
        tipo = col2.selectbox("Tipo de servicio *", ["FIJO", "MEDIDO"])
        activo = col3.checkbox("Activo", value=True)

        st.divider()

        # ---------- FIJO ----------
        tarifa_fija = st.number_input(
            "Tarifa fija ($)",
            min_value=0.0,
            step=1.0,
            disabled=(tipo != "FIJO")
        )

        # ---------- MEDIDO ----------
        precio_m3 = st.number_input(
            "Precio por m³ ($)",
            min_value=0.0,
            step=0.01,
            disabled=(tipo != "MEDIDO")
        )

        submitted = st.form_submit_button("Guardar servicio")

        if submitted:
            # =========================
            # VALIDACIONES
            # =========================
            if not nombre:
                st.error("❌ El nombre del servicio es obligatorio")

            elif tipo == "FIJO" and tarifa_fija <= 0:
                st.error("❌ La tarifa fija debe ser mayor a 0")

            elif tipo == "MEDIDO" and precio_m3 <= 0:
                st.error("❌ El precio por m³ debe ser mayor a 0")

            else:
                payload = {
                    "nombre": nombre,
                    "tipo": tipo,
                    "activo": activo,
                    "tarifa_fija": tarifa_fija if tipo == "FIJO" else None,
                    "precio_m3": precio_m3 if tipo == "MEDIDO" else None
                }

                try:
                    supabase.table("catalogo_servicios").insert(payload).execute()
                    st.success("✅ Servicio agregado correctamente")
                    st.rerun()

                except Exception as e:
                    st.error("❌ Error al guardar el servicio")
                    st.exception(e)
