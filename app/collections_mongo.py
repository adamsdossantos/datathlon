import os
from pymongo import MongoClient

#criando client MongoDB
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://root:22410Ad4m5@localhost:27017/?authSource=admin'))

# creating a database MongoDB
decision_db = client['decision_db']
# creating collections MongoDB
collection_applicants = decision_db['applicants']
collection_vagas = decision_db['vagas']
collection_prospects = decision_db['prospects']


def corpus_applicants(collection:str=collection_applicants):

    corpus_applicants = []
    id_applicants = []
    for doc in collection_applicants.find({}, {
        "_id": 1, 
        "infos_basicas.nome":1, 
        "infos_basicas.email":1,
        "informacoes_profissionais.certificacoes":1, 
        "formacao_e_idiomas.nivel_ingles": 1, 
        "formacao_e_idiomas.nivel_espanhol":1, 
        "cv_pt":1}):
        
        id = doc.get('_id', "")
        nome = doc.get('infos_basicas', {}).get("nome","")
        email = doc.get('infos_basicas', {}).get("email","")
        certification = doc.get('informacoes_profissionais', {}).get("certificacoes","")
        education_en = doc.get('formacao_e_idiomas', {}).get("nivel_ingles","")
        education_es = doc.get('formacao_e_idiomas', {}).get("nivel_espanhol","")
        cv = doc.get('cv_pt', "")

        full_text = f"{id} {certification} {education_en} {education_es} {cv}"

        corpus_applicants.append(full_text)
        id_applicants.append(id)

    return corpus_applicants, id_applicants


def corpus_vagas(collection:str=collection_vagas):

    corpus_vagas = []
    id_vagas = []
    for doc in collection_vagas.find({}, {
        "_id": 1, 
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
        pais = doc.get('perfil_vaga', {}).get("pais","")
        estado = doc.get('perfil_vaga', {}).get("estado","")
        cidade = doc.get('perfil_vaga', {}).get("cidade","")
        n_prof = doc.get('perfil_vaga', {}).get("nivel profissional","")
        n_acad = doc.get('perfil_vaga', {}).get("nivel_academico","")
        n_en = doc.get('perfil_vaga', {}).get("nivel_ingles","")
        n_es = doc.get('perfil_vaga', {}).get("nivel_espanhol","")
        area = doc.get('perfil_vaga', {}).get("areas_atuacao","")
        atividades = doc.get('perfil_vaga', {}).get("principais_atividades","")

        full_text_vagas = f"{id} {pais} {cidade} {estado} {n_prof} {n_acad} {n_en} {n_es} {area} {atividades}"

        corpus_vagas.append(full_text_vagas)
        id_vagas.append(id)
        
    return corpus_vagas, id_vagas
    
 