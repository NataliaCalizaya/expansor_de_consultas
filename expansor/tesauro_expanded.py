from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from time import sleep
import unicodedata

# --- Funciones de utilidad ---

def normalize_text(text):
    """
    Normaliza el texto eliminando acentos, convirtiéndolo a mayúsculas y eliminando espacios en blanco.
    """
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return text.strip().upper()

# --- Función de consulta del Tesauro ---

def query_unesco_thesaurus(term):
    """
    Consulta el sitio web del tesauro de la UNESCO para un término dado y encontrar conceptos relacionados.
    Utiliza Selenium para navegar por el sitio web dinámico y BeautifulSoup para analizar el contenido.
    """
    # Configurar las opciones de Chrome para la navegación sin interfaz gráfica (headless)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox") # Necesario para algunos entornos (ej. Docker)
    options.add_argument("--disable-dev-shm-usage") # Supera problemas de recursos limitados en algunos entornos

    # Inicializar ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Formatear el término para la URL y construir la URL de búsqueda
    formatted_term = term.replace(' ', '+')
    url = f"https://vocabularies.unesco.org/browser/thesaurus/es/search?clang=es&q={formatted_term}"
    print(f"🌐 Abriendo URL: {url}")
    driver.get(url)
    sleep(3) # Dar tiempo a la página para cargar su contenido dinámicamente

    # Analizar la página inicial de resultados de búsqueda
    soup = BeautifulSoup(driver.page_source, "html.parser")
    search_result_listing = soup.find('div', class_='search-result-listing')

    if not search_result_listing:
        print("❗ No se encontraron resultados de búsqueda para el término.")
        driver.quit()
        return {}

    # Encontrar todos los enlaces de concepto relevantes (priorizando 'conceptlabel' pero usando 'prefLabel' como alternativa)
    concept_links = (
        search_result_listing.find_all('a', class_='prefLabel conceptlabel') +
        search_result_listing.find_all('a', class_='prefLabel')
    )
    print(f"🔗 Se encontraron {len(concept_links)} enlaces de concepto para explorar.")

    # Inicializar la estructura para los resultados
    thesaurus_data = {
        "Conceptos específicos": [],
        "Conceptos relacionados": []
    }

    # Crear un mapeo de nombres de sección normalizados a sus claves originales para una coincidencia robusta
    normalized_keys_map = {normalize_text(k): k for k in thesaurus_data}

    # Iterar sobre cada enlace de concepto encontrado para extraer términos relacionados
    for link in concept_links:
        href = link.get('href')
        if not href:
            continue

        concept_detail_url = "https://vocabularies.unesco.org/browser/" + href
        print(f"➡️ Navegando a: {concept_detail_url}")

        driver.get(concept_detail_url)
        try:
            # Esperar hasta que se cargue un elemento clave que indique la presencia de contenido
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.versal.property-click"))
            )
        except Exception:
            print("❗ No se encontró el contenido esperado en la página de detalles del concepto, omitiendo.")
            continue

        # Analizar la página de detalles del concepto
        concept_soup = BeautifulSoup(driver.page_source, "html.parser")
        property_labels = concept_soup.find_all('div', class_='property-label')

        # Extraer términos basándose en las etiquetas de propiedad (ej. "Conceptos específicos", "Conceptos relacionados")
        for label_div in property_labels:
            span_element = label_div.find('span', class_='versal property-click')
            if span_element:
                normalized_section_name = normalize_text(span_element.get_text())

                # Solo procesar las secciones que nos interesan
                if normalized_section_name not in normalized_keys_map:
                    continue

                actual_section_key = normalized_keys_map[normalized_section_name]

                # Encontrar el contenedor que contiene los términos para esta propiedad
                value_wrapper = label_div.find_next('div', class_='property-value-wrapper')
                if not value_wrapper:
                    continue

                # Extraer términos individuales de los enlaces dentro del contenedor
                links_in_wrapper = value_wrapper.find_all('a')
                for a_tag in links_in_wrapper:
                    term_text = a_tag.get_text(strip=True)
                    if term_text and (term_text not in thesaurus_data[actual_section_key]):
                        thesaurus_data[actual_section_key].append(term_text)

    driver.quit() # Cerrar la instancia del navegador
    return thesaurus_data