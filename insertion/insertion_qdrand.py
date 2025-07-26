import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from threading import Thread
from sentence_transformers import SentenceTransformer
from app.collections_mongo import collection_applicants, collection_vagas
from qdrant_client.http.models import PointStruct
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.exceptions import ResponseHandlingException



model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

qdrant = QdrantClient(f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}")
#qdrant = QdrantClient(host="localhost", port=6333)

#qdrant.create_collection(collection_name="applicants", vectors_config=VectorParams(size=512, distance=Distance.COSINE))
#qdrant.create_collection(collection_name="vagas", vectors_config=VectorParams(size=512, distance=Distance.COSINE))

# def create_or_recreate_collection(collection_name: str, vector_size: int, distance_metric: Distance = Distance.COSINE):
#     print(f"Verificando coleção: {collection_name}")
#     try:
#         # Tenta deletar a coleção se ela já existir para garantir um estado limpo
#         if qdrant.collection_exists(collection_name=collection_name):
#             print(f"Coleção '{collection_name}' já existe. Deletando para recriar.")
#             qdrant.delete_collection(collection_name=collection_name)
#             # Pode ser necessário um pequeno delay para a coleção ser completamente deletada
#             time.sleep(2) # Ajuste conforme necessário
#     except UnexpectedResponse as e:
#         # Se houver um 404 (Not Found) ao tentar deletar uma coleção que não existe, está ok
#         # Ou se houver um 409 (Conflict) que signifique que ela já está em processo de exclusão
#         if e.status_code == 404:
#             print(f"Coleção '{collection_name}' não encontrada para deletar, continuando.")
#         elif e.status_code == 409:
#             print(f"Conflito ao tentar deletar '{collection_name}'. Pode estar em transição. Aguarde e tente novamente, ou verifique manualmente.")
#             # Se persistir, pode ser necessário verificar manualmente no console Qdrant
#             time.sleep(5) # Espere mais um pouco se houver conflito
#         else:
#             raise e # Relança outros erros inesperados

#     # Cria a coleção
#     qdrant.recreate_collection(
#         collection_name=collection_name,
#         vectors_config=VectorParams(size=vector_size, distance=distance_metric),
#     )
#     print(f"Coleção '{collection_name}' criada/recriada com sucesso.")

# Determine o tamanho do vetor do seu modelo
# Execute isso uma vez para obter o tamanho correto do embedding
# Lembre-se que o tamanho deve ser consistente com o modelo.encode()
# model = SentenceTransformer("distiluse-base-multilingual-cased-v1")
# sample_vector_size = model.get_sentence_embedding_dimension() # Ou um valor fixo se souber (ex: 768 para distiluse-base)

# # Função de inicialização que você chamará antes de popular
# def initialize_qdrant_collections():
#     create_or_recreate_collection("applicants", sample_vector_size)
#     create_or_recreate_collection("vagas", sample_vector_size)


BATCH_SIZE = 200


def qdrand_applicants():
    batch = []
    count = 0    
    for doc in collection_applicants.find({}, {
        "_id": 1, 
        "infos_basicas.nome":1, 
        "infos_basicas.email":1, 
        "infos_basicas.telefone":1,
        "informacoes_profissionais.certificacoes":1, 
        "formacao_e_idiomas.nivel_ingles": 1, 
        "formacao_e_idiomas.nivel_espanhol":1, 
        "cv_pt":1}):
        id = doc.get('_id', "")
        nome = doc.get('infos_basicas', {}).get("nome","")
        email = doc.get('infos_basicas', {}).get("email","")
        telefone = doc.get('infos_basicas', {}).get("telefone", "")
        certification = doc.get('informacoes_profissionais', {}).get("certificacoes","")
        education_en = doc.get('formacao_e_idiomas', {}).get("nivel_ingles","")
        education_es = doc.get('formacao_e_idiomas', {}).get("nivel_espanhol","")
        cv = doc.get('cv_pt', "")
        
        text = f"{certification} {education_en} {education_es} {cv}"
        
        vector = model.encode(text).tolist()

        payload = {"_id":id,
                "nome":nome,
                "email":email,
                "telefone":telefone   
        }

        batch.append(PointStruct( id=int(id), vector=vector, payload=payload))
            
        count += 1

        if len(batch) == BATCH_SIZE:
            # qdrant.upsert(collection_name="applicants", points=batch) comentado evitando a inserção infinita            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    qdrant.upsert(collection_name="applicants", points=batch)
                    break
                except ResponseHandlingException:
                    if attempt == max_retries - 1:
                        raise
                time.sleep(2)
            batch = []

            
    if batch:
        qdrant.upsert(collection_name='applicants', points=batch)

    print(f" Total de {count} aplicantes carregadas no Qdrant")


