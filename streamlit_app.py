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

# ======================================================
# OBTENER CLIENTE
# ======================================================

def obtener_cliente(codigo):
    response = (
        supabase
        .table("cliente")
        .select("*")
        .eq("codigo", codigo)
        .execute()
    )

    return response.data[0] if response.data else None


# ======================================================
# CALCULAR SALDO
# ======================================================

def calcular_saldo(cliente_id):
    try:
        response = (
            supabase
            .table("pagos")
            .select("cargo_generado, pago_realizado")
            .eq("clientid", cliente_id)
            .execute()
        )

        if not response.data:
            return 0.0

        total_cargos = sum(float(p.get("cargo_generado", 0) or 0) for p in response.data)
        total_pagos = sum(float(p.get("pago_realizado", 0) or 0) for p in response.data)

        # Convención global del sistema:
        # Saldo > 0  → Debe
        # Saldo = 0  → Al corriente
        # Saldo < 0  → Saldo a favor
        saldo = total_cargos - total_pagos

        return round(saldo, 2)

    except Exception as e:
        print(f"Error calculando saldo: {e}")
        return 0.0


# ======================================================
# GENERAR CARGOS MENSUALES
# ======================================================

def generar_cargos_mensuales():
    """Genera cargos fijos para todos los clientes con tipo_cobro='Fijo'"""
    try:
        clientes = (
            supabase
            .table("cliente")
            .select("*")
            .eq("tipo_cobro", "Fijo")
            .execute()
            .data
        )

        for cliente in clientes:

            fijo_response = (
                supabase
                .table("fijo")
                .select("tarifa")
                .eq("clientid", cliente["id"])
                .execute()
            )

            if fijo_response.data:
                tarifa = float(fijo_response.data[0]["tarifa"])

                supabase.table("pagos").insert({
                    "cargo_generado": tarifa,
                    "pago_realizado": 0,
                    "clientid": cliente["id"]
                }).execute()

        print("Cargos mensuales generados")

    except Exception as e:
        print(f"Error generando cargos: {e}")


# ======================================================
# DIALOG GESTIÓN
# ======================================================

@st.dialog("Gestión de Gastos")
def dialog_gestion(cliente):

    saldo = calcular_saldo(cliente["id"])

    if saldo > 0:
        estado_cuenta = "Pendiente"
        etiqueta_saldo = "Adeudo Actual"
        monto_f = f"${saldo:,.2f}"
    elif saldo == 0:
        estado_cuenta = "Al corriente"
        etiqueta_saldo = "Saldo"
        monto_f = "$0.00"
    else:
        estado_cuenta = "Saldo a favor"
        etiqueta_saldo = "Saldo a Favor"
        monto_f = f"${abs(saldo):,.2f}"

    st.markdown(f"### CLIENTE: {cliente['nombre']}")
    st.write(f"Estado de Cuenta: **{estado_cuenta}**")
    st.write(f"{etiqueta_saldo}: **{monto_f}**")

    st.divider()

    if cliente["tipo_cobro"] == "Medidor":
        render_medidor(cliente)
    else:
        render_fijo(cliente)


# ======================================================
# COBRO POR MEDIDOR
# ======================================================

def render_medidor(cliente):

    st.subheader("COBRO POR MEDIDOR")

    lectura_res = (
        supabase
        .table("lectura")
        .select("*")
        .eq("clientid", cliente["id"])
        .execute()
    )

    if not lectura_res.data:
        st.error("No se encontraron datos de lectura para este cliente.")
        return

    datos_l = lectura_res.data[0]
    lectura_anterior = datos_l["lectura_a"]
    precio_m3 = datos_l["precio_m"]

    st.info(f"Lectura Anterior registrada: **{lectura_anterior} m³**")

    lectura_actual = st.number_input(
        "Lectura Actual",
        min_value=float(lectura_anterior),
        value=float(lectura_anterior)
    )

    consumo = lectura_actual - lectura_anterior
    cargo_periodo = consumo * precio_m3

    st.write(f"Consumo del periodo: **{consumo} m³**")
    st.write(f"Cargo por consumo: **${cargo_periodo:.2f}**")

    metodo = st.selectbox("Método de Pago", ["Efectivo", "Transferencia"])
    monto_pagado = st.number_input("Monto que entrega el cliente", min_value=0.0, value=float(cargo_periodo))

    if st.button("GENERAR PAGO Y ACTUALIZAR LECTURA"):

        try:

            # Registrar cargo
            if cargo_periodo > 0:
                supabase.table("pagos").insert({
                    "clientid": cliente["id"],
                    "cargo_generado": cargo_periodo,
                    "pago_realizado": 0,
                    "metodo_pago": "Sistema"
                }).execute()

            # Registrar pago
            if monto_pagado > 0:
                supabase.table("pagos").insert({
                    "clientid": cliente["id"],
                    "cargo_generado": 0,
                    "pago_realizado": monto_pagado,
                    "metodo_pago": metodo
                }).execute()

            # Actualizar lectura
            supabase.table("lectura").update({
                "lectura_i": lectura_anterior,
                "lectura_a": lectura_actual
            }).eq("clientid", cliente["id"]).execute()

            st.success("Lectura y Pago registrados correctamente ✅")
            st.rerun()

        except Exception as e:
            st.error(f"Error al procesar: {e}")


