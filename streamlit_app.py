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

        saldo = float(total_cargos) - float(total_pagos)
        return round(saldo, 2)

    except Exception as e:
        print("Error en calcular_saldo:", e)
        return 0.0

# =========================
# DIALOG PRINCIPAL
# =========================

@st.dialog("Gestión de Gastos")
def dialog_gestion(cliente):
    saldo = calcular_saldo(cliente["id"])

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
        render_medidor(cliente)
    else:
        render_fijo(cliente)

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
def render_fijo(cliente):
    st.subheader("COBRO TARIFA FIJA")

    meses = st.number_input("Meses a pagar", min_value=1, value=1)

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
    cargo = meses * tarifa

    st.write(f"Tarifa mensual: ${tarifa}")
    st.write(f"Cargo total: ${cargo:.2f}")

    metodo = st.selectbox(
        "Método de Pago",
        ["Efectivo", "Transferencia"]
    )

    st.divider()

    col1, col2 = st.columns(2)

    # -------- BOTÓN GENERAR PAGO --------
    with col1:
        if st.button("GENERAR PAGO"):
            try:
                insert_response = (
                    supabase
                    .table("pagos")
                    .insert({
                        "cargo_generado": cargo,
                        "pago_realizado": cargo,  # aquí se paga completo
                        "metodo_pago": metodo,
                        "clientid": cliente["id"]
                    })
                    .execute()
                )

                if insert_response.data:
                    st.success("Pago registrado correctamente ✅")

                    saldo_actual = calcular_saldo(cliente["id"])
                    st.info(f"Saldo actual: ${saldo_actual:.2f}")

                else:
                    st.error("No se pudo registrar el pago.")

            except Exception as e:
                st.error(f"Error al registrar pago: {e}")

    # -------- BOTÓN SUSPENDER --------
    with col2:
        if st.button("SUSPENDER SERVICIO"):
            st.warning("Función de suspensión aún no implementada.")
        
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

    df["Total $"] = df.apply(
        lambda row: row["tarifa"] 
        if row["tipo_cobro"] == "Fijo"
        else row["consumo"] * row["precio_m"],
        axis=1
    )
    
    df_vista = df[["nombre", "codigo", "tipo_cobro", "consumo" , "Total $"]].copy()

    df_vista["Estado Cuenta"] = df_vista["total_estimado"].apply(
        lambda x: "🟢 Sin deuda" if x == 0 else "🟡 Pendiente"
    )
    
    st.dataframe(df_vista, use_container_width=True)
