import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
import string
import unicodedata
from nltk.tokenize import word_tokenize
from .expanded_queries import download_nltk

download_nltk()

#consultor.py
# Configuración de la API
BASE_URL = "https://www.boe.es/datosabiertos/api"
LEGISLACION_URL = f"{BASE_URL}/legislacion-consolidada"
TEXTO_URL = f"{BASE_URL}/legislacion-consolidada/id"

def get_identifiers(count):
    # Obtiene 10 identificadores de legislación reciente en formato JSON
    try:
        headers = {"Accept": "application/json"}
        response = requests.get(LEGISLACION_URL, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extraemos los primeros n identificadores
        identifiers = [item['identificador'] for item in data['data'][:count]]
        return identifiers
    except Exception as e:
        print(f"Error al obtener identificadores: {e}")
        return []

def normalizar_texto(texto):
    """Normaliza el texto: elimina acentos, puntuación y lo convierte a minúsculas."""
    # Quitar acentos
    texto_sin_acentos = ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c)
    )
    # Tokenizar y eliminar puntuación
    tokens = word_tokenize(texto_sin_acentos.lower())
    tokens_limpios = [t for t in tokens if t not in string.punctuation]
    return ' '.join(tokens_limpios)

def get_text_legislation(identifier):
    # Obtiene el texto completo de un identificador en formato XML
    try:
        url = f"{TEXTO_URL}/{quote(identifier)}/texto"
        headers = {"Accept": "application/xml"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parsear XML
        soup = BeautifulSoup(response.content, 'xml')

        textos = []
        for p in soup.find_all('p'):
            if p.text:
                texto_normalizado = normalizar_texto(p.text.strip())
                textos.append(texto_normalizado)

        return "\n".join(textos) if textos else None
    except Exception as e:
        print(f"Error al obtener texto para {identifier}: {e}")
        return None

def join_corpus(identifiers):
    #Construye un corpus con los textos de los identificadores
    corpus = {}
    for id in identifiers:
        texto = get_text_legislation(id)
        if texto:
            corpus[id] = texto
            print(f"Documento {id} obtenido correctamente")
        else:
            print(f"Advertencia: No se pudo obtener texto para {id}")
    return corpus

import re

def find_in_corpus(corpus, query):
    results = {}
    # Escapa la consulta por si tiene caracteres especiales y aplica \b para coincidencia exacta
    pattern = r'\b' + re.escape(query.lower()) + r'\b'

    for doc_id, texto in corpus.items():
        if re.search(pattern, texto.lower()):
            results[doc_id] = texto

    return results

import re

def mostrar_resultados(results, consulta):
    """
    Devuelve un diccionario con fragmentos de texto donde se resalta la consulta usando <strong>,
    solo si aparece como palabra o frase exacta (usando límites de palabra).
    """
    if not results:
        return {}

    resultados_resaltados = {}
    consulta_lower = consulta.lower()
    pattern = re.compile(r'\b' + re.escape(consulta_lower) + r'\b', re.IGNORECASE)

    for doc_id, texto in results.items():
        texto_lower = texto.lower()
        match = pattern.search(texto_lower)

        if match:
            start = max(0, match.start() - 250)
            end = min(len(texto), match.end() + 250)
            fragmento = texto[start:end]

            # Resaltar todas las coincidencias exactas
            fragmento_resaltado = pattern.sub(
                lambda m: f"<strong>{m.group(0)}</strong>",
                fragmento
            )
        else:
            fragmento_resaltado = texto[:300] + '...' if len(texto) > 300 else texto

        resultados_resaltados[doc_id] = fragmento_resaltado

    return resultados_resaltados
