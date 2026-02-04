import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text
from database import get_db
from models import Cliente, Servicio, Pago

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Control de Servicios",
    page_icon="📊",
    layout="wide"
)

db = get_db()

# =========================
# AUTH
# =========================
if "auth" not in st.session_state:
    st.session_state.auth = False


def login():
    st.title("🔐 Inicio de sesión")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        btn = st.form_submit_button("Ingresar")

    if btn:
        result = db.execute(
            text("""
                SELECT * FROM usuarios
                WHERE username = :u
                AND password = :p
                AND activo = true
            """),
            {"u": username.strip(), "p": password.strip()}
        ).fetchone()

        if result:
            st.session_state.auth = True
            st.success("Bienvenido")
            st.rerun()
        else:
            st.error("Credenciales incorrectas")


if not st.session_state.auth:
    login()
    st.stop()

# =========================
# HELPERS
# =========================
def limpiar(txt):
    return txt.strip() if txt else None


def calcular_estado(servicio):
    if servicio.estado == "Suspendido":
        return "Suspendido"
    if servicio.proximo_pago and date.today() > servicio.proximo_pago:
        return "Vencido"
    return "Vigente"


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
        cliente = Cliente(
            nombre_completo=limpiar(nombre),
            telefono=limpiar(telefono),
            correo=limpiar(correo),
            direccion=limpiar(direccion)
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

        servicio = Servicio(
            cliente_id=cliente.id,
            nombre_servicio=limpiar(servicio_nombre),
            tipo_servicio=tipo_servicio,
            tarifa=tarifa,
            lectura_anterior=lectura,
            ultimo_pago=ultimo_pago,
            proximo_pago=proximo_pago,
            estado="Vigente"
        )
        servicio.estado = calcular_estado(servicio)

        db.add(servicio)
        db.commit()

        st.success("Cliente y servicio guardados")

# =========================
# 📋 SERVICIOS ACTIVOS
# =========================
st.divider()
st.subheader("✅ Servicios Activos")

servicios = db.query(Servicio).all()

activos = []
suspendidos = []

for s in servicios:
    s.estado = calcular_estado(s)
    db.commit()
    if s.estado == "Suspendido":
        suspendidos.append(s)
    else:
        activos.append(s)

if activos:
    for s in activos:
        with st.expander(f"👤 {s.cliente.nombre_completo} | {s.nombre_servicio}"):
            st.write(f"📞 {s.cliente.telefono}")
            st.write(f"📍 {s.cliente.direccion}")
            st.write(f"💲 Adeudo: ${s.adeudo}")
            st.info(f"Estado: {s.estado}")

            # ---- PAGO
            with st.expander("💰 Registrar pago"):
                with st.form(f"pago_{s.id}"):
                    monto = st.number_input("Cantidad a pagar", min_value=0.0)
                    meses = st.number_input("Meses", min_value=1, step=1)
                    metodo = st.selectbox("Método", ["EFECTIVO", "TARJETA", "TRANSFERENCIA"])
                    pagar = st.form_submit_button("Aceptar")

                if pagar:
                    pago = Pago(
                        servicio_id=s.id,
                        fecha_pago=date.today(),
                        monto=monto,
                        meses_pagados=meses,
                        metodo_pago=metodo
                    )
                    s.adeudo = max(0, s.adeudo - monto)
                    s.ultimo_pago = date.today()
                    db.add(pago)
                    db.commit()
                    st.success("Pago registrado")
                    st.rerun()

            if st.button("⛔ Suspender servicio", key=f"susp_{s.id}"):
                s.estado = "Suspendido"
                db.commit()
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
        with st.expander(f"⛔ {s.cliente.nombre_completo} | {s.nombre_servicio}"):
            if st.button("▶️ Reactivar", key=f"react_{s.id}"):
                s.estado = "Vigente"
                db.commit()
                st.success("Servicio reactivado")
                st.rerun()
else:
    st.info("No hay servicios suspendidos")
