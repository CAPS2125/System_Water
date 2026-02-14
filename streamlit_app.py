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

def obtener_cliente(codigo):
    response = supabase.table("cliente") \
        .select("*") \
        .eq("codigo", codigo) \
        .execute()

    return response.data[0] if response.data else None

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

        total_cargos = sum(p.get("cargo_generado", 0) or 0 for p in response.data)
        total_pagos = sum(p.get("pago_realizado", 0) or 0 for p in response.data)

        saldo = total_cargos - total_pagos
        return round(saldo, 2)

    except Exception as e:
        print("Error en calcular_saldo:", e)
        return 0.0

# ========== GENERA CARGOS MENSUALES ==========
def generar_cargos_mensuales():
    """Genera cargos fijos para todos los clientes con tipo_cobro='Fijo'"""
    try:
        clientes = supabase.table("cliente").select("*").eq("tipo_cobro", "Fijo").execute().data
        
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

# =========================
# DIALOG PRINCIPAL
# =========================

@st.dialog("Gestión de Gastos")
def dialog_gestion(cliente):
    saldo = calcular_saldo(cliente["id"])

    if saldo > 0:
        estado_cuenta = "Pendiente"
        etiqueta_saldo = "Adeudo Actual"
    elif saldo == 0:
        estado_cuenta = "Al corriente"
        etiqueta_saldo = "Saldo"
    else:
        estado_cuenta = "Saldo a favor"
        etiqueta_saldo = "Saldo a Favor"
    
    st.markdown(f"### CLIENTE: {cliente['nombre']}")
    st.write(f"Estado del Servicio: **{cliente['estado_servicio']}**")
    
    saldo_placeholder = st.empty()
    saldo_placeholder.write(f"Estado de Cuenta: **{estado_cuenta}**")
    saldo_placeholder.write(f"{etiqueta_saldo}: **${abs(saldo):.2f}**")
    
    st.divider()
    if cliente["tipo_cobro"] == "Medidor":
        render_medidor(cliente)
    else:
        render_fijo(cliente, saldo_placeholder)

# =========================
# COBRO POR MEDIDOR (MOCK)
# =========================

def render_medidor(cliente):

    st.subheader("COBRO POR MEDIDOR")

    lectura_anterior = cliente["lectura_actual"]
    st.write("Lectura Anterior:", lectura_anterior)

    lectura_actual = st.number_input(
        "Lectura Actual",
        min_value=float(lectura_anterior),
        value=float(lectura_anterior)
    )

    consumo = lectura_actual - lectura_anterior
    cargo = consumo * cliente["tarifa_m3"]

    st.write(f"Consumo: {consumo} m³")
    st.write(f"Cargo del periodo: ${cargo:.2f}")

    metodo = st.selectbox(
        "Método de Pago",
        ["Efectivo", "Transferencia"]
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.button("GENERAR PAGO Y RECIBO PDF (Mock)")

    with col2:
        st.button("SUSPENDER SERVICIO (Mock)")


# =========================
# COBRO TARIFA FIJA
# =========================
def render_fijo(cliente, saldo_placeholder):
    st.subheader("COBRO TARIFA FIJA")

    # ADEUDO ACTUAL
    saldo_actual = calcular_saldo(cliente["id"])
    st.write(f"**Adeudo Actual: ${abs(saldo_actual):.2f}**")
    
    # Obtener tarifa
    fijo_response = (
        supabase
        .table("fijo")
        .select("tarifa")
        .eq("clientid", cliente["id"])
        .execute()
    )

    if not fijo_response.data:
        st.error("No se encontró tarifa fija para este cliente.")
        return

    tarifa = float(fijo_response.data[0]["tarifa"])
    st.write(f"Tarifa mensual: ${tarifa:.2f}")

    # EL USUARIO ELIGE QUÉ PAGAR
    st.markdown("**¿Qué deseas pagar?**")
    
    pagar_adeudo = st.checkbox("Pagar adeudo actual", value=True if saldo_actual > 0 else False)
    pagar_meses = st.number_input("Meses a pagar (nuevos)", min_value=0, value=1)

    # CALCULAR TOTAL A PAGAR
    total_a_pagar = 0.0
    if pagar_adeudo:
        total_a_pagar += max(0, saldo_actual)
    total_a_pagar += pagar_meses * tarifa

    st.write(f"**Total a pagar: ${total_a_pagar:.2f}**")

    metodo = st.selectbox(
        "Método de Pago",
        ["Efectivo", "Transferencia"]
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("GENERAR PAGO"):
            if total_a_pagar <= 0:
                st.error("El monto a pagar debe ser mayor a 0")
                return
                
            try:
                insert_response = (
                    supabase
                    .table("pagos")
                    .insert({
                        "cargo_generado": 0,
                        "pago_realizado": total_a_pagar,
                        "metodo_pago": metodo,
                        "clientid": cliente["id"]
                    })
                    .execute()
                )

                if insert_response.data:
                    st.success("Pago registrado correctamente ✅")
                    
                    nuevo_saldo = calcular_saldo(cliente["id"])
                    
                    if nuevo_saldo > 0:
                        estado_nuevo = "Pendiente"
                        etiqueta_saldo = "Adeudo Actual"
                    elif nuevo_saldo == 0:
                        estado_nuevo = "Al corriente"
                        etiqueta_saldo = "Saldo"
                    else:
                        estado_nuevo = "Saldo a favor"
                        etiqueta_saldo = "Saldo a Favor"
                    
                    saldo_placeholder.empty()
                    saldo_placeholder.write(f"Estado de Cuenta: **{estado_nuevo}**")
                    saldo_placeholder.write(f"{etiqueta_saldo}: **${abs(nuevo_saldo):.2f}**")
                    
                else:
                    st.error("No se pudo registrar el pago.")

            except Exception as e:
                st.error(f"Error al registrar pago: {e}")

    with col2:
        if st.button("SUSPENDER SERVICIO"):
            st.warning("Función de suspensión aún no implementada.")

# ========== OBTENER SALDO SEGURO ==========
def obtener_saldo_seguro(cliente_id):
    try:
        saldo = calcular_saldo(cliente_id)
        return saldo
    except Exception as e:
        print(f"Error obteniendo saldo para {cliente_id}: {e}")
        return 0.0

# ========== CARGAR TABLA CLIENTES ==========
def cargar_tabla_clientes():
    """Carga y retorna la tabla de clientes con saldo actualizado"""
    
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

    df["Consumo"] = df["lectura_a"] - df["lectura_i"]

    df["Total $"] = df.apply(
        lambda row: row["tarifa"] 
        if row["tipo_cobro"] == "Fijo"
        else row["Consumo"] * row["precio_m"],
        axis=1
    )
    
    # Calcular saldo real desde tabla pagos
    df["Saldo"] = df["id"].apply(obtener_saldo_seguro)
    
    df_vista = df[["nombre", "codigo", "tipo_cobro", "Consumo", "Total $", "Saldo"]].copy()

    df_vista["Estado Cuenta"] = df_vista["Saldo"].apply(
        lambda x: "🟡 Pendiente" if x > 0 else ("🟢 Al corriente" if x == 0 else "🟢 Saldo a favor")
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
