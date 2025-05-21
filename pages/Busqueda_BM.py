import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from io import BytesIO

st.title("Buscador de productos en BM Supermercados")

# Entrada del usuario
alimento = st.text_input("¿Qué alimento quieres buscar en BM?")

if st.button("Buscar") and alimento:
    st.info(f"Buscando productos para: **{alimento}**")

    # Configuración de Selenium
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        query = alimento.replace(" ", "%20")
        url = f"https://www.online.bmsupermercados.es/es/s/{query}?orderById=13&page=1"
        driver.get(url)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.widget-prod"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        productos = []

        bloques = soup.select("div.widget-prod")
        for bloque in bloques:
            img_tag = bloque.find('img')
            titulo = img_tag['alt'] if img_tag and img_tag.has_attr('alt') else "Sin título"

            price_span = bloque.find('span', id='grid-widget--price')
            precio = price_span.get_text(strip=True).replace('\xa0', ' ') if price_span else "Precio no disponible"

            # Buscar el enlace del producto
            link_tag = bloque.find('a', href=True)
            link = "https://www.online.bmsupermercados.es" + link_tag['href'] if link_tag else "Sin enlace"

            productos.append({
                'Producto': titulo,
                'Precio (€)': precio,
                'Enlace': link
            })
            
        if productos:
            df = pd.DataFrame(productos)
            st.success(f"Productos encontrados: {len(productos)}")
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
        st.error(f"Error al acceder a la página o al extraer productos: {e}")

    finally:
        driver.quit()
