import mlflow
from mlflow.tracking import MlflowClient

# Set the MLflow tracking URI to connect to the MLflow service
mlflow.set_tracking_uri("http://localhost:5000")

client = MlflowClient()

model_name = "TFIDFVectorizer"

try:
    # Get the latest version of the model
    latest_version = client.get_latest_versions(model_name, stages=["None"])[0].version
    print(f"Latest version of {model_name}: {latest_version}")

    # Transition the latest version to Production stage
    client.transition_model_version_stage(
        name=model_name,
        version=latest_version,
        stage="Production"
    )
    print(f"Successfully transitioned model {model_name} version {latest_version} to Production stage.")

except Exception as e:
    print(f"Error: {e}")
    print(f"Please ensure that a model named '{model_name}' exists in MLflow and that the MLflow tracking server is running.")
