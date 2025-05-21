import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import io

st.title("📊 Comparar datos entre dos archivos CSV")

# Ruta donde están los CSV
CARPETA_CSV = "CSV_ANUALES"
csv_paths = list(Path(CARPETA_CSV).glob("*.csv"))
nombres_csv = [f.name for f in csv_paths]

if len(nombres_csv) < 2:
    st.warning("Se necesitan al menos dos archivos CSV en la carpeta.")
else:
    # Selección de archivos
    col1, col2 = st.columns(2)
    with col1:
        archivo_1 = st.selectbox("Selecciona el primer CSV (2022)", nombres_csv, key="csv1")
    with col2:
        archivo_2 = st.selectbox("Selecciona el segundo CSV (2023)", [f for f in nombres_csv if f != archivo_1], key="csv2")

    # Cargar datos
    df1 = pd.read_csv(Path(CARPETA_CSV) / archivo_1)
    df2 = pd.read_csv(Path(CARPETA_CSV) / archivo_2)

    columnas_texto_1 = df1.select_dtypes(include='object').columns.tolist()
    columnas_num_1 = df1.select_dtypes(include='number').columns.tolist()

    columnas_texto_2 = df2.select_dtypes(include='object').columns.tolist()
    columnas_num_2 = df2.select_dtypes(include='number').columns.tolist()

    if columnas_texto_1 and columnas_texto_2 and columnas_num_1 and columnas_num_2:
        categoria = st.selectbox("Columna categórica común", list(set(columnas_texto_1) & set(columnas_texto_2)))
        valor = st.selectbox("Columna numérica común", list(set(columnas_num_1) & set(columnas_num_2)))

        # Reducir a columnas de interés
        df1_reducido = df1[[categoria, valor]].dropna()
        df1_reducido["Fuente"] = archivo_1

        df2_reducido = df2[[categoria, valor]].dropna()
        df2_reducido["Fuente"] = archivo_2

        df_comb = pd.concat([df1_reducido, df2_reducido])

        # Filtro por alimento (categoría)
        alimentos_disponibles = df_comb[categoria].unique()
        alimento_seleccionado = st.selectbox("Selecciona un alimento para comparar", sorted(alimentos_disponibles))

        # Filtrar solo por el alimento seleccionado
        df_filtrado = df_comb[df_comb[categoria] == alimento_seleccionado]

        # Crear pestañas
        tab1, tab2, tab3 = st.tabs(["📈 Gráficos comparativos", "📋 Tabla de datos", "📊 Estadísticas"])

        with tab1:
            st.subheader(f"Gráficos de comparación para '{alimento_seleccionado}'")
            
            # Gráfico de barras
            fig1, ax1 = plt.subplots(figsize=(12, 6))
            sns.barplot(data=df_filtrado, x=categoria, y=valor, hue="Fuente", ax=ax1)
            plt.xticks(rotation=45)
            ax1.set_title(f"Comparación de '{valor}' entre archivos para '{alimento_seleccionado}'")
            st.pyplot(fig1)

            buf1 = io.BytesIO()
            fig1.savefig(buf1, format="png")
            st.download_button("📥 Descargar gráfico de barras (PNG)", data=buf1.getvalue(),
                               file_name=f"grafico_barras_{alimento_seleccionado}.png", mime="image/png")
            
            # Gráfico de líneas
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            sns.lineplot(data=df_filtrado, x=categoria, y=valor, hue="Fuente", marker='o', ax=ax2)
            ax2.set_title(f"Comparación de '{valor}' en línea para '{alimento_seleccionado}'")
            st.pyplot(fig2)

            buf2 = io.BytesIO()
            fig2.savefig(buf2, format="png")
            st.download_button("📥 Descargar gráfico de líneas (PNG)", data=buf2.getvalue(),
                               file_name=f"grafico_lineas_{alimento_seleccionado}.png", mime="image/png")

            # Histograma
            fig3, ax3 = plt.subplots(figsize=(12, 6))
            sns.histplot(df_filtrado[valor], kde=True, ax=ax3)
            ax3.set_title(f"Distribución de '{valor}' para '{alimento_seleccionado}'")
            st.pyplot(fig3)

            buf3 = io.BytesIO()
            fig3.savefig(buf3, format="png")
            st.download_button("📥 Descargar histograma (PNG)", data=buf3.getvalue(),
                               file_name=f"histograma_{alimento_seleccionado}.png", mime="image/png")

        with tab2:
            st.subheader("Vista tabular de los datos filtrados")
            st.dataframe(df_filtrado)

            # Opción de exportar los datos
            st.subheader("🔽 Exportar resultados")
            st.download_button(
                label="📥 Descargar tabla filtrada (CSV)",
                data=df_filtrado.to_csv(index=False),
                file_name=f"datos_filtrados_{alimento_seleccionado}.csv",
                mime="text/csv"
            )

            # Exportar tabla como Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name="DatosFiltrados")

            st.download_button(
                label="📥 Descargar tabla en Excel",
                data=excel_buffer.getvalue(),
                file_name=f"tabla_filtrada_{alimento_seleccionado}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with tab3:
            st.subheader("Estadísticas descriptivas")
            st.write("Primer archivo:")
            st.dataframe(df1_reducido.describe())
            st.write("Segundo archivo:")
            st.dataframe(df2_reducido.describe())

            st.subheader("Diferencias porcentuales entre 2022 y 2023 para el alimento seleccionado")

            df1_alimento = df1_reducido[df1_reducido[categoria] == alimento_seleccionado]
            df2_alimento = df2_reducido[df2_reducido[categoria] == alimento_seleccionado]

            if not df1_alimento.empty and not df2_alimento.empty:
                valor_2022 = df1_alimento[valor].values[0]
                valor_2023 = df2_alimento[valor].values[0]
                diferencia_porcentual = ((valor_2023 - valor_2022) / valor_2022) * 100

                df_diferencias = pd.DataFrame({
                    "Año": ["2022", "2023", "Diferencia Porcentual"],
                    valor: [valor_2022, valor_2023, diferencia_porcentual]
                })
                st.write(f"Diferencia porcentual entre 2022 y 2023 para '{alimento_seleccionado}'")
                st.dataframe(df_diferencias)

                fig4, ax4 = plt.subplots(figsize=(12, 6))
                df_diferencias.set_index("Año")[valor].plot(kind="bar", ax=ax4, color=["skyblue", "lightgreen", "orange"])
                ax4.set_title(f"Comparativa de valores y diferencia porcentual para '{alimento_seleccionado}'")
                ax4.set_ylabel(valor)
                st.pyplot(fig4)

                buf4 = io.BytesIO()
                fig4.savefig(buf4, format="png")
                st.download_button("📥 Descargar gráfico de diferencias (PNG)", data=buf4.getvalue(),
                                   file_name=f"diferencias_{alimento_seleccionado}.png", mime="image/png")
            else:
                st.error("No se encontraron datos para el alimento seleccionado en ambos archivos.")
    else:
        st.error("Los CSV no tienen columnas comunes para comparar.")
