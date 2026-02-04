import streamlit as st
from supabase import create_client
from datetime import date
from dateutil.relativedelta import relativedelta

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Control de Clientes y Servicios",
    layout="wide"
)

# =========================
# SUPABASE CLIENT
# =========================
supabase = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_anon_key"]
)

# =========================
# LOGIN MOCK
# =========================
def login():
    st.title("🔐 Iniciar sesión")

    with st.form("login"):
        email = st.text_input("Correo")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        if (
            email == st.secrets["login_email"]
            and password == st.secrets["login_password"]
        ):
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login()
    st.stop()

# =========================
# HELPERS
# =========================
def limpiar(txt):
    return txt.strip() if txt else None

def calcular_estado(servicio):
    if servicio["estado"] == "Suspendido":
        return "Suspendido"
    if servicio["proximo_pago"] and date.today() > date.fromisoformat(servicio["proximo_pago"]):
        return "Vencido"
    return "Vigente"

# =========================
# HEADER
# =========================
st.title("📊 Control de Clientes y Servicios")

# =========================
# ➕ ALTA CLIENTE + SERVICIO
# =========================
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
        cliente = supabase.table("clientes").insert({
            "nombre_completo": limpiar(nombre),
            "telefono": limpiar(telefono),
            "correo": limpiar(correo),
            "direccion": limpiar(direccion)
        }).execute()

        cliente_id = cliente.data[0]["id"]

        servicio = {
            "cliente_id": cliente_id,
            "nombre_servicio": limpiar(servicio_nombre),
            "tipo_servicio": tipo_servicio,
            "tarifa": tarifa,
            "lectura_anterior": lectura,
            "ultimo_pago": ultimo_pago.isoformat() if ultimo_pago else None,
            "proximo_pago": proximo_pago.isoformat() if proximo_pago else None,
            "adeudo": 0,
            "estado": "Vigente"
        }

        servicio["estado"] = calcular_estado(servicio)

        supabase.table("servicios").insert(servicio).execute()

        st.success("Cliente y servicio registrados")
        st.rerun()

# =========================
# 📋 SERVICIOS
# =========================
st.divider()

servicios = supabase.table("servicios") \
    .select("*, clientes(*)") \
    .execute().data

activos = []
suspendidos = []

for s in servicios:
    s["estado"] = calcular_estado(s)
    supabase.table("servicios").update({
        "estado": s["estado"]
    }).eq("id", s["id"]).execute()

    if s["estado"] == "Suspendido":
        suspendidos.append(s)
    else:
        activos.append(s)

# =========================
# ✅ ACTIVOS
# =========================
st.subheader("✅ Servicios Activos")

if activos:
    for s in activos:
        with st.expander(f"👤 {s['clientes']['nombre_completo']} | {s['nombre_servicio']}"):
            st.write(f"📞 {s['clientes']['telefono']}")
            st.write(f"📍 {s['clientes']['direccion']}")
            st.write(f"💲 Adeudo: ${s['adeudo']}")
            st.info(f"Estado: {s['estado']}")

            # ---- PAGO
            with st.expander("💰 Registrar pago"):
                with st.form(f"pago_{s['id']}"):
                    monto = st.number_input("Cantidad", min_value=0.0)
                    meses = st.number_input("Meses", min_value=1, step=1)
                    metodo = st.selectbox("Método", ["EFECTIVO", "TARJETA", "TRANSFERENCIA"])
                    pagar = st.form_submit_button("Aceptar")

                if pagar:
                    supabase.table("pagos").insert({
                        "servicio_id": s["id"],
                        "fecha_pago": date.today().isoformat(),
                        "monto": monto,
                        "meses_pagados": meses,
                        "metodo_pago": metodo
                    }).execute()

                    nuevo_adeudo = max(0, s["adeudo"] - monto)
                    nuevo_proximo = (
                        date.fromisoformat(s["proximo_pago"]) + relativedelta(months=meses)
                        if s["proximo_pago"] else None
                    )

                    supabase.table("servicios").update({
                        "adeudo": nuevo_adeudo,
                        "ultimo_pago": date.today().isoformat(),
                        "proximo_pago": nuevo_proximo.isoformat() if nuevo_proximo else None
                    }).eq("id", s["id"]).execute()

                    st.success("Pago registrado")
                    st.rerun()

            if st.button("⛔ Suspender servicio", key=f"susp_{s['id']}"):
                supabase.table("servicios").update({
                    "estado": "Suspendido"
                }).eq("id", s["id"]).execute()
                st.warning("Servicio suspendido")
                st.rerun()
else:
    st.info("No hay servicios activos")

# =========================
# 🚫 SUSPENDIDOS
# =========================
st.divider()
st.subheader("🚫 Servicios Suspendidos")

if suspendidos:
    for s in suspendidos:
        with st.expander(f"⛔ {s['clientes']['nombre_completo']} | {s['nombre_servicio']}"):
            if st.button("▶️ Reactivar", key=f"react_{s['id']}"):
                supabase.table("servicios").update({
                    "estado": "Vigente"
                }).eq("id", s["id"]).execute()
                st.success("Servicio reactivado")
                st.rerun()
else:
    st.info("No hay servicios suspendidos")
