import streamlit as st

# =========================
# CONFIG GENERAL
# =========================
st.set_page_config(
    page_title="System Water – Demo UI",
    layout="wide"
)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.title("🌊 System Water")
    st.caption("Demo UI · Sin BD · Sin Login")

    st.divider()

    menu = st.radio(
        "Navegación",
        ["Dashboard", "Registrar dato", "Historial", "Configuración"]
    )

# =========================
# HEADER
# =========================
st.title("📊 System Water")
st.caption("Interfaz visual · datos simulados")

st.divider()

# =========================
# DASHBOARD
# =========================
if menu == "Dashboard":
    st.subheader("📈 Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric("Registros", "128")
    col2.metric("Última medición", "7.2 pH")
    col3.metric("Estado", "Óptimo")

    st.divider()

    st.info("Aquí irá el resumen general del sistema.")

# =========================
# REGISTRAR DATO
# =========================
elif menu == "Registrar dato":
    st.subheader("📝 Registrar medición")

    with st.form("form_registro"):
        col1, col2 = st.columns(2)

        with col1:
            ph = st.number_input("pH", min_value=0.0, max_value=14.0, step=0.1)
            temperatura = st.number_input("Temperatura (°C)", step=0.1)

        with col2:
            conductividad = st.number_input("Conductividad", step=0.1)
            oxigeno = st.number_input("Oxígeno disuelto", step=0.1)

        submitted = st.form_submit_button("Guardar (simulado)")

        if submitted:
            st.success("✔ Medición enviada (no se guardó nada)")

# =========================
# HISTORIAL
# =========================
elif menu == "Historial":
    st.subheader("📚 Historial de mediciones")

    st.warning("Datos simulados")

    fake_data = [
        {"Fecha": "2026-02-01", "pH": 7.1, "Temp": 22.3},
        {"Fecha": "2026-01-31", "pH": 7.3, "Temp": 21.9},
        {"Fecha": "2026-01-30", "pH": 7.0, "Temp": 22.1},
    ]

    st.table(fake_data)

# =========================
# CONFIGURACIÓN
# =========================
elif menu == "Configuración":
    st.subheader("⚙ Configuración")

    st.checkbox("Notificaciones activas", value=True)
    st.selectbox("Unidad de temperatura", ["Celsius", "Fahrenheit"])
    st.button("Guardar cambios (fake)")

    st.info("Configuración visual solamente.")

# =========================
# FOOTER
# =========================
st.divider()
st.caption("Demo UI · Streamlit · Sin backend")
