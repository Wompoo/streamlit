import streamlit as st
import requests
import pandas as pd
from io import BytesIO

def obtener_producto_por_codigo(codigo_barras):
    url = f'https://world.openfoodfacts.org/api/v2/product/{codigo_barras}'
    params = {'fields': 'product_name,brands,stars'}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 1:
            product = data.get('product', {})
            nombre = product.get('product_name', 'Nombre no disponible')
            marca = product.get('brands', 'Marca no disponible')
            estrellas = product.get('stars', 'Estrellas no disponibles')
            return {
                'Código de barras': codigo_barras,
                'Producto': nombre,
                'Marca': marca,
                'Estrellas': estrellas
            }
        else:
            return {
                'Código de barras': codigo_barras,
                'Producto': 'Producto no encontrado',
                'Marca': '',
                'Estrellas': ''
            }
    else:
        return {
            'Código de barras': codigo_barras,
            'Producto': 'Error al consultar la API',
            'Marca': '',
            'Estrellas': ''
        }

def cargar_codigos_desde_txt(uploaded_file):
    try:
        return [line.decode('utf-8').strip() for line in uploaded_file if line.strip()]
    except Exception as e:
        st.write(f"Error al leer el archivo: {e}")
        return []

def convertir_a_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Productos')
    output.seek(0)
    return output

def main():
    st.title("Consulta de Productos por Código de Barras")

    uploaded_file = st.file_uploader("Sube tu archivo de códigos de barras (.txt)", type=["txt"])

    if uploaded_file:
        codigos_barras = cargar_codigos_desde_txt(uploaded_file)
        if codigos_barras:
            resultados = []
            with st.spinner("Buscando productos..."):
                for codigo in codigos_barras:
                    resultados.append(obtener_producto_por_codigo(codigo))

            df_resultados = pd.DataFrame(resultados)
            st.dataframe(df_resultados)

            # Botón para descargar como CSV
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button("📄 Descargar CSV", data=csv, file_name='productos.csv', mime='text/csv')

            # Botón para descargar como Excel
            excel_data = convertir_a_excel(df_resultados)
            st.download_button("📊 Descargar Excel", data=excel_data, file_name='productos.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.write("El archivo no contiene códigos de barras válidos.")

if __name__ == "__main__":
    main()
