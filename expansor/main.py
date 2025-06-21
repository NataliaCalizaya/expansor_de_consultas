from .expanded_queries import generate_expanded_queries
from .consultor import get_identifiers, join_corpus, find_in_corpus, mostrar_resultados
from typing import Dict  # Importación necesaria para las anotaciones de tipo
import time
# def mostrar_resultados(results):
#     #Muestra los resultados de búsqueda de forma organizada
#     if not results:
#         print("No se encontraron documentos para esta consulta")
#         return
    
#     for doc_id, texto in results.items():
#         print(f"\n{'=================================================================='}")
#         print(f"Documento ID: {doc_id}")
#         print(f"URL completo: https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{doc_id}/texto")
#         print(f"Extracto relevante:")
        
#         # Mostrar fragmento con los primeros 200 caracteres
#         if len(texto) > 200:
#             fragmento = (texto[:200] + '...') 
#         else: 
#             fragmento = texto
#         print(fragmento)
#         print(f"{'====================================================================='}\n")

def main():
    # Paso 1: Obtener identificadores de legislación
    print("Obteniendo identificadores de legislación del BOE...")
    identifiers = get_identifiers()
    
    if not identifiers:
        print("No se pudieron obtener identificadores. Saliendo...")
        return
    
    print(f"\nIdentificadores obtenidos: {identifiers}")

    # Paso 2: Construir corpus con los textos
    print("\nConstruyendo corpus de documentos...")
    corpus = join_corpus(identifiers)
    
    if not corpus:
        print("No se pudo construir el corpus. Saliendo...")
        return
    
    print(f"\nCorpus construido con {len(corpus)} documentos")

    # Paso 3: Obtener consulta del usuario
    while True:
        consulta_original = input("\nIngrese su consulta (o 'salir' para terminar): ").strip()
        
        if consulta_original.lower() == 'salir':
            break
        
        # Paso 4: Expandir consulta
        consultas_expandidas = generate_expanded_queries(consulta_original)
        
        print("\nConsultas expandidas generadas:")
        for i, consulta in enumerate(consultas_expandidas, 1):
            print(f"{i}. {consulta}")
        
        # Paso 5: Buscar en el corpus
        print("\nRealizando búsquedas...")
        for consulta in consultas_expandidas:
            print(f"\nBuscando: '{consulta}'")
            resultados = find_in_corpus(corpus, consulta)
            mostrar_resultados(resultados)
            
            time.sleep(1)  # Espera para no saturar la API

if __name__ == "__main__":
    
    main()
    
