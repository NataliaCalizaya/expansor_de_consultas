import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
import string
from itertools import product
from collections import defaultdict
# Importa la función renombrada desde el módulo tesauro_expanded
from .tesauro_expanded import query_unesco_thesaurus 

# --- Gestión de recursos NLTK ---

def download_nltk_resources():
    """Descarga los recursos esenciales de NLTK (punkt, wordnet, stopwords) si no están ya presentes."""
    resources = {
        'punkt': 'tokenizers/punkt',
        'wordnet': 'corpora/wordnet',
        'stopwords': 'corpora/stopwords',
    }
    for name, path in resources.items():
        try:
            nltk.data.find(path)
            print(f"✔️ '{name}' ya está disponible.")
        except LookupError:
            print(f"⬇️ Descargando '{name}'...")
            nltk.download(name)

# Llamar a esta función una vez cuando se carga el módulo para asegurar que los recursos estén disponibles
download_nltk_resources()

# Palabras vacías (stopwords) globales y puntuación para español
STOP_WORDS = set(nltk.corpus.stopwords.words('spanish') + list(string.punctuation))

# --- Expansión con WordNet ---

def get_wordnet_synonyms(word):
    """
    Obtiene sinónimos para una palabra dada utilizando el corpus de WordNet (español).
    Excluye la palabra original y los sinónimos de varias palabras.
    """
    synonyms = set()
    for syn in wordnet.synsets(word, lang='spa'):
        for lemma in syn.lemmas('spa'):
            synonym = lemma.name().replace('_', ' ').lower()
            # Asegurarse de que el sinónimo no sea la palabra original y sea de una sola palabra
            if synonym != word and ' ' not in synonym:
                synonyms.add(synonym)
    return list(synonyms)

# --- Expansión con Tesauro (usando el módulo externo) ---

def get_thesaurus_phrases(query, max_results=15):
    """
    Obtiene hasta `max_results` frases relacionadas del tesauro de la UNESCO
    para una consulta dada, llamando a una función externa.
    """
    thesaurus_phrases = []
    try:
        # Llama a la función del módulo tesauro_expanded.py
        results_from_thesaurus = query_unesco_thesaurus(query.lower()) 
        for section_name in results_from_thesaurus:
            thesaurus_phrases.extend(results_from_thesaurus[section_name])
    except Exception as e:
        print(f"❗ Error al consultar el tesauro para la frase '{query}': {e}")

    # Devolver frases únicas, limitadas por max_results
    return list(set(thesaurus_phrases))[:max_results]

# --- Lógica principal de expansión de consultas ---

def generate_expanded_queries(original_query, stop_words=STOP_WORDS, max_results=15):
    """
    Genera consultas expandidas combinando sinónimos de WordNet para palabras individuales
    y añadiendo frases adicionales del tesauro de la UNESCO.
    """
    # Tokenizar la consulta original y filtrar palabras vacías y tokens no alfabéticos
    tokens = [
        word.lower() for word in word_tokenize(original_query, language='spanish')
        if word.lower() not in stop_words and word.isalpha()
    ]

    # Mapear cada token significativo a su lista de sinónimos de WordNet
    synonyms_map = defaultdict(list)
    for token in tokens:
        wordnet_synonyms = get_wordnet_synonyms(token)
        if wordnet_synonyms:
            synonyms_map[token].extend(wordnet_synonyms)
        synonyms_map[token] = list(set(synonyms_map[token])) # Asegurar unicidad

    # Preparar palabras para la combinación: palabras originales más sus sinónimos
    original_query_tokens = word_tokenize(original_query, language='spanish')
    words_for_combination = []
    for word in original_query_tokens:
        lower = word.lower()
        if lower in synonyms_map:
            # Incluir la palabra original y sus sinónimos para la combinación
            syns = synonyms_map[lower]
            words_for_combination.append([word] + syns)
        else:
            # Si no hay sinónimos, solo incluir la palabra original
            words_for_combination.append([word])

    # Generar todas las combinaciones posibles de palabras y sus sinónimos
    synonym_combinations = list(product(*words_for_combination))
    expanded_queries_wordnet = set()

    # Convertir combinaciones en frases y añadir al conjunto
    for combo in synonym_combinations:
        phrase = ' '.join(combo)
        if phrase.lower() != original_query.lower(): # Excluir la consulta original
            expanded_queries_wordnet.add(phrase)
        if len(expanded_queries_wordnet) >= max_results:
            break

    # Obtener expansiones adicionales del tesauro de la UNESCO
    thesaurus_expansions = get_thesaurus_phrases(original_query)

    # Devolver expansiones de WordNet (limitadas) y expansiones de Tesauro
    return list(expanded_queries_wordnet)[:max_results], thesaurus_expansions