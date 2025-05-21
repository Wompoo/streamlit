import streamlit as st
import os
import pandas as pd
import itertools
import io
import altair as alt




CSV_MENSUAL = "CSV_Mensuales"
CSV_ANUAL = "CSV_Anuales"
CARPETAS_MENSUALES = ["ccaa", "canal", "sociodem"]

def key_safe(*args):
    return "_".join(str(a).replace(" ", "_").replace(".", "_").replace("/", "_") for a in args)

st.set_page_config(page_title="Comparador de Alimentos", layout="wide")
st.title("\U0001F4CA Comparador por Alimentos")

# Crear pestañas arriba
tab_datos_generales, tab_tam_ytd = st.tabs(["📋 Datos Generales", "📊 YTD / TAM  "])

# Variables para acumular datos y selección de usuario
seleccion_usuario = {}
df_acumulado_total = pd.DataFrame()
meses_ordenados = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]

with tab_datos_generales:
    st.subheader("1️⃣ Selecciona una fuente")
    fuente_seleccionada = st.selectbox("Fuente", options=CARPETAS_MENSUALES)

    if not fuente_seleccionada:
        st.stop()

    estructura = {}
    regiones_mensuales = {}
    categorias_mensuales = {}

    carpeta_path = os.path.join(CSV_MENSUAL, fuente_seleccionada)
    if not os.path.exists(carpeta_path):
        st.error(f"No se encontró la carpeta {carpeta_path}")
        st.stop()

    for f in os.listdir(carpeta_path):
        if f.endswith(".csv"):
            partes = f.replace(".csv", "").split("_")
            if len(partes) >= 3:
                anio = partes[0]
                mes = partes[2].capitalize()
                estructura.setdefault(anio, set()).add(mes)
                if fuente_seleccionada == "ccaa" and len(partes) > 3:
                    region = "_".join(partes[3:])
                    regiones_mensuales.setdefault(anio, set()).add(region)
                elif fuente_seleccionada in ["canal", "sociodem"] and len(partes) > 3:
                    categoria = "_".join(partes[3:])
                    categorias_mensuales.setdefault(anio, set()).add(categoria)

    def buscar_csv(anio, mes_lower, region, fuente, carpeta):
        for f in os.listdir(carpeta):
            if f.endswith(".csv"):
                partes = f.replace(".csv", "").split("_")
                if len(partes) >= 4:
                    if partes[0] == anio and partes[1] == fuente and partes[2].lower() == mes_lower:
                        if "_".join(partes[3:]) == region:
                            return f
        return None

    def detectar_separador(path, num_lineas=5):
        posibles = [',', ';', '\t', '|']
        with open(path, 'r', encoding='utf-8') as f:
            lineas = list(itertools.islice(f, num_lineas))
        if not lineas:
            return ','
        mejor, max_cnt = None, 0
        for sep in posibles:
            cnt = sum(line.count(sep) for line in lineas) / len(lineas)
            if cnt > max_cnt:
                mejor, max_cnt = sep, cnt
        return mejor or ','

    def mostrar_alimentos_paginados(alimentos, anio, mes, region_o_cat, nivel, pagina_actual, items_por_pagina=8):
        nivel_str = str(nivel).replace(".", "_")
        filtro = st.text_input(f"\U0001F50D Buscar alimento en Nivel {nivel}:", key=key_safe("buscador", anio, mes, region_o_cat, nivel_str))
        if filtro:
            alimentos = [a for a in alimentos if filtro.lower() in a.lower()]
        total = len(alimentos)
        total_paginas = (total - 1) // items_por_pagina + 1 if total > 0 else 1
        pagina_actual = min(max(pagina_actual, 0), total_paginas - 1)
        inicio = pagina_actual * items_por_pagina
        fin = inicio + items_por_pagina
        alimentos_pagina = alimentos[inicio:fin]
        cols = st.columns(2)
        seleccionados_pagina = []
        for i, alimento in enumerate(alimentos_pagina):
            col = cols[i % 2]
            with col:
                key = key_safe("chk", anio, mes, region_o_cat, nivel_str, alimento)
                if key not in st.session_state:
                    st.session_state[key] = False
                chk_alimento = st.checkbox(f"\U0001F374 {alimento}", key=key)
                if chk_alimento:
                    seleccionados_pagina.append(alimento)
        key_global = key_safe("seleccion", anio, mes, region_o_cat, nivel_str)
        st.session_state[key_global] = set(st.session_state.get(key_global, set()))
        for a in seleccionados_pagina:
            st.session_state[key_global].add(a)
        for alimento in alimentos_pagina:
            key = key_safe("chk", anio, mes, region_o_cat, nivel_str, alimento)
            if not st.session_state[key] and alimento in st.session_state[key_global]:
                st.session_state[key_global].remove(alimento)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if pagina_actual > 0:
                if st.button("⬅️ Anterior", key=key_safe("prev_page", anio, mes, region_o_cat, nivel_str)):
                    return None, pagina_actual - 1
        with col2:
            st.markdown(f"**Página {pagina_actual + 1} de {total_paginas}**")
        with col3:
            if pagina_actual < total_paginas - 1:
                if st.button("Siguiente ➡️", key=key_safe("next_page", anio, mes, region_o_cat, nivel_str)):
                    return None, pagina_actual + 1
        return None, pagina_actual

    st.subheader("2️⃣ Selecciona meses")
    meses_años = {}
    for anio, meses in estructura.items():
        for mes in meses:
            meses_años.setdefault(mes, set()).add(anio)

    meses_ordenados = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]

    for mes in sorted(meses_años.keys(), key=lambda x: meses_ordenados.index(x.lower())):
        with st.expander(f"{mes}", expanded=False):
            años_disponibles = sorted(meses_años[mes])
            años_seleccionados = st.multiselect(f"Selecciona uno o más años para {mes}", options=años_disponibles, default=años_disponibles, key=key_safe("anios", mes))
            carpeta_mensual_path = os.path.join(CSV_MENSUAL, fuente_seleccionada)
            for anio_seleccionado in años_seleccionados:
                st.markdown(f"---\n### Año {anio_seleccionado}")
                opciones_region_o_cat = sorted(categorias_mensuales.get(anio_seleccionado, [])) if fuente_seleccionada in ["canal", "sociodem"] else sorted(regiones_mensuales.get(anio_seleccionado, []))
                if opciones_region_o_cat:
                    key_multiselect = key_safe("regiones_categorias", mes, anio_seleccionado)
                    if key_multiselect not in st.session_state:
                        st.session_state[key_multiselect] = []
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Seleccionar todo", key=key_safe("sel_todo", mes, anio_seleccionado)):
                            st.session_state[key_multiselect] = opciones_region_o_cat
                    with col2:
                        if st.button("❌ Deseleccionar todo", key=key_safe("desel_todo", mes, anio_seleccionado)):
                            st.session_state[key_multiselect] = []
                    seleccionadas = st.multiselect(f"Selecciona regiones/categorías para {mes} {anio_seleccionado}:", options=opciones_region_o_cat, default=st.session_state[key_multiselect], key=key_multiselect)
                    for region_o_cat in seleccionadas:
                        nombre_csv = buscar_csv(anio_seleccionado, mes.lower(), region_o_cat, fuente_seleccionada, carpeta_mensual_path)
                        if nombre_csv:
                            path_csv = os.path.join(carpeta_mensual_path, nombre_csv)
                            try:
                                sep = detectar_separador(path_csv)
                                df = pd.read_csv(path_csv, sep=sep)
                                st.write(f"Cargando archivo: {nombre_csv} - Fuente: {fuente_seleccionada}")

                                # Determinar columnas clave según la fuente seleccionada
                                if fuente_seleccionada == "canal":
                                    columnas_clave = ["VALOR", "VOLUMEN", "PENETRACION", "PRECIO MEDIO"]
                                    columnas_disponibles_clave = [col for col in columnas_clave if col in df.columns]
                                    columnas_numericas = df.select_dtypes(include=["number"]).columns.tolist()
                                    columnas_para_seleccionar = sorted(set(columnas_numericas) | set(columnas_disponibles_clave))
                                elif fuente_seleccionada == "sociodem":
                                    columnas_excluir = ["Alimentos", "Nivel"]
                                    columnas_para_seleccionar = [col for col in df.columns if col not in columnas_excluir and pd.api.types.is_numeric_dtype(df[col])]
                                    columnas_disponibles_clave = columnas_para_seleccionar.copy()
                                    if not columnas_para_seleccionar:
                                        st.warning(f"No hay columnas numéricas disponibles para calcular YTD en {nombre_csv}")
                                        columnas_seleccionadas = []
                                elif fuente_seleccionada == "ccaa":
                                    columnas_excluir = ["Alimentos", "Nivel"]  # ajusta según sea necesario
                                    columnas_para_seleccionar = [col for col in df.columns if col not in columnas_excluir and pd.api.types.is_numeric_dtype(df[col])]
                                    columnas_disponibles_clave = columnas_para_seleccionar.copy()
                                else:
                                    columnas_para_seleccionar = []
                                    columnas_disponibles_clave = []
                                # Solo mostrar selección si hay columnas disponibles
                                if not columnas_para_seleccionar:
                                    st.warning(f"No hay columnas numéricas para seleccionar en {nombre_csv}")
                                    columnas_seleccionadas = []
                                else:
                                    # Clave única para esta selección
                                    key_cols = key_safe("columnas_seleccion", anio_seleccionado, mes, region_o_cat)

                                    # Botones de seleccionar/deseleccionar todo
                                    col1, col2 = st.columns([1, 1])
                                    with col1:
                                        if st.button("✅ Seleccionar todas", key=key_safe("select_all", fuente_seleccionada, mes, anio_seleccionado)):
                                            st.session_state[key_cols] = columnas_para_seleccionar
                                    with col2:
                                        if st.button("❌ Deseleccionar todas", key=key_safe("deselect_all", fuente_seleccionada, mes, anio_seleccionado)):
                                            st.session_state[key_cols] = []

                                    # Mostrar multiselect con estado persistente
                                    columnas_seleccionadas = st.multiselect(
                                        f"Selecciona columnas para análisis en {region_o_cat} ({mes} {anio_seleccionado}):",
                                        options=columnas_para_seleccionar,
                                        default=st.session_state.get(key_cols, columnas_disponibles_clave),
                                        key=key_cols
                                    )

                                if "Alimentos" in df.columns and "Nivel" in df.columns:
                                    niveles_unicos = sorted(df["Nivel"].dropna().unique())
                                    niveles_seleccionados = st.multiselect(f"Niveles para {region_o_cat} ({mes} {anio_seleccionado}):", options=niveles_unicos, default=niveles_unicos, key=key_safe("niveles", mes, anio_seleccionado, region_o_cat))
                                    clave = key_safe(anio_seleccionado, mes, fuente_seleccionada, region_o_cat)
                                    seleccion_usuario.setdefault(clave, {"anio": anio_seleccionado, "mes": mes, "fuente": fuente_seleccionada, "region_o_categoria": region_o_cat, "niveles": niveles_seleccionados, "alimentos": []})
                                    for nivel in niveles_seleccionados:
                                        df_nivel = df[df["Nivel"] == nivel]
                                        alimentos_nivel = sorted(df_nivel["Alimentos"].dropna().unique())
                                        st.markdown(f"### \U0001F522 Nivel {nivel}")
                                        pagina_key = key_safe("pagina", clave, nivel)
                                        if pagina_key not in st.session_state:
                                            st.session_state[pagina_key] = 0
                                        _, nueva_pagina = mostrar_alimentos_paginados(alimentos_nivel, anio_seleccionado, mes, region_o_cat, nivel, st.session_state[pagina_key])
                                        if isinstance(nueva_pagina, int):
                                            st.session_state[pagina_key] = nueva_pagina
                                        key_global = key_safe("seleccion", anio_seleccionado, mes, region_o_cat, str(nivel).replace(".", "_"))
                                        seleccion_usuario[clave]["alimentos"].extend(list(st.session_state.get(key_global, [])))

                                # Acumular datos para después
                                if columnas_seleccionadas and "Alimentos" in df.columns:
                                    df_filtrado = df[df["Alimentos"].isin(seleccion_usuario[clave]["alimentos"])][["Alimentos"] + columnas_seleccionadas]
                                    df_filtrado["Año"] = anio_seleccionado
                                    df_filtrado["Mes"] = mes
                                    df_filtrado["Región/Categoría"] = region_o_cat
                                    df_filtrado["Fuente"] = fuente_seleccionada
                                    df_acumulado_total = pd.concat([df_acumulado_total, df_filtrado], ignore_index=True)
                            except Exception as e:
                                st.error(f"Error al leer {nombre_csv}: {e}")


