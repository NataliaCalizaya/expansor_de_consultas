import nltk

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

# Ejecutar cuando se importe este módulo
download_nltk()
