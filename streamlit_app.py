import streamlit as st
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
if st.session_state.menu == "Clientes":
    st.title("👤 Clientes")

    with st.form("nuevo_cliente"):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre")
        email = col2.text_input("Email")
        telefono = col1.text_input("Teléfono")
        direccion = col2.text_input("Dirección")
        submitted = st.form_submit_button("Guardar cliente")

        if submitted:
            supabase.table("clientes").insert({
                "nombre": nombre,
                "email": email,
                "telefono": telefono,
                "direccion": direccion
            }).execute()
            st.success("Cliente agregado")

    clientes = supabase.table("clientes").select("*").execute().data

    st.divider()
    for c in clientes:
        estado_color = "🟢" if c["estado"] == "Activo" else "🔴"
        st.write(f"{estado_color} **{c['nombre']}** — {c['email']}")

# ======================================================
# SERVICIOS
# ======================================================
elif st.session_state.menu == "Servicios":
    st.title("🔧 Servicios")

    clientes = supabase.table("clientes").select("id,nombre").execute().data
    cliente_map = {c["nombre"]: c["id"] for c in clientes}

    with st.form("nuevo_servicio"):
        col1, col2, col3 = st.columns(3)
        cliente = col1.selectbox("Cliente", cliente_map.keys())
        nombre_servicio = col2.text_input("Nombre del servicio")
        tipo = col3.selectbox("Tipo", ["FIJO", "MEDIDO"])
        tarifa = col1.number_input("Tarifa", min_value=0.0)
        submitted = st.form_submit_button("Agregar servicio")

        if submitted:
            supabase.table("servicios").insert({
                "cliente_id": cliente_map[cliente],
                "nombre_servicio": nombre_servicio,
                "tipo_servicio": tipo,
                "tarifa": tarifa
            }).execute()
            st.success("Servicio creado")

    servicios = supabase.table("servicios") \
        .select("id,nombre_servicio,estado,clientes(nombre)") \
        .execute().data

    st.divider()
    for s in servicios:
        color = "🟢" if s["estado"] == "Vigente" else "🔴"
        st.write(f"{color} **{s['nombre_servicio']}** — {s['clientes']['nombre']}")

# ======================================================
# LECTURAS
# ======================================================
elif st.session_state.menu == "Lecturas":
    st.title("📊 Lecturas")

    servicios = supabase.table("servicios") \
        .select("id,nombre_servicio,clientes(nombre)") \
        .eq("tipo_servicio", "MEDIDO") \
        .execute().data

    servicio_map = {
        f"{s['clientes']['nombre']} | {s['nombre_servicio']}": s["id"]
        for s in servicios
    }

    with st.form("nueva_lectura"):
        servicio = st.selectbox("Servicio", servicio_map.keys())
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