if not df_acumulado_total.empty:
    st.subheader("📊 Visualización avanzada de datos")

    columnas_numericas = [col for col in df_acumulado_total.columns if pd.api.types.is_numeric_dtype(df_acumulado_total[col])]
    columnas_categoricas = [col for col in df_acumulado_total.columns if pd.api.types.is_object_dtype(df_acumulado_total[col]) or pd.api.types.is_categorical_dtype(df_acumulado_total[col])]

    columna_valor = st.selectbox("Selecciona la métrica a graficar (eje Y):", options=columnas_numericas)

    columna_x = st.selectbox("Selecciona el eje X:", options=columnas_categoricas, index=columnas_categoricas.index("Mes") if "Mes" in columnas_categoricas else 0)
    columna_color = st.selectbox("Selecciona el agrupamiento por color:", options=["(Ninguno)"] + columnas_categoricas)
    columna_fila = st.selectbox("Dividir por filas (facet row):", options=["(Ninguno)"] + columnas_categoricas)
    columna_columna = st.selectbox("Dividir por columnas (facet column):", options=["(Ninguno)"] + columnas_categoricas)

    tipo_grafico = st.selectbox("Tipo de gráfico", ["Línea", "Barras", "Área", "Dispersión", "Boxplot", "Heatmap"])


    # Base chart
    base = alt.Chart(df_acumulado_total)

    if tipo_grafico == "Línea":
        chart = base.mark_line()
    elif tipo_grafico == "Barras":
        chart = base.mark_bar()
    elif tipo_grafico == "Área":
        chart = base.mark_area()
    elif tipo_grafico == "Dispersión":
        chart = base.mark_circle(size=60)
    elif tipo_grafico == "Boxplot":
        chart = base.mark_boxplot()
    elif tipo_grafico == "Heatmap":
        chart = base.mark_rect()

    # Construcción dinámica del gráfico
    encode = {
        "x": alt.X(f"{columna_x}:N", sort=meses_ordenados if columna_x.lower() == "mes" else "ascending", title=columna_x),
        "y": alt.Y(f"{columna_valor}:Q", title=columna_valor)
    }

    if columna_color != "(Ninguno)":
        encode["color"] = alt.Color(f"{columna_color}:N", title=columna_color)

    if tipo_grafico == "Heatmap":
        encode["color"] = alt.Color(f"{columna_valor}:Q", title=columna_valor, scale=alt.Scale(scheme="blues"))

    chart = chart.encode(**encode)

    if columna_fila != "(Ninguno)" or columna_columna != "(Ninguno)":
        chart = chart.facet(
            row=alt.Row(f"{columna_fila}:N") if columna_fila != "(Ninguno)" else alt.Row(),
            column=alt.Column(f"{columna_columna}:N") if columna_columna != "(Ninguno)" else alt.Column()
        )

    chart = chart.properties(width=300, height=300).interactive()

    st.altair_chart(chart, use_container_width=True)




