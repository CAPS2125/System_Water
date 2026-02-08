import streamlit as st
import pandas as pd
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
    ["Clientes", "Tipo de Servicios", "Servicios", "Lecturas", "Pagos"]
)

# ======================================================
# CLIENTES
# ======================================================
columnas_ui = [
    "nombre",
    "numero_cliente",
    "calle",
    "lote",
    "manzana",
    "telefono",
    "correo"
]

# =========================
# INIT CLIENTES DESDE SUPABASE
# =========================
if "clientes" not in st.session_state:
    response = supabase.table("clientes").select("*").execute()
    st.session_state["clientes"] = response.data or []

if st.session_state.menu == "Clientes":
    st.header("👤 Clientes")
    st.subheader("Agregar nuevo cliente")

    # =========================
    # FORMULARIO
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre *")
        numero_cliente = st.text_input("Número de cliente *")
        telefono = st.text_input("Teléfono")

    with col2:
        correo = st.text_input("Correo electrónico")
        calle = st.text_input("Calle *")

        col_lote, col_manzana = st.columns(2)
        with col_lote:
            lote = st.text_input("Lote")
        with col_manzana:
            manzana = st.text_input("Manzana")

    if st.button("Agregar cliente"):
        if not nombre or not numero_cliente or not calle:
            st.error("❌ Campos obligatorios: Nombre, Número de cliente y Dirección")
        else:
            # 1️⃣ Verificar si ya existe el número de cliente
            existente = (
                supabase
                .table("clientes")
                .select("id")
                .eq("numero_cliente", numero_cliente)
                .execute()
                .data
            )

            if existente:
                st.warning(
                    f"⚠️ Ya existe un cliente con el número {numero_cliente}"
                )
            else:
                nuevo_cliente = {
                    "nombre": nombre,
                    "numero_cliente": numero_cliente,
                    "calle": calle,
                    "lote": lote,
                    "manzana": manzana,
                    "telefono": telefono,
                    "correo": correo
                }

                supabase.table("clientes").insert(nuevo_cliente).execute()

                # 2️⃣ Mantener frontend en sync
                st.session_state["clientes"].append(nuevo_cliente)

                st.success("✅ Cliente registrado correctamente")
                st.rerun()

    # =========================
    # TABLA DE ESTADO DEL SISTEMA
    # =========================
    st.divider()
    st.subheader("📋 Clientes registrados en el sistema")

    df_clientes = pd.DataFrame(st.session_state.get("clientes", []))

    if df_clientes.empty:
        st.info("Aún no hay clientes registrados")
    else:
        columnas_presentes = [c for c in columnas_ui if c in df_clientes.columns]
        df_clientes = df_clientes[columnas_presentes]
        st.dataframe(df_clientes, use_container_width=True)

# ======================================================
# TIPO DE SERVICIOS
# ======================================================
elif st.session_state.menu == "Tipo de Servicios":
    st.header("🧾 Tipo de Servicios")

    # 🔹 ESTE SELECTBOX DEBE IR FUERA DEL FORM
    tipo = st.selectbox(
        "Tipo de servicio",
        ["FIJO", "MEDIDO"],
        key="tipo_servicio_selector"
    )

    with st.form("form_tipo_servicio"):
        col1, col2 = st.columns(2)

        nombre = col1.text_input("Nombre del servicio *")
        activo = col2.checkbox("Activo", value=True)

        st.divider()

        # =========================
        # CAMPOS CONDICIONALES
        # =========================
        if tipo == "FIJO":
            tarifa_fija = st.number_input(
                "Tarifa fija ($)",
                min_value=0.0,
                step=1.0
            )
            precio_m3 = None

        else:  # MEDIDO
            precio_m3 = st.number_input(
                "Precio por m³ ($)",
                min_value=0.0,
                step=0.01
            )
            tarifa_fija = None

        submitted = st.form_submit_button("Guardar servicio")

        if submitted:
            # =========================
            # VALIDACIONES
            # =========================
            if not nombre:
                st.error("❌ El nombre es obligatorio")

            elif tipo == "FIJO" and tarifa_fija <= 0:
                st.error("❌ La tarifa fija debe ser mayor a 0")

            elif tipo == "MEDIDO" and precio_m3 <= 0:
                st.error("❌ El precio por m³ debe ser mayor a 0")

            else:
                payload = {
                    "nombre": nombre,
                    "tipo": tipo,
                    "tarifa_fija": tarifa_fija,
                    "precio_m3": precio_m3,
                    "activo": activo
                }

                supabase.table("catalogo_servicios").insert(payload).execute()
                st.success("✅ Tipo de servicio registrado correctamente")
                st.toast("Servicio guardado con éxito", icon="🎉")

