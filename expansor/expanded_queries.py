import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
import string
from itertools import product
from collections import defaultdict
from .tesauro_expanded import consultar_tesauro_unesco

# Descargar recursos necesarios de NLTK (solo la primera vez)
def download_nltk():
    recursos = {
        'punkt': 'tokenizers/punkt',
        'wordnet': 'corpora/wordnet',
        'stopwords': 'corpora/stopwords',
    }
    for nombre, ruta in recursos.items():
        try:
            nltk.data.find(ruta)
            print(f"✔️ '{nombre}' ya está disponible.")
        except LookupError:
            print(f"⬇️ Descargando '{nombre}'...")
            nltk.download(nombre)

download_nltk()

# Stopwords y puntuación
STOP_WORDS = set(nltk.corpus.stopwords.words('spanish') + list(string.punctuation))


def expand_with_synonyms(word):
    """Obtiene sinónimos usando WordNet para una palabra."""
    synonyms = set()
    for syn in wordnet.synsets(word, lang='spa'):
        for lemma in syn.lemmas('spa'):
            synonym = lemma.name().replace('_', ' ').lower()
            if synonym != word and ' ' not in synonym:
                synonyms.add(synonym)
    return list(synonyms)


def expand_with_tesaurus(query, max_results=15):
    """Devuelve hasta `max_results` frases del tesauro UNESCO relacionadas con la consulta."""
    tesauro_phrases = []
    try:
        resultados = consultar_tesauro_unesco(query.lower())
        for seccion in resultados:
            tesauro_phrases.extend(resultados[seccion])
    except Exception as e:
        print(f"❗ Error al consultar el tesauro para la frase '{query}': {e}")

    return list(set(tesauro_phrases))[:max_results]



def generate_expanded_queries(original_query, stop_words=STOP_WORDS, max_results=15):
    """
    Genera combinaciones de sinónimos por palabra (WordNet),
    y agrega frases relacionadas por tesauro (UNESCO) sin combinarlas.
    """
    # Tokenizar y filtrar stopwords
    tokens = [
        word.lower() for word in word_tokenize(original_query, language='spanish')
        if word.lower() not in stop_words and word.isalpha()
    ]

    synonyms_dict = defaultdict(list)
    for token in tokens:
        wn_synonyms = expand_with_synonyms(token)
        if wn_synonyms:
            synonyms_dict[token].extend(wn_synonyms)
        synonyms_dict[token] = list(set(synonyms_dict[token]))

    # Armar combinaciones
    original_tokens = word_tokenize(original_query, language='spanish')
    words_to_expand = []
    for word in original_tokens:
        lower = word.lower()
        if lower in synonyms_dict:
            syns = synonyms_dict[lower]
            words_to_expand.append([word] + syns)
        else:
            words_to_expand.append([word])

    synonym_combinations = list(product(*words_to_expand))
    expanded_queries = set()

    for combo in synonym_combinations:
        phrase = ' '.join(combo)
        if phrase.lower() != original_query.lower():
            expanded_queries.add(phrase)
        if len(expanded_queries) >= max_results:
            break

    tesauro_expansions = expand_with_tesaurus(original_query)

    return list(expanded_queries)[:max_results], tesauro_expansions
 