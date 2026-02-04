import streamlit as st
from supabase import create_client
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="System Water", layout="wide")

supabase = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_anon_key"]
)

# =========================
# HELPERS UI
# =========================
def estado_badge(activo: bool):
    color = "#22c55e" if activo else "#ef4444"
    label = "Activo" if activo else "Suspendido"
    return f"""
    <span style="
        padding:4px 10px;
        border-radius:12px;
        background:{color};
        color:white;
        font-size:12px;
    ">{label}</span>
    """

# =========================
# DATA LOADERS
# =========================
@st.cache_data
def get_clientes():
    return supabase.table("clientes").select("*").execute().data

@st.cache_data
def get_servicios():
    return supabase.table("servicios").select("*").execute().data

# =========================
# SIDEBAR
# =========================
st.sidebar.title("🚰 System Water")

seccion = st.sidebar.radio(
    "Sección",
    ["Clientes", "Servicios", "Pagos"]
)

# =========================
# CLIENTES
# =========================
if seccion == "Clientes":
    st.title("👥 Clientes")

    clientes = get_clientes()

    for c in clientes:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"**{c['nombre']}**")
            st.caption(c.get("direccion", ""))

        with col2:
            st.markdown(
                estado_badge(c["activo"]),
                unsafe_allow_html=True
            )

# =========================
# SERVICIOS
# =========================
elif seccion == "Servicios":
    st.title("🛠️ Servicios")

    servicios = get_servicios()

    for s in servicios:
        col1, col2, col3 = st.columns([4, 2, 1])

        with col1:
            st.markdown(f"**{s['nombre']}**")
            st.caption(s.get("descripcion", ""))

        with col2:
            st.metric("Precio", f"${s['precio']}")

        with col3:
            st.markdown(
                estado_badge(s["activo"]),
                unsafe_allow_html=True
            )

# =========================
# PAGOS (SECCIÓN APARTE)
# =========================
elif seccion == "Pagos":
    st.title("💰 Pagos")

    clientes = get_clientes()
    servicios = get_servicios()

    st.subheader("Registrar pago")

    col1, col2 = st.columns(2)

    with col1:
        cliente = st.selectbox(
            "Cliente",
            clientes,
            format_func=lambda c: c["nombre"]
        )

    with col2:
        servicio = st.selectbox(
            "Servicio",
            servicios,
            format_func=lambda s: s["nombre"]
        )

    st.metric("Monto a pagar", f"${servicio['precio']}")

    metodo = st.selectbox(
        "Método de pago",
        ["Efectivo", "Transferencia", "Tarjeta"]
    )

    if st.button("Registrar pago", type="primary"):
        supabase.table("pagos").insert({
            "cliente_id": cliente["id"],
            "servicio_id": servicio["id"],
            "monto": servicio["precio"],
            "metodo": metodo.lower(),
            "estado": "pagado",
            "fecha": datetime.utcnow().isoformat()
        }).execute()

        st.success("Pago registrado correctamente")
        st.cache_data.clear()

