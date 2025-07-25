import os
import mlflow
import mlflow.pyfunc
from sentence_transformers import SentenceTransformer
from mlflow.models.signature import infer_signature
from dotenv import load_dotenv

# === Load environment variables from .env ===
load_dotenv()
mlflow.set_tracking_uri("databricks")
mlflow.set_registry_uri("databricks-uc")
os.environ["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN")
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_PATH"))

# === Pre-download model and save to local folder ===
model_name = "distiluse-base-multilingual-cased-v1"
model_path = os.path.abspath("models/distiluse-base-multilingual-cased-v1") 
if not os.path.exists(model_path):
    print("Downloading SentenceTransformer model...")
    model = SentenceTransformer(model_name)
    model.save(model_path)
else:
    print("Using cached model at:", model_path)

# === Define custom wrapper class ===
class SentenceTransformerWrapper(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        from sentence_transformers import SentenceTransformer
        model_path = os.path.join(os.path.dirname(__file__), "distiluse-base-multilingual-cased-v1")
        self.model = SentenceTransformer(model_path)


    def predict(self, context, model_input):
        if isinstance(model_input, str):
            return self.model.encode([model_input])
        elif hasattr(model_input, 'iloc'):
            texts = model_input.iloc[:, 0].tolist() if len(model_input.shape) > 1 else model_input.tolist()
            return self.model.encode(texts)
        else:
            return self.model.encode(list(model_input))

# === Create wrapper and signature ===
artifacts = {"model_path": model_path}
wrapper_model = SentenceTransformerWrapper()
wrapper_model.load_context(type("Context", (), {"artifacts": artifacts})())

sample_input = ["MLflow embedding test", "This is a sentence."]
sample_output = wrapper_model.predict(None, sample_input)
signature = infer_signature(sample_input, sample_output)

# === Register in MLflow ===
with mlflow.start_run(run_name="Register SentenceTransformer Model") as run:
    mlflow.pyfunc.log_model(
        name="sentence_transformer_model",
        python_model=wrapper_model,
        artifacts=artifacts,
        signature=signature,
        #input_example=sample_input,
        registered_model_name="workspace.default.SentenceTransformerModel"
    )