def qdrand_vagas():
    batch = []
    count = 0         
    for doc in collection_vagas.find({}, {
        "_id": 1,
        "informacoes_basicas.cliente":1,
        "informacoes_basicas.titulo_vaga":1,
        "perfil_vaga.pais":1, 
        "perfil_vaga.estado":1,
        "perfil_vaga.cidade":1, 
        "perfil_vaga.nivel profissional":1, 
        "perfil_vaga.nivel_academico" :1,
        "perfil_vaga.nivel_ingles":1,
        "perfil_vaga.nivel_espanhol":1,
        "perfil_vaga.areas_atuacao":1,
        "perfil_vaga.principais_atividades":1
        }):
        id = doc.get('_id', "")
        cliente = doc.get('informacoes_basicas', {}).get('cliente',"")
        titulo_vaga = doc.get('informacoes_basicas', {}).get('titulo_vaga', "")
        pais = doc.get('perfil_vaga', {}).get("pais","")
        estado = doc.get('perfil_vaga', {}).get("estado","")
        cidade = doc.get('perfil_vaga', {}).get("cidade","")
        n_prof = doc.get('perfil_vaga', {}).get("nivel profissional","")
        n_acad = doc.get('perfil_vaga', {}).get("nivel_academico","")
        n_en = doc.get('perfil_vaga', {}).get("nivel_ingles","")
        n_es = doc.get('perfil_vaga', {}).get("nivel_espanhol","")
        area = doc.get('perfil_vaga', {}).get("areas_atuacao","")
        atividades = doc.get('perfil_vaga', {}).get("principais_atividades","")

        full_text_vagas = f"{titulo_vaga} {pais} {estado} {n_prof} {n_acad} {n_en} {n_es} {area} {atividades}"
    
        vector = model.encode(full_text_vagas).tolist()

        payload = {"_id":id,
                "cliente":cliente,
                "titulo_vaga":titulo_vaga,
                "area":area,
                "pais": pais, 
                "estado": estado,
                "cidade": cidade
                }

        batch.append(PointStruct( id=int(id), vector=vector, payload=payload))
            
        count += 1

        if len(batch) == BATCH_SIZE:
            # qdrant.upsert(collection_name="vagas", points=batch) comentado evitando a inserção infinita            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    qdrant.upsert(collection_name="vagas", points=batch)
                    break
                except ResponseHandlingException:
                    if attempt == max_retries - 1:
                        raise
                time.sleep(2)
            batch = []
            
    if batch:
        qdrant.upsert(collection_name='vagas', points=batch)

    print(f"Total de {count} vagas carregadas no Qdrant")


# sync function
def sync_qdrant_periodically(interval:int=3600):
    while True:
        print('Sincronizando Qdrant com MongoDB')
        qdrand_applicants()
        qdrand_vagas()
        print("Sincronização concluída")
        time.sleep(interval)

def start_qdrant_background_sync(delay=120):
    def background():
        print("Initial Qdrant sync")
        qdrand_applicants()
        qdrand_vagas()
        print("Qdrant sync ready")
        time.sleep(delay)
        sync_qdrant_periodically()

    # Background periodic sync
    Thread(target=background, daemon=True).start()

if __name__ == '__main__':
    #initialize_qdrant_collections(),# Chame isso antes de qdrand_applicants/vagas
    qdrand_applicants()
    qdrand_vagas()