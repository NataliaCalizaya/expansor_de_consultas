from django.shortcuts import render
# Importa las funciones renombradas desde los módulos refactorizados
from .expanded_queries import generate_expanded_queries
from .consultor import get_document_identifiers, build_corpus, find_in_corpus, get_highlighted_snippets

def interface(request):
    """
    Renderiza la página de la interfaz de búsqueda inicial.
    """
    return render(request, 'expansor/interface.html')

def find(request):
    """
    Maneja la solicitud de búsqueda: expande la consulta, recupera documentos,
    busca dentro de ellos y prepara los resultados para su visualización.
    """
    if request.method == "POST":
        # Obtener 'count' (número de documentos) de los datos POST, por defecto 5
        document_count = int(request.POST.get("cantidad", "5"))
        # Obtener la consulta original de los datos POST
        original_query = request.POST.get("consulta", "")

        # Si no se proporciona una consulta, renderizar la página de resultados con una consulta vacía
        if not original_query:
            print("DEBUG: No se proporcionó consulta, renderizando resultados vacíos.")
            return render(request, "expansor/results.html", {"consulta": original_query, "results": []})

        print(f"DEBUG: Consulta recibida: '{original_query}' (Solicitando {document_count} documentos)")

        # Paso 1: Expandir la consulta original usando WordNet y Tesauro
        wordnet_expansions, thesaurus_expansions = generate_expanded_queries(original_query)
        print(f"DEBUG: Expansiones WordNet generadas: {wordnet_expansions}")
        print(f"DEBUG: Expansiones Tesauro generadas: {thesaurus_expansions}")

        # Paso 2: Obtener identificadores de documentos y construir el corpus del BOE
        identifiers = get_document_identifiers(document_count)
        print(f"DEBUG: Identificadores de documentos obtenidos: {identifiers}")
        corpus = build_corpus(identifiers)
        print(f"DEBUG: Corpus construido (contiene {len(corpus)} documentos).")


        # Inicializar diccionarios/listas para almacenar los resultados
        document_results_map = {}
        queries_with_no_results = []

        # Buscar primero la consulta original en el corpus
        found_original_query_docs = find_in_corpus(corpus, original_query)
        if found_original_query_docs:
            highlighted_original_results = get_highlighted_snippets(found_original_query_docs, original_query)
            document_results_map[original_query] = highlighted_original_results
            print(f"DEBUG: Consulta original '{original_query}' encontró {len(highlighted_original_results)} resultados.")
        else:
            queries_with_no_results.append(original_query)
            print(f"DEBUG: Consulta original '{original_query}' no encontró resultados.")


        # Paso 3: Buscar en el corpus para cada consulta expandida y resaltar la coincidencia
        # Combinar todas las expansiones, asegurando que no haya duplicados y excluyendo la consulta original
        all_expanded_queries = [
            exp for exp in (wordnet_expansions + thesaurus_expansions)
            if exp.lower() != original_query.lower()
        ]
        print(f"DEBUG: Total de consultas expandidas a buscar (sin la original): {len(all_expanded_queries)}")

        for expanded_query in all_expanded_queries:
            found_expanded_query_docs = find_in_corpus(corpus, expanded_query)
            if found_expanded_query_docs:
                highlighted_expanded_results = get_highlighted_snippets(found_expanded_query_docs, expanded_query)
                document_results_map[expanded_query] = highlighted_expanded_results
                print(f"DEBUG: Consulta expandida '{expanded_query}' encontró {len(highlighted_expanded_results)} resultados.")
            else:
                queries_with_no_results.append(expanded_query)
                print(f"DEBUG: Consulta expandida '{expanded_query}' no encontró resultados.")

        print(f"\nDEBUG: Contenido final de 'resultados_documentos': {document_results_map}")
        print(f"DEBUG: Contenido final de 'sin_resultados': {queries_with_no_results}")
        print(f"DEBUG: Entregando datos al template 'expansor/results.html'")

        # Renderizar la página de resultados con todos los datos recopilados
        return render(request, "expansor/results.html", {
            "identifiers": identifiers, # IDs de los documentos incluidos en el corpus
            "original_query": original_query, # La consulta original
            "wordnet_expansions": wordnet_expansions, # Expansiones de WordNet
            "thesaurus_expansions": thesaurus_expansions, # Expansiones de Tesauro
            "document_results_map": document_results_map, # Diccionario de consultas a sus documentos encontrados/resaltados
            "queries_with_no_results": queries_with_no_results, # Lista de consultas que no produjeron resultados
        })

    # Si no es una solicitud POST (ej., solicitud GET inicial a /find),
    # renderizar la página de resultados con datos vacíos.
    print("DEBUG: Solicitud GET, renderizando resultados vacíos para la interfaz inicial.")
    return render(request, "expansor/results.html", {"consulta": "", "results": []})