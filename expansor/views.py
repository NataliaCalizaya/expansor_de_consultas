from django.shortcuts import render
from .expanded_queries import generate_expanded_queries
from .consultor import get_identifiers, join_corpus, find_in_corpus, mostrar_resultados

def interfaz(request):
    return render(request, 'expansor/interfaz.html')

def buscar(request):
    if request.method == "POST":
        count = int(request.POST.get("cantidad", "5"))  # Valor por defecto: 5
        consulta = request.POST.get("consulta", "")
        if not consulta:
            return render(request, "expansor/resultados.html", {"consulta": consulta, "resultados": []})

        # Paso 1: Expandir consulta
        expandidas_wordnet, expandidas_tesauro = generate_expanded_queries(consulta)

        # Paso 2: Obtener corpus del BOE
        identifiers = get_identifiers(count)
        corpus = join_corpus(identifiers)

        resultados_documentos = {}
        sin_resultados = []

        encontrados_original = find_in_corpus(corpus, consulta)
        if encontrados_original:
            resaltados = mostrar_resultados(encontrados_original, consulta)
            resultados_documentos[consulta] = resaltados
        else:
            sin_resultados.append(consulta)
        # Paso 3: Buscar en el corpus para cada consulta expandida y resaltar la coincidencia
        todas_expandidas = [
            exp for exp in (expandidas_wordnet + expandidas_tesauro)
            if exp.lower() != consulta.lower()
        ]

        for consulta_exp in todas_expandidas:
            encontrados = find_in_corpus(corpus, consulta_exp)
            if encontrados:
                resaltados = mostrar_resultados(encontrados, consulta_exp)
                resultados_documentos[consulta_exp] = resaltados
            else:
                sin_resultados.append(consulta_exp)

        return render(request, "expansor/resultados.html", {
            "identifiers": identifiers,
            "consulta": consulta,
            "expandidas_wordnet": expandidas_wordnet,
            "expandidas_tesauro": expandidas_tesauro,
            "resultados_documentos": resultados_documentos,
            "sin_resultados": sin_resultados,

        })

    return render(request, "expansor/resultados.html", {"consulta": "", "resultados": []})
