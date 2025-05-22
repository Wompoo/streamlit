import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time
from tqdm import tqdm

def download_excel_files(url):
    # Headers para simular un navegador
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Obtener el contenido de la página
        print("Accediendo a la página web...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parsear el HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar todos los enlaces
        links = soup.find_all('a')
        
        # Filtrar solo los enlaces de Excel
        excel_links = [link.get('href') for link in links if link.get('href', '').lower().endswith('.xlsx')]
        
        # Convertir URLs relativas a absolutas
        excel_links = [urljoin(url, link) for link in excel_links]
        
        print(f"\nEncontrados {len(excel_links)} archivos Excel")
        
        # Contador de archivos descargados y omitidos
        downloaded = 0
        skipped = 0
        
        # Descargar cada archivo
        for excel_url in tqdm(excel_links, desc="Descargando archivos"):
            # Obtener el nombre del archivo de la URL
            filename = excel_url.split('/')[-1]
            
            # Verificar si el archivo ya existe
            if os.path.exists(filename):
                skipped += 1
                continue
                
            try:
                # Descargar el archivo
                response = requests.get(excel_url, headers=headers)
                response.raise_for_status()
                
                # Guardar el archivo
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                downloaded += 1
                
                # Pequeña pausa para no sobrecargar el servidor
                time.sleep(0.5)
                
            except Exception as e:
                print(f"\nError descargando {filename}: {str(e)}")
        
        print(f"\nProceso completado:")
        print(f"- Archivos descargados: {downloaded}")
        print(f"- Archivos omitidos (ya existentes): {skipped}")
        print(f"- Total de archivos procesados: {downloaded + skipped}")
        
    except Exception as e:
        print(f"Error accediendo a la página: {str(e)}")

# URL de la página
url = "https://www.mapa.gob.es/es/alimentacion/temas/consumo-tendencias/panel-de-consumo-alimentario/series-anuales/default.aspx"

# Ejecutar la función
if __name__ == "__main__":
    download_excel_files(url)