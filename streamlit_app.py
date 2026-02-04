import streamlit as st
from datetime import date

# =========================
# INIT SESSION STATE
# =========================
if "clientes" not in st.session_state:
    st.session_state.clientes = []

if "servicios" not in st.session_state:
    st.session_state.servicios = []

if "pagos" not in st.session_state:
    st.session_state.pagos = []

# =========================
# HELPERS
# =========================
def limpiar(txt):
    return txt.strip() if txt else None

def calcular_estado(servicio):
    if servicio["estado"] == "Suspendido":
        return "Suspendido"
    if servicio["proximo_pago"] and date.today() > servicio["proximo_pago"]:
        return "Vencido"
    return "Vigente"

def next_id(lista):
    return len(lista) + 1

# =========================
# LOGIN MOCK
# =========================
def login_mock():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.title("🔐 Inicio de Sesión")

    with st.form("login_form"):
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        if (
            email == st.secrets["login_email"]
            and password == st.secrets["login_password"]
        ):
            st.session_state.logged_in = True
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    return False

if not login_mock():
    st.stop()

# =========================
# ➕ ALTA CLIENTE + SERVICIO
# =========================
st.title("📊 Control de Clientes y Servicios")
st.subheader("➕ Registrar cliente y servicio")

with st.form("alta_cliente"):
    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre completo")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo")
        direccion = st.text_input("Dirección")

    with col2:
        servicio_nombre = st.text_input("Servicio")
        tipo_servicio = st.selectbox("Tipo", ["FIJO", "MEDIDO"])
        tarifa = st.number_input("Tarifa", min_value=0.0)
        lectura = st.number_input("Lectura inicial", min_value=0)

    col3, col4 = st.columns(2)
    with col3:
        ultimo_pago = st.date_input("Último pago", value=None)
    with col4:
        proximo_pago = st.date_input("Próximo pago", value=None)

    guardar = st.form_submit_button("💾 Guardar")

    if guardar and nombre:
        cliente_id = next_id(st.session_state.clientes)

        cliente = {
            "id": cliente_id,
            "nombre_completo": limpiar(nombre),
            "telefono": limpiar(telefono),
            "correo": limpiar(correo),
            "direccion": limpiar(direccion),
        }
        st.session_state.clientes.append(cliente)

        servicio = {
            "id": next_id(st.session_state.servicios),
            "cliente_id": cliente_id,
            "nombre_servicio": limpiar(servicio_nombre),
            "tipo_servicio": tipo_servicio,
            "tarifa": tarifa,
            "lectura_anterior": lectura,
            "ultimo_pago": ultimo_pago,
            "proximo_pago": proximo_pago,
            "adeudo": tarifa,
            "estado": "Vigente",
        }
        servicio["estado"] = calcular_estado(servicio)

        st.session_state.servicios.append(servicio)

        st.success("Cliente y servicio guardados (mock)")
        st.rerun()

# =========================
# 📋 SERVICIOS ACTIVOS
# =========================
st.divider()
st.subheader("✅ Servicios Activos")

activos = []
suspendidos = []

for s in st.session_state.servicios:
    s["estado"] = calcular_estado(s)
    if s["estado"] == "Suspendido":
        suspendidos.append(s)
    else:
        activos.append(s)

def get_cliente(cliente_id):
    return next(c for c in st.session_state.clientes if c["id"] == cliente_id)

if activos:
    for s in activos:
        cliente = get_cliente(s["cliente_id"])

        with st.expander(f"👤 {cliente['nombre_completo']} | {s['nombre_servicio']}"):
            st.write(f"📞 {cliente['telefono']}")
            st.write(f"📍 {cliente['direccion']}")
            st.write(f"💲 Adeudo: ${s['adeudo']}")
            st.info(f"Estado: {s['estado']}")

            # ---- PAGO
            with st.expander("💰 Registrar pago"):
                with st.form(f"pago_{s['id']}"):
                    monto = st.number_input("Cantidad a pagar", min_value=0.0, key=f"m_{s['id']}")
                    meses = st.number_input("Meses", min_value=1, step=1, key=f"mes_{s['id']}")
                    metodo = st.selectbox(
                        "Método",
                        ["EFECTIVO", "TARJETA", "TRANSFERENCIA"],
                        key=f"met_{s['id']}"
                    )
                    pagar = st.form_submit_button("Aceptar")

                if pagar:
                    pago = {
                        "servicio_id": s["id"],
                        "fecha_pago": date.today(),
                        "monto": monto,
                        "meses_pagados": meses,
                        "metodo_pago": metodo,
                    }
                    st.session_state.pagos.append(pago)
                    s["adeudo"] = max(0, s["adeudo"] - monto)
                    s["ultimo_pago"] = date.today()
                    st.success("Pago registrado (mock)")
                    st.rerun()

            if st.button("⛔ Suspender servicio", key=f"susp_{s['id']}"):
                s["estado"] = "Suspendido"
                st.warning("Servicio suspendido")
                st.rerun()
else:
    st.info("No hay servicios activos")

# =========================
# 🚫 SERVICIOS SUSPENDIDOS
# =========================
st.divider()
st.subheader("🚫 Servicios Suspendidos")

if suspendidos:
    for s in suspendidos:
        cliente = get_cliente(s["cliente_id"])

        with st.expander(f"⛔ {cliente['nombre_completo']} | {s['nombre_servicio']}"):
            if st.button("▶️ Reactivar", key=f"react_{s['id']}"):
                s["estado"] = "Vigente"
                st.success("Servicio reactivado")
                st.rerun()
else:
    st.info("No hay servicios suspendidos")
