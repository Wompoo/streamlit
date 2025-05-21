import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import unicodedata
import re  # Import añadido para usar expresiones regulares
from io import BytesIO

# Función para eliminar acentos y caracteres especiales
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

# Función para obtener detalles del producto (versión mejorada)
def obtener_detalles(url_producto):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url_producto, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Precio
            precio_span = soup.find('span', {'itemprop': 'price', 'class': 'offer-now'})
            precio = precio_span.get_text(strip=True).replace('€', '').strip() if precio_span else 'No disponible'
            
            # Valoración - Método 1: Barra de porcentaje
            valoracion_real = 'Sin valoración'
            rating_div = soup.find('div', class_='ratingPercentBar')
            
            if rating_div:
                barra_porcentaje = rating_div.find('div')
                if barra_porcentaje and 'width' in barra_porcentaje.get('style', ''):
                    porcentaje = int(barra_porcentaje['style'].split(':')[1].replace('%', '').strip())
                    valoracion_real = round(porcentaje / 20, 1)
            
            # Método 2: Meta tag de valoración
            if valoracion_real == 'Sin valoración':
                rating_meta = soup.find('meta', {'itemprop': 'ratingValue'})
                if rating_meta:
                    try:
                        valoracion_real = float(rating_meta['content'])
                    except ValueError:
                        pass
            
            # Método 3: Texto en el subtítulo con regex
            if valoracion_real == 'Sin valoración':
                rating_text = soup.find('div', class_='ratingSubtitle')
                if rating_text:
                    match = re.search(r'([\d,]+)\s+de\s+5', rating_text.get_text())
                    if match:
                        try:
                            valoracion_real = float(match.group(1).replace(',', '.'))
                        except ValueError:
                            pass
            
            # Formatear la valoración
            if isinstance(valoracion_real, (int, float)):
                valoracion_real = f"{valoracion_real:.1f} estrellas"
            
            # Reseñas
            reseñas_divs = soup.find_all('div', class_='reviewText')
            reseñas = [reseña.get_text(strip=True) for reseña in reseñas_divs]
            
            return {
                'precio': precio,
                'valoracion': valoracion_real if valoracion_real != 'Sin valoración' else 'Sin valoración',
                'reseñas': reseñas
            }
        return {'precio': 'Error página', 'valoracion': '0', 'reseñas': []}
    
    except Exception as e:
        return {'precio': f'Error: {str(e)}', 'valoracion': '0', 'reseñas': []}

# Interfaz de Streamlit (igual que antes)
st.title("Buscador de alimentos en Eroski")

alimento = st.text_input("¿Qué alimento quieres buscar en Eroski?")

if st.button("Buscar") and alimento:
    st.info(f"Buscando: {alimento}")
    alimento_clean = remove_accents(alimento)
    url = f"https://supermercado.eroski.es/es/search/results/?q={alimento_clean.replace(' ', '%20')}&suggestionsFilter=false"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        product_links = soup.find_all('a', href=lambda href: href and '/productdetail/' in href)
        
        productos = []
        seen_hrefs = set()
        normalized_alimento = alimento_clean.lower()

        for link in product_links:
            href = link['href']
            title = link.text.strip()
            normalized_title = remove_accents(title).lower()

            if href in seen_hrefs or normalized_alimento not in normalized_title:
                continue

            seen_hrefs.add(href)
            product_url = f"https://supermercado.eroski.es{href}"

            detalles = obtener_detalles(product_url)
            time.sleep(0.5)
            
            # Añadir reseñas en formato texto concatenado
            reseñas_texto = "\n".join(detalles['reseñas']) if detalles['reseñas'] else "Sin reseñas"
            
            # Añadir los productos con sus detalles
            productos.append({
                'Producto': title,
                'Precio (€)': detalles['precio'],
                'Valoración': detalles['valoracion'],
                'Enlace': product_url,
                'Reseñas': reseñas_texto  # Se agrega el texto concatenado de las reseñas
            })

        if productos:
            # Crear el DataFrame
            df = pd.DataFrame(productos)
            st.dataframe(df)

            # Mostrar las reseñas en pantalla
            for i, producto in enumerate(productos):
                if producto['Reseñas'] != "Sin reseñas":
                    with st.expander(f"Reseñas de {producto['Producto']}"):
                        reseñas = producto['Reseñas'].split("\n")
                        for j, reseña in enumerate(reseñas, 1):
                            st.markdown(f"**Reseña {j}:** {reseña}")
            
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

    else:
        st.error(f"Error al acceder a la página: {response.status_code}")
