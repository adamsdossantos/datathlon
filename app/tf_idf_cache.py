import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pickle
from datetime import datetime
from threading import Thread
from app.collections_mongo import corpus_applicants, corpus_vagas
from dotenv import load_dotenv

import mlflow


# === Load environment variables from .env ===
load_dotenv()
os.environ["DATABRICKS_HOST"] = os.getenv("DATABRICKS_HOST")
os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")
print("TOKEN:", os.getenv("DATABRICKS_TOKEN"))
print("HOST:", os.getenv("DATABRICKS_HOST"))

mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")
#vectorizer = mlflow.sklearn.load_model("models:/workspace.default.tfidfvectorizer@champion")

path_to_vectorizer = os.path.join("app", "vectorizer.pkl")
with open(path_to_vectorizer, "rb") as f:
   vectorizer = pickle.load(f)

# with open("app/vectorizer.pkl", "rb") as f:
#     vectorizer_new = pickle.load(f)


# GLOBAL CACHE OBJECTS
cache_applicants = {
    "id_applicants": [],
    "texts": [],
    "vectorized": None,
    "last_updated": None
}

cache_vagas = {
    "id_vagas": [],
    "texts": [],
    "vectorized": None,
    "last_updated": None
}

# LOADERS
def update_cache_applicants():
    texts, ids = corpus_applicants(None)
    cache_applicants["id_applicants"] = ids
    cache_applicants["texts"] = texts
    cache_applicants["vectorized"] = vectorizer.transform(texts)
    cache_applicants["last_updated"] = datetime.now()

def update_cache_vagas():
    texts, ids = corpus_vagas(None)
    cache_vagas["id_vagas"] = ids
    cache_vagas["texts"] = texts
    cache_vagas["vectorized"] = vectorizer.transform(texts)
    cache_vagas["last_updated"] = datetime.now()

# BACKGROUND THREADS
def refresh_all_caches_periodically(interval=3600):
    while True:
        print("Refreshing TF-IDF caches...")
        update_cache_applicants()
        update_cache_vagas()
        print("Caches refreshed.")
        time.sleep(interval)

def start_background_refresh(delay=120):
    def background():
        print("TF-IDF cache load")
        update_cache_applicants()
        update_cache_vagas()
        print("TF_IDF cache ready")
        time.sleep(delay)
        refresh_all_caches_periodically()
    Thread(target=background, daemon=True).start()
