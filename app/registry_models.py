import os
import pickle
import mlflow
import mlflow.pyfunc
from sentence_transformers import SentenceTransformer
from mlflow.models.signature import infer_signature
from dotenv import load_dotenv

model = SentenceTransformer("distiluse-base-multilingual-cased-v1")
model.save("models/distiluse-base-multilingual-cased-v1")

# Load environment variables from .env
load_dotenv()

# Set MLflow Tracking URI and authentication
mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")     # For Unity Catalog model registry


os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")

# Set experiment in Databricks
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_PATH"))


### 1. Register TF-IDF Vectorizer ###
with open("app/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Create sample data for signature inference
sample_texts = ["Sample job description with skills and requirements", "Another sample text for vectorization"]
sample_output = vectorizer.transform(sample_texts)

# Infer signature for TF-IDF vectorizer
tfidf_signature = infer_signature(sample_texts, sample_output)

with mlflow.start_run(run_name="Register TFIDF Vectorizer") as run:
    mlflow.log_param("model_type", "TF-IDF")
    mlflow.sklearn.log_model(
        sk_model=vectorizer,
        name="tfidf_vectorizer",
        signature=tfidf_signature,
        registered_model_name="workspace.default.TFIDFVectorizer"
    )
    mlflow.log_artifact("app/vectorizer.pkl", artifact_path="original_pickle")


### 2. Register SentenceTransformer with Custom Wrapper ###
class SentenceTransformerWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.model = SentenceTransformer(context.artifacts["model_path"])

    def predict(self, context, model_input):
        # Handle both single strings and lists of strings
        if isinstance(model_input, str):
            return self.model.encode([model_input])
        elif hasattr(model_input, 'iloc'):  # pandas DataFrame/Series
            # Convert pandas input to list of strings
            texts = model_input.iloc[:, 0].tolist() if len(model_input.shape) > 1 else model_input.tolist()
            return self.model.encode(texts)
        else:
            # Assume it's already a list-like object
            return self.model.encode(list(model_input))

# Create sample data for signature inference
sample_input = ["Sample text for embedding", "Another sample for sentence transformer"]
wrapper_model = SentenceTransformerWrapper()

# Load the model context manually for signature inference
class MockContext:
    pass

wrapper_model.load_context(MockContext())
sample_embeddings = wrapper_model.predict(None, sample_input)

# Infer signature for SentenceTransformer
st_signature = infer_signature(sample_input, sample_embeddings)

with mlflow.start_run(run_name="Register SentenceTransformer Model") as run:
    mlflow.log_param("model_type", "SentenceTransformer")
    mlflow.log_param("model_name", "distiluse-base-multilingual-cased-v1")
    
    mlflow.pyfunc.log_model(
        name="sentence_transformer",
        python_model=SentenceTransformerWrapper(),
        signature=st_signature,
        registered_model_name="workspace.default.SentenceTransformerModel"
    )



