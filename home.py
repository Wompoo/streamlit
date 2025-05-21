import streamlit as st
from PIL import Image
st.set_page_config(page_title="Comparador de Alimentos", layout="wide")
st.title("🏠 Página Principal")

st.sidebar.image("logo.jpg", use_container_width=True)
st.write("Contenido del home")

# Título principal
st.title("📊 Comparador de Archivos CSV")
st.subheader("Bienvenido/a al panel de análisis de datos")

st.markdown("""
Este panel te permite comparar y analizar datos entre distintos archivos CSV.
Puedes explorar las diferencias entre años, revisar estadísticas, visualizar gráficos interactivos y exportar resultados.

---

### ¿Qué puedes hacer aquí?

- 📂 **Comparar archivos CSV** por categorías y valores numéricos.
- 📊 **Visualizar gráficos** para entender mejor los cambios.
- 🔍 **Ver diferencias entre años** con porcentajes y gráficos horizontales.
- 📈 **Obtener estadísticas detalladas** y exportarlas.

---

### 👉 Comienza navegando por las secciones desde el menú de la izquierda.

""")

# Instrucciones rápidas
st.info("""
ℹ️ Para comenzar, asegúrate de que has subido al menos dos archivos `.csv` en la carpeta de trabajo.
Los archivos deben tener columnas comunes para comparar.
""")

# Pie de página
st.markdown("---")
st.markdown("Desarrollado por [Across the Shopper] • © 2025")

