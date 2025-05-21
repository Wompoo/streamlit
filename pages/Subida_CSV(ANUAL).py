# Archivo: pages/4_subida_archivos.py

import streamlit as st
import pandas as pd
from pathlib import Path

st.title("📤 Subida de nuevos archivos CSV")

# Ruta destino para guardar archivos
CARPETA_CSV = "CSV_ANUALES"

archivo_subido = st.file_uploader("Selecciona un archivo CSV para subir", type="csv")

if archivo_subido:
    nombre_guardado = st.text_input("Nombre para guardar el archivo (incluye .csv)", value=archivo_subido.name)
    
    if st.button("Guardar archivo"):
        ruta_destino = Path(CARPETA_CSV) / nombre_guardado
        with open(ruta_destino, "wb") as f:
            f.write(archivo_subido.getbuffer())
        st.success(f"✅ Archivo guardado como: {nombre_guardado}")

        # Vista previa
        try:
            df_vista = pd.read_csv(ruta_destino)
            st.subheader("👀 Vista previa del archivo subido")
            st.dataframe(df_vista.head())
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
