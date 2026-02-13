import streamlit as st
import pandas as pd
from supabase import create_client

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(page_title="Padre Kino", layout="wide")

# ======================================================
# CONEXIÓN SUPABASE
# ======================================================
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_anon_key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# FUNCIONES BASE
# =========================

def obtener_cliente(codigo):
    response = supabase.table("clientes") \
        .select("*") \
        .eq("codigo", codigo) \
        .execute()

    if response.data:
        return response.data[0]
    return None


def calcular_saldo(cliente_id):
    response = supabase.table("pagos") \
        .select("cargo_generado, pago_realizado") \
        .eq("cliente_id", cliente_id) \
        .execute()

    movimientos = response.data or []

    total_cargos = sum(m["cargo_generado"] or 0 for m in movimientos)
    total_pagos = sum(m["pago_realizado"] or 0 for m in movimientos)

    return total_cargos - total_pagos


def registrar_pago(cliente_id, cargo, pago, metodo):
    supabase.table("pagos").insert({
        "cliente_id": cliente_id,
        "fecha": datetime.now().isoformat(),
        "cargo_generado": cargo,
        "pago_realizado": pago,
        "metodo_pago": metodo
    }).execute()


def suspender_servicio(cliente_id):
    supabase.table("cliente") \
        .update({"estado_servicio": "Suspendido"}) \
        .eq("id", cliente_id) \
        .execute()


# =========================
# DIALOGO PRINCIPAL
# =========================

@st.dialog("Gestión de Gastos")
def dialog_gestion(cliente):

    cliente_id = cliente["id"]
    saldo = calcular_saldo(cliente_id)

    # Estado de cuenta derivado
    if saldo > 0:
        estado_cuenta = "Pendiente"
    elif saldo == 0:
        estado_cuenta = "Al corriente"
    else:
        estado_cuenta = "Saldo a favor"

    st.markdown(f"### CLIENTE: {cliente['nombre']}")
    st.write(f"Estado del Servicio: **{cliente['estado_servicio']}**")
    st.write(f"Estado de Cuenta: **{estado_cuenta}**")
    st.write(f"Adeudo Actual: **${saldo:.2f}**")

    st.divider()

    if cliente["tipo_cobro"] == "Medidor":
        render_medidor(cliente, saldo)
    else:
        render_fijo(cliente, saldo)


# =========================
# COBRO POR MEDIDOR
# =========================

def render_medidor(cliente, saldo):

    st.subheader("COBRO POR MEDIDOR")

    lectura_anterior = cliente["lectura_actual"]
    st.write("Lectura Anterior:", lectura_anterior)

    lectura_actual = st.number_input(
        "Lectura Actual",
        min_value=float(lectura_anterior),
        key="lectura_actual"
    )

    tarifa_m3 = cliente.get("tarifa_m3", 1)

    consumo = lectura_actual - lectura_anterior
    cargo = consumo * tarifa_m3

    st.write(f"Consumo: {consumo} m³")
    st.write(f"Cargo del periodo: ${cargo:.2f}")

    metodo = st.selectbox(
        "Método de Pago",
        ["Efectivo", "Transferencia"],
        key="metodo_medidor"
    )

    st.divider()

    if st.button("GENERAR PAGO Y RECIBO PDF", key="btn_medidor"):

        registrar_pago(cliente["id"], cargo, cargo, metodo)

        # actualizar lectura
        supabase.table("clientes") \
            .update({"lectura_actual": lectura_actual}) \
            .eq("id", cliente["id"]) \
            .execute()

        st.success("Pago registrado correctamente")
        st.rerun()

    if st.button("SUSPENDER SERVICIO", key="suspender_medidor"):
        suspender_servicio(cliente["id"])
        st.warning("Servicio suspendido")
        st.rerun()


# =========================
# COBRO TARIFA FIJA
# =========================

def render_fijo(cliente, saldo):

    st.subheader("COBRO TARIFA FIJA")

    meses = st.number_input(
        "Meses a pagar",
        min_value=1,
        value=1,
        key="meses"
    )

    tarifa = cliente["tarifa_mensual"]
    cargo = meses * tarifa

    st.write(f"Tarifa mensual: ${tarifa}")
    st.write(f"Cargo total: ${cargo:.2f}")

    metodo = st.selectbox(
        "Método de Pago",
        ["Efectivo", "Transferencia"],
        key="metodo_fijo"
    )

    st.divider()

    if st.button("GENERAR PAGO Y RECIBO PDF", key="btn_fijo"):

        registrar_pago(cliente["id"], cargo, cargo, metodo)

        st.success("Pago registrado correctamente")
        st.rerun()

    if st.button("SUSPENDER SERVICIO", key="suspender_fijo"):
        suspender_servicio(cliente["id"])
        st.warning("Servicio suspendido")
        st.rerun()

