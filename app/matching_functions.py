import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mlflow
import traceback
import time
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.collections_mongo import collection_applicants, collection_vagas
from app.collection_qdrant import qdrant
from app.tf_idf_cache import cache_applicants, cache_vagas
from qdrant_client.http.exceptions import ResponseHandlingException


from dotenv import load_dotenv

path_to_vectorizer = os.path.join("models", "tfidf_vectorizer.pkl")
with open(path_to_vectorizer, "rb") as f:
   vectorizer_new = pickle.load(f)

#with open("app/vectorizer.pkl", "rb") as f:
#     vectorizer_new = pickle.load(f)

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

# === Load environment variables from .env ===
load_dotenv()
os.environ["DATABRICKS_HOST"] = os.getenv("DATABRICKS_HOST")
os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")
print("TOKEN:", os.getenv("DATABRICKS_TOKEN"))
print("HOST:", os.getenv("DATABRICKS_HOST"))

mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")
#mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_PATH"))

mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_PATH", "/Users/contact.adams.souza@gmail.com/Matching_Experiment"))

# Add a small delay to ensure authentication is fully established
time.sleep(5)

#vectorizer_new = mlflow.sklearn.load_model("models:/workspace.default.tfidfvectorizer@champion")
#model = mlflow.pyfunc.load_model("models:/workspace.default.sentencetransformermodel@champion")

