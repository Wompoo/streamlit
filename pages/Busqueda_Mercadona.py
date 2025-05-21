import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import BytesIO

st.title("Buscador de productos en Mercadona")

# Entrada en Streamlit
alimento = st.text_input("¿Qué alimento quieres buscar en Mercadona?")

if st.button("Buscar") and alimento:
    st.info(f"Buscando productos para: **{alimento}**")

    # Configurar navegador en modo headless
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service, options=options)

    try:
        # Navegar a la URL de búsqueda
        url = f"https://tienda.mercadona.es/search-results?query={alimento}"
        driver.get(url)

        # Esperar hasta que los productos estén disponibles en la página
        wait = WebDriverWait(driver, 10)
        productos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-cell")))

        data = []
        for producto in productos:
            try:
                # Obtener el nombre del producto
                nombre = producto.find_element(By.CLASS_NAME, "product-cell__description-name").text.strip()

                # Obtener el precio del producto
                precio = producto.find_element(By.CLASS_NAME, "product-price__unit-price").text.strip()

                # Obtener el enlace del producto desde el meta tag "og:url"
                try:
                    meta_url = driver.find_element(By.XPATH, "//meta[@property='og:url']").get_attribute("content")
                except Exception:
                    meta_url = None

                # Guardar los datos solo si encontramos el enlace
                if meta_url:
                    data.append({"Producto": nombre, "Precio (€)": precio, "Enlace": meta_url})
                else:
                    st.warning(f"No se encontró el enlace para el producto: {nombre}")
            except Exception as e:
                st.error(f"Error al obtener un producto: {e}")
                continue

        if data:
            # Crear el DataFrame con los datos encontrados
            df = pd.DataFrame(data)
            st.success(f"Productos encontrados: {len(data)}")
            st.dataframe(df)

            # Crear un archivo Excel en memoria
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Productos')
            excel_buffer.seek(0)

            # Botón para descargar el archivo Excel
            st.download_button(
                label="Descargar en Excel",
                data=excel_buffer,
                file_name=f"productos_{alimento}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No se encontraron productos.")

    except Exception as e:
        st.error(f"Ocurrió un error al buscar en Mercadona: {e}")
    
    finally:
        driver.quit()
