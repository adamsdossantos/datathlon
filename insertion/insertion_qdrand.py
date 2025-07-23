import time
from threading import Thread
from app.collection_qdrant import qdrant
from sentence_transformers import SentenceTransformer
from app.collections_mongo import collection_applicants, collection_vagas
from qdrant_client.http.models import PointStruct

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

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
            qdrant.upsert(collection_name="applicants", points=batch)
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
            qdrant.upsert(collection_name="vagas", points=batch)
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

