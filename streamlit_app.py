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
    ["Clientes", "Servicios", "Lecturas", "Pagos"]
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
# SERVICIOS
# ======================================================
elif st.session_state.menu == "Servicios":
    st.title("🔧 Servicios")

    clientes = supabase.table("clientes").select("id,nombre").execute().data
    cliente_map = {c["nombre"]: c["id"] for c in clientes}

    catalogo_fijo = supabase.table("catalogo_servicios_fijos").select("*").execute().data
    catalogo_medidor = supabase.table("catalogo_medidor").select("*").execute().data

    fijo_map = {c["nombre"]: c for c in catalogo_fijo}
    medidor_map = {f"${c['precio_m3']} / m³": c for c in catalogo_medidor}

    with st.form("nuevo_servicio"):
        col1, col2, col3 = st.columns(3)

        cliente = col1.selectbox("Cliente *", cliente_map.keys())
        nombre_servicio = col2.text_input("Nombre del servicio *")
        tipo = col3.selectbox("Tipo de servicio *", ["FIJO", "MEDIDO"])

        st.divider()

        # =========================
        # FIJO
        # =========================
        servicio_fijo = st.selectbox(
            "Catálogo servicio fijo",
            fijo_map.keys(),
            disabled=(tipo != "FIJO")
        )

        tarifa_fija = st.number_input(
            "Tarifa fija",
            min_value=0.0,
            value=float(fijo_map[servicio_fijo]["tarifa"]) if tipo == "FIJO" else 0.0,
            disabled=(tipo != "FIJO")
        )

        # =========================
        # MEDIDO
        # =========================
        servicio_medido = st.selectbox(
            "Precio por m³",
            medidor_map.keys(),
            disabled=(tipo != "MEDIDO")
        )

        submitted = st.form_submit_button("Agregar servicio")

        if submitted:
            if not nombre_servicio:
                st.error("❌ El nombre del servicio es obligatorio")
            else:
                payload = {
                    "cliente_id": cliente_map[cliente],
                    "nombre_servicio": nombre_servicio,
                    "tipo_servicio": tipo,
                    "estado": "Vigente"
                }

                if tipo == "FIJO":
                    payload["catalogo_fijo_id"] = fijo_map[servicio_fijo]["id"]
                    payload["tarifa"] = tarifa_fija

                if tipo == "MEDIDO":
                    payload["catalogo_medidor_id"] = medidor_map[servicio_medido]["id"]
                    payload["tarifa"] = medidor_map[servicio_medido]["precio_m3"]

                supabase.table("servicios").insert(payload).execute()
                st.success("✅ Servicio creado correctamente")
                st.rerun()

# ======================================================
# LECTURAS
# ======================================================
elif st.session_state.menu == "Lecturas":
    st.title("📊 Lecturas")

    servicios = supabase.table("servicios") \
        .select("id,nombre_servicio,clientes(nombre)") \
        .eq("tipo_servicio", "MEDIDO") \
        .execute().data

    opciones = {
        s["id"]: f"{s['clientes']['nombre']} | {s['nombre_servicio']}"
        for s in servicios
    }

    with st.form("nueva_lectura"):
        servicio_id = st.selectbox("Servicio", options=list(opciones.keys()), format_func=lambda x: opciones[x])
        l_anterior = st.number_input("Lectura anterior", min_value=0.0)
        l_actual = st.number_input("Lectura actual", min_value=0.0)
        fecha = st.date_input("Fecha", value=date.today())
        submitted = st.form_submit_button("Registrar lectura")

        if submitted:
            supabase.table("lecturas").insert({
                "servicio_id": servicio_map[servicio],
                "lectura_anterior": l_anterior,
                "lectura_actual": l_actual,
                "fecha": fecha.isoformat()
            }).execute()
            st.success("Lectura registrada")

# ======================================================
# PAGOS (SECCIÓN INDEPENDIENTE)
# ======================================================
elif st.session_state.menu == "Pagos":
    st.title("💰 Pagos")

    servicios = supabase.table("servicios") \
        .select("id,nombre_servicio,tarifa,clientes(nombre)") \
        .execute().data

    servicio_map = {
        f"{s['clientes']['nombre']} | {s['nombre_servicio']}": s
        for s in servicios
    }

    with st.form("nuevo_pago"):
        servicio_key = st.selectbox("Servicio", servicio_map.keys())
        servicio = servicio_map[servicio_key]

        monto = st.number_input(
            "Monto",
            value=float(servicio["tarifa"]),
            min_value=0.0
        )

        metodo = st.selectbox("Método de pago", ["Efectivo", "Transferencia", "Tarjeta"])
        fecha = st.date_input("Fecha de pago", value=date.today())
        submitted = st.form_submit_button("Registrar pago")

        if submitted:
            supabase.table("pagos").insert({
                "servicio_id": servicio["id"],
                "monto": monto,
                "metodo": metodo,
                "fecha_pago": fecha.isoformat()
            }).execute()
            st.success("Pago registrado")

