import streamlit as st
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# --------------------- FUNCIONES ---------------------

def graficar_diferencias(df, categoria, valor_base, valor_comparado, tipo="absoluta", top_n=20, titulo=""):
    """
    Grafica diferencias absolutas o porcentuales entre dos columnas de un DataFrame agrupado por categoría.
    """
    df_plot = df.copy()
    df_plot = df_plot[df_plot[valor_base] != 0]  # Evitar divisiones por cero

    df_plot["Diferencia"] = df_plot[valor_comparado] - df_plot[valor_base]
    df_plot["Diferencia %"] = (df_plot["Diferencia"] / df_plot[valor_base]) * 100
    df_plot["abs_diff"] = df_plot["Diferencia"].abs()
    df_plot = df_plot.sort_values("abs_diff", ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(12, 0.5 * top_n + 2))

    if tipo == "porcentual":
        valores = df_plot["Diferencia %"]
        xlabel = "Diferencia porcentual (%)"
    else:
        valores = df_plot["Diferencia"]
        xlabel = "Diferencia absoluta"

    ax.barh(df_plot[categoria], valores, color="steelblue")
    ax.axvline(0, color="gray", linestyle="--")
    ax.set_xlabel(xlabel)
    ax.set_title(titulo or f"Top {top_n} diferencias en '{categoria}'")
    plt.tight_layout()

    return fig, df_plot


# --------------------- APLICACIÓN STREAMLIT ---------------------

st.title("🔍 Análisis de Diferencias entre Archivos CSV")

# Cargar archivos CSV desde la carpeta
CARPETA_CSV = "CSV_Anuales"
csv_paths = list(Path(CARPETA_CSV).glob("*.csv"))
nombres_csv = [f.name for f in csv_paths]

if len(nombres_csv) < 2:
    st.warning("Se necesitan al menos dos archivos CSV en la carpeta.")
else:
    col1, col2 = st.columns(2)
    with col1:
        archivo_1 = st.selectbox("Selecciona el primer CSV", nombres_csv, key="dif_csv1")
    with col2:
        archivo_2 = st.selectbox("Selecciona el segundo CSV", [f for f in nombres_csv if f != archivo_1], key="dif_csv2")

    df1 = pd.read_csv(Path(CARPETA_CSV) / archivo_1)
    df2 = pd.read_csv(Path(CARPETA_CSV) / archivo_2)

    columnas_texto = list(set(df1.select_dtypes(include='object').columns) & set(df2.select_dtypes(include='object').columns))
    columnas_numericas = list(set(df1.select_dtypes(include='number').columns) & set(df2.select_dtypes(include='number').columns))

    if columnas_texto and columnas_numericas:
        categoria = st.selectbox("Columna categórica común", columnas_texto)
        valor = st.selectbox("Columna numérica común", columnas_numericas)

        df1_reducido = df1[[categoria, valor]].dropna().groupby(categoria).mean().reset_index()
        df2_reducido = df2[[categoria, valor]].dropna().groupby(categoria).mean().reset_index()

        df_dif = pd.merge(df1_reducido, df2_reducido, on=categoria, suffixes=(f"_{archivo_1}", f"_{archivo_2}"))
        df_dif = df_dif[df_dif[f"{valor}_{archivo_1}"] != 0]  # Excluir donde valor base es 0

        df_dif["Diferencia"] = df_dif[f"{valor}_{archivo_2}"] - df_dif[f"{valor}_{archivo_1}"]
        df_dif["Diferencia %"] = (df_dif["Diferencia"] / df_dif[f"{valor}_{archivo_1}"]) * 100

        st.subheader("📋 Tabla de diferencias")
        st.dataframe(df_dif[[categoria, f"{valor}_{archivo_1}", f"{valor}_{archivo_2}", "Diferencia", "Diferencia %"]])

        st.subheader("📈 Comparación visual de diferencias entre archivos CSV por categoría común")
        st.markdown(f"""
Este gráfico compara el valor promedio de **'{valor}'** entre los archivos seleccionados (**{archivo_1}** y **{archivo_2}**) para cada categoría en **'{categoria}'**.

- Cada barra representa la diferencia entre los valores promedio por categoría.
- Puedes elegir mostrar diferencias absolutas o porcentuales.
- Se excluyen las categorías donde el valor base sea 0 para evitar errores y mejorar la calidad del análisis.
""")

        max_mostrar = st.slider("Cantidad máxima de categorías a mostrar", min_value=5, max_value=min(50, len(df_dif)), value=20)
        tipo_diferencia = st.radio("Tipo de diferencia a mostrar", ["absoluta", "porcentual"])

        fig, df_plot = graficar_diferencias(
            df=df_dif,
            categoria=categoria,
            valor_base=f"{valor}_{archivo_1}",
            valor_comparado=f"{valor}_{archivo_2}",
            tipo=tipo_diferencia,
            top_n=max_mostrar,
            titulo=f"Diferencias de '{valor}' por '{categoria}' entre {archivo_1} y {archivo_2}"
        )

        # Generar resumen textual del gráfico
        if not df_plot.empty:
            mayor_aumento = df_plot.loc[df_plot["Diferencia"].idxmax()]
            mayor_disminucion = df_plot.loc[df_plot["Diferencia"].idxmin()]
            num_subidas = (df_plot["Diferencia"] > 0).sum()
            num_bajadas = (df_plot["Diferencia"] < 0).sum()
            promedio_cambio = df_plot["Diferencia"].mean()

            resumen = f"""
**🧾 Resumen del gráfico**
- Se analizaron **{len(df_plot)}** categorías.
- **{num_subidas}** categorías presentan un aumento promedio de **{promedio_cambio:.2f}** unidades.
- **{num_bajadas}** categorías muestran una disminución.
- La categoría con mayor aumento fue **{mayor_aumento[categoria]}** con **+{mayor_aumento['Diferencia']:.2f}**.
- La mayor disminución fue en **{mayor_disminucion[categoria]}** con **{mayor_disminucion['Diferencia']:.2f}**.
"""
            st.markdown(resumen)

        st.pyplot(fig)

    else:
        st.error("No hay columnas comunes de tipo texto y numérico para comparar.")
