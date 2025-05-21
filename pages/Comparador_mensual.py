import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt

CSV_MENSUAL = "CSV_Mensuales"
CSV_ANUAL = "CSV_Anuales"

st.title("📊 Comparador por Alimento: Meses vs Años")

# --------------------------
# Utilidades para cargar estructura de archivos
# --------------------------

def listar_estructura_mensual():
    estructura = {}
    for f in os.listdir(CSV_MENSUAL):
        if not f.endswith(".csv"):
            continue
        partes = f.replace(".csv", "").split("_")
        if len(partes) >= 2:
            mes = partes[0].capitalize()
            anio = partes[1]
            estructura.setdefault(anio, set()).add(mes)
    return estructura  # dict { "2022": {"Enero", "Febrero", ...} }

def listar_anios_anuais():
    return sorted([f.replace(".csv", "") for f in os.listdir(CSV_ANUAL)
                   if f.endswith(".csv") and f.replace(".csv", "").isdigit()])

estructura_mensual = listar_estructura_mensual()
anios_anuais = listar_anios_anuais()

# Unir años encontrados en ambas fuentes
todos_los_anios = sorted(set(estructura_mensual.keys()).union(anios_anuais))

# --------------------------
# Interfaz de selección
# --------------------------

st.markdown("## 🗓️ Selección de años y meses")

seleccion_usuario = {}

for anio in todos_los_anios:
    con_anio = st.checkbox(f"📅 {anio} (Año completo)", key=f"chk_{anio}")
    seleccion_usuario[anio] = {"__año__": con_anio, "meses": set()}

    meses_disponibles = sorted(estructura_mensual.get(anio, []))
    if meses_disponibles:
        # Agregamos la opción de seleccionar/desmarcar todos los meses
        with st.expander(f"Meses disponibles para {anio}", expanded=True):
            select_all = st.checkbox(f"Seleccionar/Deseleccionar todos los meses para {anio}", key=f"select_all_{anio}")
            for mes in meses_disponibles:
                mes_key = f"{anio}_{mes}"
                con_mes = st.checkbox(f"{mes}", key=mes_key, value=(select_all if select_all else False))
                if con_mes:
                    seleccion_usuario[anio]["meses"].add(mes)

# Mostrar resumen de selección
selecciones = []
for anio, datos in seleccion_usuario.items():
    if datos["__año__"]:
        selecciones.append(f"Año completo: {anio}")
    for mes in sorted(datos["meses"]):
        selecciones.append(f"{mes} {anio}")

if not selecciones:
    st.warning("Selecciona al menos un año o mes.")
    st.stop()

st.success("Seleccionado: " + ", ".join(selecciones))

# --------------------------
# Cargar archivos
# --------------------------

def cargar_datos(seleccion):
    dfs = []
    for anio, datos in seleccion.items():
        if datos["__año__"]:
            path = os.path.join(CSV_ANUAL, f"{anio}.csv")
            try:
                if os.path.exists(path):
                    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
                    df["Origen"] = anio
                    dfs.append(df)
            except Exception as e:
                st.error(f"Error al cargar el archivo anual {anio}: {e}")
        
        for mes in datos["meses"]:
            archivos = [f for f in os.listdir(CSV_MENSUAL)
                        if f.startswith(f"{mes}_{anio}_") and f.endswith(".csv")]
            for archivo in archivos:
                try:
                    df = pd.read_csv(os.path.join(CSV_MENSUAL, archivo), sep=";", encoding="utf-8-sig")
                    df["Origen"] = f"{mes} {anio}"
                    dfs.append(df)
                except Exception as e:
                    st.error(f"Error al cargar el archivo mensual {archivo}: {e}")
                    
    return pd.concat(dfs) if dfs else pd.DataFrame()

df_total = cargar_datos(seleccion_usuario)

if df_total.empty or "Alimentos" not in df_total.columns:
    st.error("No se encontraron datos válidos para los filtros seleccionados.")
    st.stop()

# --------------------------
# Comparación de alimentos
# --------------------------

alimentos = sorted(df_total["Alimentos"].dropna().unique())
alimento_sel = st.selectbox("🍎 Selecciona un alimento", alimentos)

df_filtrado = df_total[df_total["Alimentos"] == alimento_sel]

if df_filtrado.empty:
    st.warning("No hay datos para ese alimento.")
    st.stop()

df_numerico = df_filtrado.drop(columns=["Alimentos"]).set_index("Origen").apply(pd.to_numeric, errors='coerce')
df_numerico = df_numerico.transpose()

st.subheader("📋 Indicadores")
st.dataframe(df_numerico)

# --------------------------
# Gráficos
# --------------------------

st.subheader("📊 Comparativa Gráfica")

# Gráfico de barras ordenado
fig1, ax1 = plt.subplots(figsize=(10, 5))
df_numerico_sorted = df_numerico.sort_values(by=df_numerico.columns[0], axis=1, ascending=False)  # Ordenar por la primera columna
df_numerico_sorted.plot(kind="bar", ax=ax1)
ax1.set_title(f"Comparativa de {alimento_sel}")
plt.xticks(rotation=45)
st.pyplot(fig1)

# Gráfico de evolución
fig2, ax2 = plt.subplots(figsize=(10, 5))
df_numerico.plot(marker='o', ax=ax2)
ax2.set_title("Evolución")
plt.xticks(rotation=45)
st.pyplot(fig2)
