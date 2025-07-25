def setup_databricks_auth():
    """Setup Databricks authentication for both local and production environments"""
    
    # Check if required environment variables are set
    databricks_host = os.getenv("DATABRICKS_HOST")
    databricks_token = os.getenv("DATABRICKS_TOKEN")
    
    if not databricks_host:
        raise ValueError("DATABRICKS_HOST environment variable must be set")
    
    if not databricks_token:
        raise ValueError("DATABRICKS_TOKEN environment variable must be set")
    
    # Set environment variables (redundant but ensures they're available)
    os.environ["DATABRICKS_HOST"] = databricks_host
    os.environ["DATABRICKS_TOKEN"] = databricks_token
    
    try:
        w = WorkspaceClient()
        print(f"✓ Successfully authenticated to Databricks: {w.config.host}")
        return True
    except Exception as e:
        print(f"✗ Databricks authentication failed: {e}")
        raise

# Setup authentication
setup_databricks_auth()


# Load models with retry logic
def load_models_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Loading models (attempt {attempt + 1})...")
            vectorizer_new = mlflow.sklearn.load_model("models:/workspace.default.tfidfvectorizer@champion")
            model = mlflow.pyfunc.load_model("models:/workspace.default.sentencetransformermodel@champion")
            print("✓ Models loaded successfully")
            return vectorizer_new, model
        except Exception as e:
            print(f"✗ Model loading attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)

vectorizer_new, model = load_models_with_retry()
