import os
import pickle
import mlflow
import mlflow.pyfunc
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set MLflow Tracking URI and authentication
mlflow.set_tracking_uri(os.getenv("DATABRICKS_HOST"))
os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")

# Set experiment in Databricks
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_PATH"))


### 1. Register TF-IDF Vectorizer ###
with open("app/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

with mlflow.start_run(run_name="Register TFIDF Vectorizer") as run:
    mlflow.log_param("model_type", "TF-IDF")
    mlflow.sklearn.log_model(
        sk_model=vectorizer,
        artifact_path="tfidf_vectorizer",
        registered_model_name="TFIDFVectorizer"
    )
    mlflow.log_artifact("app/vectorizer.pkl", artifact_path="original_pickle")


### 2. Register SentenceTransformer with Custom Wrapper ###
class SentenceTransformerWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

    def predict(self, context, model_input):
        return self.model.encode(model_input)

with mlflow.start_run(run_name="Register SentenceTransformer Model") as run:
    mlflow.log_param("model_type", "SentenceTransformer")
    mlflow.log_param("model_name", "distiluse-base-multilingual-cased-v1")
    
    mlflow.pyfunc.log_model(
        artifact_path="sentence_transformer",
        python_model=SentenceTransformerWrapper(),
        registered_model_name="SentenceTransformerModel"
    )




# # register_models.py
# import mlflow
# import pickle
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv
# import mlflow.pyfunc
# import os

# load_dotenv()

# mlflow.set_tracking_uri(os.getenv("DATABRICKS_HOST"))

# os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")


# # Load your models
# with open("app/vectorizer.pkl", "rb") as f:
#     vectorizer = pickle.load(f)

# model = SentenceTransformer("distiluse-base-multilingual-cased-v1")

# # Create experiment (optional)
# mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_PATH"))

# with mlflow.start_run(run_name="Registro dos Modelos TFIDF and SentenceTransformer") as run:
#     # Log and register TF-IDF
#     run_id_tfidf = mlflow.sklearn.log_model(
#         sk_model=vectorizer,
#         artifact_path="tfidf_vectorizer",
#         registered_model_name="TFIDFVectorizer"
#     ).run_id

#     # Log and register SentenceTransformer
#     run_id_sentence = mlflow.sentence_transformers.log_model(
#         model=model,
#         artifact_path="sentence_transformer",
#         registered_model_name="SentenceTransformerModel"
#     ).run_id

    