with tab_tam_ytd:
    st.subheader("📈 Cálculo TAM y YTD independiente")

    fuentes_disponibles = CARPETAS_MENSUALES
    fuente_seleccionada_tam = st.selectbox("Selecciona fuente", options=fuentes_disponibles)

    carpeta_path = os.path.join(CSV_MENSUAL, fuente_seleccionada_tam)
    if not os.path.exists(carpeta_path):
        st.error(f"No se encontró la carpeta: {carpeta_path}")
        st.stop()

    opciones_filtro = set()
    for f in os.listdir(carpeta_path):
        if f.endswith(".csv"):
            partes = f.replace(".csv", "").split("_")
            if len(partes) >= 4:
                opcion = "_".join(partes[3:]).upper()
                if opcion:
                    opciones_filtro.add(opcion)

    opciones_filtro = sorted(opciones_filtro)
    if not opciones_filtro:
        st.warning("No se encontraron opciones para filtrar en esta fuente.")
        st.stop()

    opcion_seleccionada = st.selectbox(f"Selecciona filtro para {fuente_seleccionada_tam.upper()}", options=opciones_filtro)

    archivos = [f for f in os.listdir(carpeta_path) if f.endswith(".csv")]
    anos_disponibles = sorted(set(f.split("_")[0] for f in archivos))
    anio_seleccionado = st.selectbox("Selecciona año", options=anos_disponibles)

    mes_orden = {m: i for i,m in enumerate(meses_ordenados)}

    mes_inicio = st.selectbox("Mes inicio YTD", options=meses_ordenados)
    mes_fin = st.selectbox("Mes fin YTD", options=meses_ordenados, index=len(meses_ordenados)-1)

    if mes_orden[mes_fin] < mes_orden[mes_inicio]:
        st.error("El mes fin debe ser igual o posterior al mes inicio")
    else:
        alimentos_set = set()
        for mes in meses_ordenados[mes_orden[mes_inicio]:mes_orden[mes_fin]+1]:
            nombre_archivo = f"{anio_seleccionado}_{fuente_seleccionada_tam}_{mes.lower()}_{opcion_seleccionada}.csv"
            ruta_csv = os.path.join(carpeta_path, nombre_archivo)
            if os.path.exists(ruta_csv):
                sep = detectar_separador(ruta_csv)
                df = pd.read_csv(ruta_csv, sep=sep)
                if "Alimentos" in df.columns:
                    alimentos_set.update(df["Alimentos"].dropna().unique())

        alimentos_disponibles = sorted(alimentos_set)

        productos_seleccionados = []

        if not alimentos_disponibles:
            st.warning("No se encontraron alimentos para esa selección.")
        else:
            pagina_key = key_safe("pagina", anio_seleccionado, "YTD")
            if pagina_key not in st.session_state:
                st.session_state[pagina_key] = 0

            niveles_detectados = set()
            df_temporal = []

            for mes in meses_ordenados[mes_orden[mes_inicio]:mes_orden[mes_fin]+1]:
                nombre_archivo = f"{anio_seleccionado}_{fuente_seleccionada_tam}_{mes.lower()}_{opcion_seleccionada}.csv"
                ruta_csv = os.path.join(carpeta_path, nombre_archivo)
                if os.path.exists(ruta_csv):
                    sep = detectar_separador(ruta_csv)
                    df = pd.read_csv(ruta_csv, sep=sep)
                    if "Alimentos" in df.columns and "Nivel" in df.columns:
                        df_temporal.append(df)
                    break

            if df_temporal:
                df_sample = df_temporal[0]
                niveles_detectados = sorted(df_sample["Nivel"].dropna().unique())

            productos_seleccionados = []

            for nivel in niveles_detectados:
                st.markdown(f"### 🔢 Nivel {nivel}")
                alimentos_nivel = sorted(df_sample[df_sample["Nivel"] == nivel]["Alimentos"].dropna().unique())
                pagina_key_nivel = key_safe("pagina", anio_seleccionado, "YTD", str(nivel).replace(".", "_"))
                if pagina_key_nivel not in st.session_state:
                    st.session_state[pagina_key_nivel] = 0

                _, nueva_pagina = mostrar_alimentos_paginados(
                    alimentos_nivel,
                    anio_seleccionado,
                    "YTD",
                    "YTD",
                    nivel,
                    st.session_state[pagina_key_nivel],
                    items_por_pagina=8
                )
                if isinstance(nueva_pagina, int):
                    st.session_state[pagina_key_nivel] = nueva_pagina

                key_global = key_safe("seleccion", anio_seleccionado, "YTD", "YTD", str(nivel).replace(".", "_"))
                productos_seleccionados.extend(st.session_state.get(key_global, []))
    if productos_seleccionados:
        dfs_ytd = []
        for mes in meses_ordenados[mes_orden[mes_inicio]:mes_orden[mes_fin]+1]:
            nombre_archivo = f"{anio_seleccionado}_{fuente_seleccionada_tam}_{mes.lower()}_{opcion_seleccionada}.csv"
            ruta_csv = os.path.join(carpeta_path, nombre_archivo)
            if os.path.exists(ruta_csv):
                sep = detectar_separador(ruta_csv)
                df = pd.read_csv(ruta_csv, sep=sep)
                if "Alimentos" in df.columns:
                    df_filtrado = df[df["Alimentos"].isin(productos_seleccionados)].copy()
                    df_filtrado["Mes"] = mes
                    dfs_ytd.append(df_filtrado)

    if dfs_ytd:
        df_ytd_total = pd.concat(dfs_ytd, ignore_index=True)

        columnas_numericas = df_ytd_total.select_dtypes(include=["number"]).columns.tolist()
        columnas_numericas = [col for col in columnas_numericas if col not in ["Nivel"]]

        if not columnas_numericas:
            st.warning("No se encontraron columnas numéricas para calcular YTD.")
        else:
            df_ytd_sumado = df_ytd_total.groupby("Alimentos")[columnas_numericas].sum().reset_index()


            csv_ytd = df_ytd_sumado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Descargar YTD en CSV",
                data=csv_ytd,
                file_name=f"YTD_{anio_seleccionado}_{opcion_seleccionada}.csv",
                mime="text/csv"
            )

        for col in df_ytd_total.columns:
            if col not in ["Alimentos", "Nivel", "Mes"]:
                df_ytd_total[col] = pd.to_numeric(df_ytd_total[col], errors='coerce')

        columnas_valores = [col for col in df_ytd_total.columns
                        if col not in ["Alimentos", "Nivel", "Mes"] and pd.api.types.is_numeric_dtype(df_ytd_total[col])]

        if not columnas_valores:
            st.warning("No hay columnas numéricas disponibles para calcular YTD.")
            st.stop()
        else:
            columna_valor = st.multiselect("Selecciona la columna para calcular YTD:", columnas_valores)
            df_resultado = df_ytd_total.groupby("Alimentos")[columna_valor].sum().reset_index()
            df_resultado = df_resultado.sort_values(by=columna_valor, ascending=False)
            st.subheader("📊 Resultados acumulados YTD")
            st.dataframe(df_resultado)

            # Botón para descargar YTD en CSV
            csv_ytd_resultado = df_resultado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Descargar YTD (Resultados) en CSV",
                data=csv_ytd_resultado,
                file_name=f"YTD_resultados_{anio_seleccionado}_{opcion_seleccionada}.csv",
                mime="text/csv"
            )

            # Botón para descargar YTD en Excel
            excel_ytd_resultado = io.BytesIO()
            with pd.ExcelWriter(excel_ytd_resultado, engine='xlsxwriter') as writer:
                df_resultado.to_excel(writer, index=False, sheet_name='YTD Resultados')
            excel_ytd_resultado.seek(0)
            st.download_button(
                label="📥 Descargar YTD (Resultados) en Excel",
                data=excel_ytd_resultado,
                file_name=f"YTD_resultados_{anio_seleccionado}_{opcion_seleccionada}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- CALCULAR TAM (suma todo el año para la misma selección) ---
            dfs_tam = []
            for mes in meses_ordenados:
                nombre_archivo = f"{anio_seleccionado}_{fuente_seleccionada_tam}_{mes.lower()}_{opcion_seleccionada}.csv"
                ruta_csv = os.path.join(carpeta_path, nombre_archivo)
                if os.path.exists(ruta_csv):
                    sep = detectar_separador(ruta_csv)
                    df = pd.read_csv(ruta_csv, sep=sep)
                    if "Alimentos" in df.columns:
                        df_filtrado = df[df["Alimentos"].isin(productos_seleccionados)].copy()
                        df_filtrado["Mes"] = mes
                        dfs_tam.append(df_filtrado)

            if dfs_tam:
                df_tam_total = pd.concat(dfs_tam, ignore_index=True)
                for col in df_tam_total.columns:
                    if col not in ["Alimentos", "Nivel", "Mes"]:
                        df_tam_total[col] = pd.to_numeric(df_tam_total[col], errors='coerce')

                df_tam_resultado = df_tam_total.groupby("Alimentos")[columna_valor].sum().reset_index()
                df_tam_resultado = df_tam_resultado.sort_values(by=columna_valor, ascending=False)
                st.subheader("📈 Resultados acumulados TAM (año completo)")
                st.dataframe(df_tam_resultado)

                # Botón para descargar TAM en CSV
                csv_tam_resultado = df_tam_resultado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Descargar TAM (Resultados) en CSV",
                    data=csv_tam_resultado,
                    file_name=f"TAM_resultados_{anio_seleccionado}_{opcion_seleccionada}.csv",
                    mime="text/csv"
                )

                # Botón para descargar TAM en Excel
                excel_tam_resultado = io.BytesIO()
                with pd.ExcelWriter(excel_tam_resultado, engine='xlsxwriter') as writer:
                    df_tam_resultado.to_excel(writer, index=False, sheet_name='TAM Resultados')
                excel_tam_resultado.seek(0)
                st.download_button(
                    label="📥 Descargar TAM (Resultados) en Excel",
                    data=excel_tam_resultado,
                    file_name=f"TAM_resultados_{anio_seleccionado}_{opcion_seleccionada}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