# ======================================================
# SERVICIOS
# ======================================================
elif st.session_state.menu == "Servicios":
    st.header("🧾 Asignar Servicio a Cliente")

    # ======================
    # DATOS BASE
    # ======================
    clientes = supabase.table("clientes").select("id, nombre").execute().data
    tipos_servicio = supabase.table("tipos_servicio").select("*").execute().data
    catalogo = supabase.table("catalogo_servicios").select("*").execute().data

    if not clientes:
        st.warning("No hay clientes registrados")
        st.stop()

    if not tipos_servicio:
        st.warning("No hay tipos de servicio configurados")
        st.stop()

    # ======================
    # SELECTS BASE
    # ======================
    cliente_nombre = st.selectbox(
        "Cliente",
        [c["nombre"] for c in clientes]
    )

    tipo_nombre = st.selectbox(
        "Tipo de servicio",
        [t["nombre"] for t in tipos_servicio]
    )

    # ======================
    # OBTENER TIPO REAL (SIN MAPEO ROTO)
    # ======================
    tipo_actual = next(
        t for t in tipos_servicio if t["nombre"] == tipo_nombre
    )

    # ======================
    # FILTRAR CATÁLOGO SEGÚN TIPO
    # ======================
    if tipo_actual["usa_catalogo_fijo"]:
        catalogo_filtrado = [
            s for s in catalogo if s["tipo"] == "FIJO"
        ]
    elif tipo_actual["usa_medidor"]:
        catalogo_filtrado = [
            s for s in catalogo if s["tipo"] == "MEDIDO"
        ]
    else:
        catalogo_filtrado = []

    if not catalogo_filtrado:
        st.warning("No hay servicios disponibles para este tipo")
        st.stop()

    servicio_nombre = st.selectbox(
        "Servicio",
        [s["nombre"] for s in catalogo_filtrado]
    )

    servicio_actual = next(
        s for s in catalogo_filtrado if s["nombre"] == servicio_nombre
    )

    fecha_inicio = st.date_input(
        "Fecha de inicio del servicio"
    )

    fecha_final = st.date_input(
        "Fecha de final del servicio"
    )

    # ======================
    # FORMULARIO (SOLO SUBMIT)
    # ======================
    with st.form("form_asignar_servicio"):
        st.markdown("### Confirmar asignación")

        if tipo_actual["usa_catalogo_fijo"]:
            st.info(f"Tarifa fija: ${servicio_actual['tarifa_fija']}")

        if tipo_actual["usa_medidor"]:
            st.info(f"Precio por m³: ${servicio_actual['precio_m3']}")

        submitted = st.form_submit_button("Asignar servicio")

    # ======================
    # LÓGICA DE NEGOCIO
    # ======================
    if submitted:
        cliente_actual = next(
            c for c in clientes if c["nombre"] == cliente_nombre
        )

        nuevo_servicio = {
            "cliente_id": cliente_actual["id"],
            "tipos_servicio_id": tipo_actual["id"],
            "tipo": tipo_actual["nombre"],
            "tarifa_fija": servicio_actual["tarifa_fija"] if tipo_actual["usa_catalogo_fijo"] else None,
            "precio_m3": servicio_actual["precio_m3"] if tipo_actual["usa_medidor"] else None,
            "estado": "ACTIVO",
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_final": fecha_inicio.isoformat()
        }

        supabase.table("servicios").insert(nuevo_servicio).execute()
        st.success("✅ Servicio asignado correctamente al cliente")

