from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from time import sleep
import unicodedata

def normalizar(texto: str) -> str:
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto.strip().upper()
    
def consultar_tesauro_unesco(termino: str):
    opciones = webdriver.ChromeOptions()
    opciones.add_argument("--headless")
    opciones.add_argument("--no-sandbox")
    opciones.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)

    termino_formateado = termino.replace(' ', '+')
    url = f"https://vocabularies.unesco.org/browser/thesaurus/es/search?clang=es&q={termino_formateado}"
    print(f"🌐 Abriendo URL: {url}")
    driver.get(url)
    sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    search_result = soup.find('div', class_='search-result-listing')
    if not search_result:
        print("❗ No se encontró ningún resultado.")
        driver.quit()
        return {}

    #concept_links = search_result.find_all('a', class_='prefLabel conceptlabel')
    concept_links = (
    search_result.find_all('a', class_='prefLabel conceptlabel') +
    search_result.find_all('a', class_='prefLabel')
    )
    print(f"🔗 Se encontraron {len(concept_links)} enlaces de concepto")

    resultados = {
        "Conceptos específicos": [],
        "Conceptos relacionados": []
    }

    # Creamos un mapa de secciones normalizadas -> originales
    claves_normalizadas = {normalizar(k): k for k in resultados}

    for link in concept_links:
        href = link.get('href')
        if not href:
            continue

        concepto_url = "https://vocabularies.unesco.org/browser/" + href
        print(f"➡️ Navegando a: {concepto_url}")
        
        driver.get(concepto_url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.versal.property-click"))
            )
        except:
            print("❗ No se encontró el contenido esperado en la página del concepto.")
            continue

        concept_soup = BeautifulSoup(driver.page_source, "html.parser")
        labels = concept_soup.find_all('div', class_='property-label')

        for label_div in labels:
            span = label_div.find('span', class_='versal property-click')
            if span:
                seccion_normalizada = normalizar(span.get_text())
                if seccion_normalizada not in claves_normalizadas:
                    continue

                seccion_real = claves_normalizadas[seccion_normalizada]

                wrapper = label_div.find_next('div', class_='property-value-wrapper')
                if not wrapper:
                    continue

                links = wrapper.find_all('a')
                for a in links:
                    texto = a.get_text(strip=True)
                    if texto and (texto not in resultados[seccion_real]):
                        resultados[seccion_real].append(texto)

    driver.quit()
    return resultados


# Uso
# if __name__ == "__main__":
#     termino = "abadia"
#     resultados = consultar_tesauro_unesco(termino)
#     print("✅ Términos encontrados:")
#     for seccion, items in resultados.items():
#         print(f"\n📚 {seccion}:")
#         for item in items:
#             print("-", item)