def qdrant_retry_wrapper(func, *args, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except ResponseHandlingException as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = 2 ** attempt
            time.sleep(wait_time)


def vagas_match(job_id:str, model:object=model, vectorizer:object = vectorizer_new, alpha:float=0.3, top_n:int=5, version:str="1.0"):
    """
    Analisa o corpus das vagas e associa aos top-n candidatos com mais adequação
    """
    try:
        # coletando dados do MongoDB
        job_doc = collection_vagas.find_one({"_id":str(job_id)}, {
                                            "_id": 1,
                                            "informacoes_basicas.cliente":1,
                                            "informacoes_basicas.titulo_vaga":1 ,
                                            "perfil_vaga.pais":1,
                                            "perfil_vaga.estado":1,
                                            "perfil_vaga.cidade":1,
                                            "perfil_vaga.nivel profissional":1,
                                            "perfil_vaga.nivel_academico" :1,
                                            "perfil_vaga.nivel_ingles":1,
                                            "perfil_vaga.nivel_espanhol":1,
                                            "perfil_vaga.areas_atuacao":1,
                                            "perfil_vaga.principais_atividades":1
                                            })

        if not job_doc:
            return []

        id = job_doc.get('_id', "")
        cliente = job_doc.get('informacoes_basicas', {}).get('cliente',"")
        titulo_vaga = job_doc.get('informacoes_basicas', {}).get('titulo_vaga', "")
        solicitante_cliente = job_doc.get('informacoes_basicas', {}).get("solicitante_cliente",""),
        pais = job_doc.get('perfil_vaga', {}).get("pais","")
        estado = job_doc.get('perfil_vaga', {}).get("estado","")
        cidade = job_doc.get('perfil_vaga', {}).get("cidade","")
        n_prof = job_doc.get('perfil_vaga', {}).get("nivel profissional","")
        n_acad = job_doc.get('perfil_vaga', {}).get("nivel_academico","")
        n_en = job_doc.get('perfil_vaga', {}).get("nivel_ingles","")
        n_es = job_doc.get('perfil_vaga', {}).get("nivel_espanhol","")
        area = job_doc.get('perfil_vaga', {}).get("areas_atuacao","")
        atividades = job_doc.get('perfil_vaga', {}).get("principais_atividades","")

        # corpus para embedding
        job_text = f"{id} {pais} {estado} {cidade} {n_prof} {n_acad} {n_en} {n_es} {area} {atividades}"

        # vectorização para tf-idf + consine similarity
        vectorized_job = vectorizer.transform([job_text])
        similar_job = cosine_similarity(cache_applicants["vectorized"], vectorized_job)

        # dicionario de similaridade tf-idf
        tfidf_scores = {
            str(cache_applicants["id_applicants"][i]): similar_job[i] for i in range(len(similar_job))
        }

        # vectorização do corpus para sentence transformer + Qdrant
        qdrant_vector_job = model.encode(job_text)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                results = qdrant_retry_wrapper(qdrant.query_points, collection_name="applicants", query=qdrant_vector_job, limit=20)
                break
            except ResponseHandlingException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

        # normalizando os scores
        tfidf_max = max(tfidf_scores.values()) if tfidf_scores else 1
        tfidf_scores = {k: v / tfidf_max for k, v in tfidf_scores.items()}

        qdrant_scores = {str(item.payload["_id"]):item.score for item in results.points}

        qdrant_max = max(qdrant_scores.values()) if qdrant_scores else 1
        qdrant_scores = {k: v / qdrant_max for k, v in qdrant_scores.items()}

        #combinando os scores
        combined_scores = []
        for _id in set(tfidf_scores) & set(qdrant_scores):
            combined = alpha * tfidf_scores[_id] + (1- alpha) * qdrant_scores[_id]
            combined_scores.append((_id,combined.item()))

        # sorting and display os scores combinados
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = combined_scores[:top_n]

        # Log parameters
        if mlflow.active_run() is None:
            with mlflow.start_run(run_name="Vagas Match - SUCCESS") as run:
                mlflow.log_param("job_id", job_id)
                mlflow.log_param("job_id", job_id)
                mlflow.log_param("alpha", alpha)
                mlflow.log_param("top_n", top_n)
                mlflow.log_param("version", version)

                # Log metrics
                mlflow.log_metric("tfidf_max", tfidf_max.item() if hasattr(tfidf_max, 'item') else tfidf_max)
                mlflow.log_metric("qdrant_max", qdrant_max)
                if combined_scores:
                    mlflow.log_metric("combined_max", max(combined_scores, key=lambda x: x[1])[1])

                #log models
                #mlflow.sklearn.log_model(sk_model=vectorizer_new, name="TFIDFVectorizer")
                #mlflow.sentence_transformers.log_model(model=model, name="SentenceTransformerModel")

                # Set tags
                mlflow.set_tag("status", "success")

        # payload do Qdrant
        qdrant_map = {
            str(p.payload["_id"]): p.payload for p in results.points
        }

        # resposta
        vaga_info = {
            "_id": id,
            "titulo_vaga": titulo_vaga,
            "cliente": cliente,
            "solicitante_cliente": solicitante_cliente,
        }

        top_applicants = []
        for _id, score in top_matches:
            payload = qdrant_map.get(_id, {})
            top_applicants.append({
                "_id" : _id,
                "nome" : payload.get("nome", ""),
                "email" : payload.get("email", ""),
                "telefone":payload.get("telefone",""),
                "score" : round(score, 3)
            })

        output = [{"vaga":vaga_info, "top_applicants":top_applicants}]
        return output

    except Exception as e:
        with mlflow.start_run(run_name="Vagas Match - FAILED") as run:
            mlflow.log_param("job_id", job_id)
            mlflow.log_param("alpha", alpha)
            mlflow.log_param("top_n", top_n)
            mlflow.log_param("version", version)
            mlflow.set_tag("status", "failed")
            mlflow.set_tag("error_message", str(e))
            mlflow.set_tag("error_traceback", traceback.format_exc())
        raise e

def applicants_match(applicant_id:str, model:object=model, vectorizer:object=vectorizer_new, alpha:float=0.3, top_n:int=5, version:str="1.0"):
    """
    Analisa o corpus dos candidatos e os associa às top-n vagas com mais adequação
    """
    try:
        # coletando dados do MongoDB
        applicants_doc = collection_applicants.find_one({"_id":str(applicant_id)}, {
                                                        "_id": 1,
                                                        "infos_basicas.nome":1,
                                                        "infos_basicas.email":1,
                                                        "infos_basicas.telefone":1,
                                                        "informacoes_profissionais.certificacoes":1,
                                                        "formacao_e_idiomas.nivel_ingles": 1,
                                                        "formacao_e_idiomas.nivel_espanhol":1,
                                                        "cv_pt":1
                                                        })

        if not applicants_doc:
            return []

        id = applicants_doc.get('_id', "")
        nome = applicants_doc.get('infos_basicas', {}).get("nome","")
        email = applicants_doc.get('infos_basicas', {}).get("email","")
        telefone = applicants_doc.get('infos_basicas', {}).get("telefone", "")
        certification = applicants_doc.get('informacoes_profissionais', {}).get("certificacoes","")
        education_en = applicants_doc.get('formacao_e_idiomas', {}).get("nivel_ingles","")
        education_es = applicants_doc.get('formacao_e_idiomas', {}).get("nivel_espanhol","")
        cv = applicants_doc.get('cv_pt', "")

        # corpus para embedding
        applicant_text = f"{certification} {education_en} {education_es} {cv}"

        # vectorização para tf-idf + consine similarity
        vectorized_applicant = vectorizer.transform([applicant_text])
        similar_applicant = cosine_similarity(cache_vagas["vectorized"], vectorized_applicant)

        # dicionario de similaridade tf-idf
        tfidf_scores = {
            str(cache_vagas["id_vagas"][i]):similar_applicant[i] for i in range(len(similar_applicant))
        }

        # vectorização do corpus para sentence transformer + Qdrant
        qdrant_vector_applicant = model.encode(applicant_text)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                results = qdrant_retry_wrapper(qdrant.query_points, collection_name="vagas", query=qdrant_vector_applicant, limit=20)
                break
            except ResponseHandlingException:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

        # normalizando os scores
        tfidf_max = max(tfidf_scores.values()) if tfidf_scores else 1
        tfidf_scores = {k: v / tfidf_max for k, v in tfidf_scores.items()}

        qdrant_scores = {str(item.payload["_id"]):item.score for item in results.points}

        qdrant_max = max(qdrant_scores.values()) if qdrant_scores else 1
        qdrant_scores = {k: v / qdrant_max for k, v in qdrant_scores.items()}

        #combinando os scores
        combined_scores = []
        for _id in set(tfidf_scores) & set(qdrant_scores):
            combined = alpha * tfidf_scores[_id] + (1- alpha) * qdrant_scores[_id]
            combined_scores.append((_id,combined.item()))

        # sorting and display os scores combinados
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        top_matches = combined_scores[:top_n]

        # tracking com MLFlow
        if mlflow.active_run() is None:
            with mlflow.start_run(run_name="Applicants Match - SUCCESS") as run:
            # Log parameters
                mlflow.log_param("applicant_id", applicant_id)
                mlflow.log_param("alpha", alpha)
                mlflow.log_param("top_n", top_n)
                mlflow.log_param("version", version)
                #mlflow.log_param("model_name_qdrant",model)
                #mlflow.log_param("model_name_tfidf",vectorizer)


                # Log metrics
                mlflow.log_metric("tfidf_max", tfidf_max.item() if hasattr(tfidf_max, 'item') else tfidf_max)
                mlflow.log_metric("qdrant_max", qdrant_max)
                if combined_scores:
                    mlflow.log_metric("combined_max", max(combined_scores, key=lambda x: x[1])[1])
                
                #log models
                #mlflow.sklearn.log_model(sk_model=vectorizer_new, name="TFIDFVectorizer")
                #mlflow.sentence_transformers.log_model(model=model, name="SentenceTransformerModel")

                # Set tags
                mlflow.set_tag("status", "success")

        # payload do Qdrant
        qdrant_map = {
            str(p.payload["_id"]): p.payload for p in results.points
        }

        # resposta
        applicant_info = {
                "_id" : id,
                "nome" : nome,
                "email" : email,
                "telefone":telefone,
        }

        top_vagas = []
        for _id, score in top_matches:
            payload = qdrant_map.get(_id, {})
            top_vagas.append({
                 "_id": _id,
                "titulo_vaga": payload.get("titulo_vaga", ""),
                "cliente": payload.get("cliente", ""),
                "score": round(score, 3)
            })

        output = [{"applicant":applicant_info, "top_vagas":top_vagas}]
        return output

    except Exception as e:
        with mlflow.start_run(run_name="Applicants Match - FAILED") as run:
            mlflow.log_param("applicant_id", applicant_id)
            mlflow.log_param("alpha", alpha)
            mlflow.log_param("top_n", top_n)
            mlflow.log_param("version", version)
            mlflow.set_tag("status", "failed")
            mlflow.set_tag("error_message", str(e))
            mlflow.set_tag("error_traceback", traceback.format_exc())
        raise e

# if __name__ == "__main__":
#     vagas_match, applicants_match = vagas_match, applicants_match
#     start_background_refresh()