# ======================================================
# LECTURAS
# ======================================================
elif st.session_state.menu == "Lecturas":
    st.header("📊 Toma de Lecturas (Servicios Medidos)")

    # ======================
    # CLIENTES CON SERVICIO MEDIDO ACTIVO
    # ======================
    servicios_medidos = supabase.table("servicios") \
        .select("id, cliente_id, precio_m3, estado, clientes(nombre)") \
        .eq("tipo", "MEDIDO") \
        .eq("estado", "ACTIVO") \
        .execute().data

    if not servicios_medidos:
        st.info("No hay servicios medidos activos")
        st.stop()

    servicio_map = {
        f"{s['clientes']['nombre']}": s
        for s in servicios_medidos
    }

    # ======================
    # FORMULARIO
    # ======================
    with st.form("form_lectura"):

        cliente_nombre = st.selectbox(
            "Cliente",
            servicio_map.keys()
        )

        fecha_lectura = st.date_input(
            "Fecha de lectura"
        )

        lectura_actual = st.number_input(
            "Lectura actual",
            min_value=0.0
        )

        submitted = st.form_submit_button("Registrar lectura")

    # ======================
    # LÓGICA
    # ======================
    if submitted:

        servicio = servicio_map[cliente_nombre]

        # Última lectura
        ultima_lectura = supabase.table("lecturas") \
            .select("lectura_actual, saldo_actual") \
            .eq("servicio_id", servicio["id"]) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute().data

        lectura_anterior = ultima_lectura[0]["lectura_actual"] if ultima_lectura else 0
        saldo_anterior = ultima_lectura[0]["saldo_actual"] if ultima_lectura else 0

        if lectura_actual <= lectura_anterior:
            st.error("❌ La lectura actual debe ser mayor a la anterior")
            st.stop()

        consumo = lectura_actual - lectura_anterior
        importe = consumo * servicio["precio_m3"]
        saldo_actual = saldo_anterior + importe

        nueva_lectura = {
            "cliente_id": servicio["cliente_id"],
            "servicio_id": servicio["id"],
            "fecha_lectura": fecha_lectura.isoformat(),
            "lectura_anterior": lectura_anterior,
            "lectura_actual": lectura_actual,
            "consumo": consumo,
            "precio_m3": servicio["precio_m3"],
            "importe": importe,
            "saldo_anterior": saldo_anterior,
            "saldo_actual": saldo_actual
        }

        supabase.table("lecturas").insert(nueva_lectura).execute()

        st.success(f"✅ Lectura registrada. Importe: ${importe:.2f}")

# ======================================================
# PAGOS
# ======================================================
elif st.session_state.menu == "Pagos":
    st.header("💳 Registro de Pagos")

    # ======================
    # CLIENTES CON SALDO
    # ======================
    ultimos_saldos = supabase.table("lecturas") \
        .select("cliente_id, servicio_id, saldo_actual, clientes(nombre)") \
        .order("created_at", desc=True) \
        .execute().data

    saldo_map = {}
    for r in ultimos_saldos:
        if r["cliente_id"] not in saldo_map:
            saldo_map[r["cliente_id"]] = r

    if not saldo_map:
        st.info("No hay clientes con saldo registrado")
        st.stop()

    cliente_map = {
        r["clientes"]["nombre"]: r
        for r in saldo_map.values()
    }

    # ======================
    # FORMULARIO
    # ======================
    with st.form("form_pago"):

        cliente_nombre = st.selectbox(
            "Cliente",
            cliente_map.keys()
        )

        # Definir saldo actual del cliente seleccionado
        saldo_actual = cliente_map[cliente_nombre]["saldo_actual"]
        st.info(f"Saldo actual del cliente: ${saldo_actual:.2f}")

        meses = st.number_input(
            "Meses a pagar",
            min_value=1,
            step=1
        )

        # Calcular monto automáticamente según meses
        tarifa_mensual = saldo_actual / max(meses, 1)
        monto_pagado = tarifa_mensual * meses
        st.write(f"Monto a pagar calculado: ${monto_pagado:.2f}")

        metodo = st.selectbox(
            "Método de pago",
            ["EFECTIVO", "TRANSFERENCIA", "TARJETA"]
        )

        submitted = st.form_submit_button("Registrar pago")

    # ======================
    # LÓGICA
    # ======================
    if submitted:
        data = cliente_map[cliente_nombre]
        saldo_anterior = data["saldo_actual"]

        # Validar que no se pague más del saldo
        if monto_pagado > saldo_anterior:
            st.error("El monto a pagar no puede ser mayor al saldo actual.")
        else:
            nuevo_saldo = saldo_anterior - monto_pagado

            nuevo_pago = {
                "cliente_id": data["cliente_id"],
                "servicio_id": data["servicio_id"],
                "fecha_pago": date.today().isoformat(),
                "meses_pagados": meses,
                "monto_pagado": monto_pagado,
                "saldo_anterior": saldo_anterior,
                "saldo_actual": nuevo_saldo,
                "metodo_pago": metodo
            }

            supabase.table("pagos").insert(nuevo_pago).execute()

            st.success(f"✅ Pago registrado. Nuevo saldo: ${nuevo_saldo:.2f}")
