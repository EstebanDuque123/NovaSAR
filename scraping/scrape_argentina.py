import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

def scrape_argentina_profugos_de_la_justicia():
    headers = {'User-Agent': 'Mozilla/5.0'}
    base_url = 'https://www.argentina.gob.ar/seguridad/recompensas/profugos?page='

    nombres = []
    pagina = 1

    while True:
        url = base_url + str(pagina)
        print(f"🔄 Procesando página {pagina}...")

        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            break

        soup = BeautifulSoup(res.text, 'html.parser')
        h4_tags = soup.find_all('h4')

        if not h4_tags:
            print("✅ No hay más datos.")
            break

        for tag in h4_tags:
            texto = tag.text.strip()
            if texto and texto not in nombres:
                nombres.append(texto)

        pagina += 1

    # 🔹 Preparar DataFrame con las columnas requeridas
    fecha_hoy = datetime.today().strftime("%d/%m/%Y")
    df = pd.DataFrame([{
        "nombre": nombre,
        "identificacion": "",
        "lista": "Argentina profugos de la justicia",
        "tipo_lista": "Listas profugos",
        "fuente": "Prófugos de la Justicia - Programa Nacional de Recompensas",
        "fecha_ingreso": fecha_hoy
    } for nombre in nombres])

    # 🔹 Crear carpeta resultado_scraping dentro de la app scraping
    carpeta_resultados = os.path.join(os.path.dirname(__file__), 'resultado_scraping')
    os.makedirs(carpeta_resultados, exist_ok=True)

    # 🔹 Exportar los datos a CSV
    ruta_csv = os.path.join(carpeta_resultados, 'ARGENTINA_PROFUGOS_DE_LA_JUSTICIA.csv')
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")

    print(f"✅ Nombres guardados en '{ruta_csv}'")

if __name__ == "__main__":
    scrape_argentina_profugos_de_la_justicia()