# ======================================================
# COBRO TARIFA FIJA
# ======================================================

def render_fijo(cliente):

    st.subheader("COBRO TARIFA FIJA")

    saldo_actual = calcular_saldo(cliente["id"])

    if saldo_actual > 0:
        st.error(f"Adeudo Actual: ${saldo_actual:,.2f}")
    elif saldo_actual < 0:
        st.info(f"Saldo a Favor: ${abs(saldo_actual):,.2f}")

    fijo_res = (
        supabase
        .table("fijo")
        .select("tarifa")
        .eq("clientid", cliente["id"])
        .execute()
    )

    tarifa = float(fijo_res.data[0]["tarifa"]) if fijo_res.data else 0.0

    pagar_adeudo = st.checkbox("Liquidar adeudo anterior", value=(saldo_actual > 0))
    pagar_meses = st.number_input("Meses a pagar (nuevos)", min_value=0, value=1 if saldo_actual <= 0 else 0)

    adeudo_visual = saldo_actual if saldo_actual > 0 else 0.0

    total_a_pagar = (adeudo_visual if pagar_adeudo else 0.0) + (pagar_meses * tarifa)

    st.markdown(f"### Total a recibir: `${total_a_pagar:,.2f}`")

    if st.button("REGISTRAR PAGO"):

        if total_a_pagar > 0:
            supabase.table("pagos").insert({
                "cargo_generado": 0,
                "pago_realizado": total_a_pagar,
                "clientid": cliente["id"]
            }).execute()

            st.success("Pago registrado")
            st.rerun()


# ======================================================
# OBTENER SALDO SEGURO
# ======================================================

def obtener_saldo_seguro(cliente_id):
    try:
        return calcular_saldo(cliente_id)
    except Exception as e:
        print(f"Error obteniendo saldo para {cliente_id}: {e}")
        return 0.0


# ======================================================
# CARGAR TABLA CLIENTES
# ======================================================

def cargar_tabla_clientes():

    clientes_data = supabase.table("cliente").select("*").execute().data
    fijo_data = supabase.table("fijo").select("clientid, tarifa").execute().data
    lectura_data = supabase.table("lectura").select("clientid, precio_m, lectura_i, lectura_a").execute().data
    pagos_data = supabase.table("pagos").select("clientid, cargo_generado, pago_realizado").execute().data

    df = pd.DataFrame(clientes_data)
    df_fijo = pd.DataFrame(fijo_data)
    df_lectura = pd.DataFrame(lectura_data)
    df_pagos = pd.DataFrame(pagos_data)

    if not df_pagos.empty:

        df_pagos["cargo_generado"] = pd.to_numeric(df_pagos["cargo_generado"], errors="coerce").fillna(0)
        df_pagos["pago_realizado"] = pd.to_numeric(df_pagos["pago_realizado"], errors="coerce").fillna(0)

        saldos_df = (
            df_pagos
            .groupby("clientid", as_index=False)
            .agg({
                "cargo_generado": "sum",
                "pago_realizado": "sum"
            })
        )

        saldos_df["Saldo"] = saldos_df["cargo_generado"] - saldos_df["pago_realizado"]
        saldos_df = saldos_df[["clientid", "Saldo"]]

    else:
        saldos_df = pd.DataFrame(columns=["clientid", "Saldo"])

    df = df.merge(df_fijo, left_on="id", right_on="clientid", how="left")
    df = df.merge(df_lectura, left_on="id", right_on="clientid", how="left", suffixes=('', '_l'))
    df = df.merge(saldos_df, left_on="id", right_on="clientid", how="left")

    df["Saldo"] = df["Saldo"].fillna(0.0).round(2)
    df["Consumo"] = (df["lectura_a"] - df["lectura_i"]).fillna(0)

    df["Total $"] = df.apply(
        lambda row: row["tarifa"] if row["tipo_cobro"] == "Fijo"
        else row["Consumo"] * (row["precio_m"] or 0),
        axis=1
    )

    df_vista = df[["nombre", "codigo", "tipo_cobro", "Consumo", "Total $", "Saldo"]].copy()

    df_vista["Estado Cuenta"] = df_vista["Saldo"].apply(
        lambda x: "🔴 Pendiente" if x > 0
        else ("🟢 Al corriente" if x == 0
        else "🔵 Saldo a favor")
    )

    return df_vista

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
        estado_servicio = st.selectbox("Estado del Servicio", ["Activo", "Suspendido"])
        
        st.markdown("**Dirección**")
        calle = st.text_input("Calle")
        lote = st.text_input("Lote")
        manzana = st.text_input("Manzana")

        st.markdown("**Cobro**")
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
                "tipo_cobro": tipo_cobro,
                "estado_servicio": estado_servicio
            }).execute()

            cliente_id = res.data[0]["id"]
           
            # Si es fijo, inicializar tarifa
            if tipo_cobro == "Fijo" and tarifa is not None:
                supabase.table("fijo").insert({"clientid": cliente_id, "tarifa": tarifa}).execute()
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
    
    # Cargar tabla actualizada
    df_vista = cargar_tabla_clientes()
    st.dataframe(df_vista, use_container_width=True)