st.title("💧 Sistema de Clientes y Lecturas")

# ======================
# LAYOUT
# ======================
col1, col2 = st.columns([1, 2])

# ======================================================
# COLUMNA 1 — ALTA DE CLIENTE
# ======================================================
with col1:
    st.subheader("➕ Alta de Cliente")

    tipo_cobro = st.selectbox("Tipo de cobro", ["Fijo", "Medidor"])
    with st.form("form_cliente", clear_on_submit=True):
        nombre = st.text_input("Nombre *")
        codigo = st.text_input("Código *")
        telefono = st.text_input("Teléfono")
        correo = st.text_input("Correo")

        st.markdown("**Dirección**")
        calle = st.text_input("Calle")
        lote = st.text_input("Lote")
        manzana = st.text_input("Manzana")
        
        if tipo_cobro == "Fijo":
            tarifa = st.number_input("Tarifa fija mensual (solo si es Fijo)", min_value=0.0, step=10.0)
        elif tipo_cobro == "Medidor":
            precio_m = st.number_input("Precio x M cubico", min_value=0, step=10)
            lectura_i = st.number_input("Lectura Actual", min_value=0, step=10)
        
        guardar = st.form_submit_button("Guardar")

    if guardar:
        if not nombre or not codigo:
            st.error("Nombre y código son obligatorios")
        else:
            res = supabase.table("cliente").insert({
                "nombre": nombre,
                "codigo": codigo,
                "telefono": telefono,
                "correo": correo,
                "calle": calle,
                "lote": lote,
                "manzana": manzana,
                "tipo_cobro": tipo_cobro
            }).execute()

            cliente_id = res.data[0]["id"]

            # 2. Insertar estado (SIEMPRE)
            supabase.table("estado").insert({"estatus": "activo", "clientid": cliente_id, "saldo": 0, "adeudo": 0}).execute()
            
            # Si es fijo, inicializar tarifa
            if tipo_cobro == "Fijo" and tarifa is not None:
                supabase.table("fijo").insert({"clientid": cliente_id, "Tarifa": tarifa}).execute()
            elif tipo_cobro == "Medidor" and ((precio_m is not None) and (lectura_i is not None)):
                supabase.table("lectura").insert({"clientid": cliente_id, "precio_m": precio_m, "lectura_i": lectura_i, "lectura_a": lectura_i}).execute()

            st.success("Cliente creado correctamente")
            st.rerun()
with col2:
    # Buscar Clientes - Codigo
    st.subheader("Buscar Cliente")

    # Entrada del codigo
    codigo = st.text_input("Código de Cliente")

    # -----------------------------------------
    if st.button("Buscar Cliente"):

        cliente = obtener_cliente(codigo)

        if cliente is None:
            st.error("❌ El cliente no existe.")
        else:
            dialog_gestion(cliente)
        
    st.subheader("Tabla de Clientes")
    
    # Clientes
    clientes_data = supabase.table("cliente").select("*").execute().data
    df_clientes = pd.DataFrame(clientes_data)

    # Fijo
    fijo_data = supabase.table("fijo").select("*").execute().data
    df_fijo = pd.DataFrame(fijo_data)

    # Lectura
    lectura_data = supabase.table("lectura").select("*").execute().data
    df_lectura = pd.DataFrame(lectura_data)

    df = df_clientes.merge(
        df_fijo[["clientid", "tarifa"]],
        left_on="id",
        right_on="clientid",
        how="left"
    )
    
    df = df.merge(
        df_lectura[["clientid", "precio_m", "lectura_i", "lectura_a"]],
        left_on="id",
        right_on="clientid",
        how="left"
    )

    df.drop(columns=["clientid"], inplace=True, errors="ignore")

    df["consumo"] = df["lectura_a"] - df["lectura_i"]

    df["total_estimado"] = df.apply(
        lambda row: row["tarifa"] 
        if row["tipo_cobro"] == "Fijo"
        else row["consumo"] * row["precio_m"],
        axis=1
    )
    
    df_vista = df[["nombre", "codigo", "tipo_cobro", "consumo" ,"total_estimado"]].copy()

    df_vista["Estado Cuenta"] = df_vista["total_estimado"].apply(
        lambda x: "🟢 Sin deuda" if x == 0 else "🟡 Pendiente"
    )
    
    st.dataframe(df_vista, use_container_width=True)
