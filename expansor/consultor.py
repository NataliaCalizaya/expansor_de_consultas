import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
import string
import unicodedata
from nltk.tokenize import word_tokenize
# Importa la función renombrada desde expanded_queries
from .expanded_queries import download_nltk_resources 

# Asegurarse de que los recursos de NLTK estén descargados al inicio
download_nltk_resources()

# --- Configuración de la API ---
# URL base para la API del BOE (Boletín Oficial del Estado)
BASE_URL = "https://www.boe.es/datosabiertos/api"
# URL para la legislación consolidada
LEGISLATION_URL = f"{BASE_URL}/legislacion-consolidada"
# URL para el texto de legislación específica por ID
TEXT_URL = f"{BASE_URL}/legislacion-consolidada/id"

def get_document_identifiers(count):
    """
    Obtiene un número 'count' de identificadores de legislación reciente de la API del BOE
    en formato JSON.
    """
    try:
        headers = {"Accept": "application/json"}
        response = requests.get(LEGISLATION_URL, headers=headers)
        response.raise_for_status() # Lanza un HTTPError para respuestas de error (4xx o 5xx)

        data = response.json()
        
        # Extraer los primeros 'count' identificadores
        identifiers = [item['identificador'] for item in data['data'][:count]]
        return identifiers
    except Exception as e:
        print(f"Error al obtener identificadores: {e}")
        return []

def normalize_document_text(text):
    """
    Normaliza el texto de un documento: elimina acentos, puntuación y lo convierte a minúsculas.
    """
    # Quitar acentos
    text_without_accents = ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )
    # Tokenizar y eliminar puntuación
    tokens = word_tokenize(text_without_accents.lower(), language='spanish')
    clean_tokens = [t for t in tokens if t not in string.punctuation]
    return ' '.join(clean_tokens)

def get_legislation_text(identifier):
    """
    Obtiene el texto completo de un documento de legislación por su identificador en formato XML.
    Analiza la respuesta XML para extraer y normalizar el texto de las etiquetas <p>.
    """
    try:
        url = f"{TEXT_URL}/{quote(identifier)}/texto"
        headers = {"Accept": "application/xml"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Analizar el contenido XML
        soup = BeautifulSoup(response.content, 'xml')

        paragraphs = []
        for p_tag in soup.find_all('p'):
            if p_tag.text:
                normalized_paragraph = normalize_document_text(p_tag.text.strip())
                paragraphs.append(normalized_paragraph)

        return "\n".join(paragraphs) if paragraphs else None
    except Exception as e:
        print(f"Error al obtener texto para {identifier}: {e}")
        return None

def build_corpus(identifiers):
    """
    Construye un corpus (diccionario) donde las claves son los IDs de los documentos
    y los valores son su contenido de texto normalizado.
    """
    corpus = {}
    for doc_id in identifiers:
        text_content = get_legislation_text(doc_id)
        if text_content:
            corpus[doc_id] = text_content
            print(f"Documento {doc_id} obtenido correctamente.")
        else:
            print(f"Advertencia: No se pudo obtener el texto para {doc_id}.")
    return corpus

def find_in_corpus(corpus_data, query):
    """
    Busca una consulta (como palabra o frase exacta) dentro del corpus dado.
    Devuelve un diccionario de documentos donde se encuentra la consulta, con los IDs de los documentos
    como claves y su texto normalizado completo como valores.
    """
    results = {}
    # Escapar la consulta por si tiene caracteres especiales y usar \b para coincidencia exacta
    search_pattern = r'\b' + re.escape(query.lower()) + r'\b'

    for doc_id, text_content in corpus_data.items():
        if re.search(search_pattern, text_content.lower()):
            results[doc_id] = text_content

    return results

def get_highlighted_snippets(search_results, query):
    """
    Devuelve un diccionario de fragmentos de texto donde la consulta se resalta usando <strong>.
    El resaltado se aplica solo si la consulta aparece como una palabra o frase exacta
    (usando límites de palabra). Los fragmentos se extraen alrededor de la primera coincidencia.
    """
    if not search_results:
        return {}

    highlighted_snippets = {}
    query_lower = query.lower()
    # Compilar la expresión regular para la coincidencia insensible a mayúsculas/minúsculas y de palabra/frase completa
    pattern = re.compile(r'\b' + re.escape(query_lower) + r'\b', re.IGNORECASE)

    for doc_id, text_content in search_results.items():
        text_lower = text_content.lower()
        match = pattern.search(text_lower)

        if match:
            # Extraer un fragmento de texto alrededor de la primera coincidencia
            start_index = max(0, match.start() - 250)
            end_index = min(len(text_content), match.end() + 250)
            snippet = text_content[start_index:end_index]

            # Resaltar todas las coincidencias exactas dentro del fragmento extraído
            highlighted_snippet = pattern.sub(
                lambda m: f"<strong>{m.group(0)}</strong>",
                snippet
            )
        else:
            # En caso de que, por alguna razón, no se encuentre una coincidencia (no debería ocurrir si find_in_corpus ya filtró),
            # proporciona el comienzo del texto.
            highlighted_snippet = text_content[:300] + '...' if len(text_content) > 300 else text_content

        highlighted_snippets[doc_id] = highlighted_snippet

    return highlighted_snippets