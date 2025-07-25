import os
from qdrant_client import QdrantClient

qdrant = QdrantClient(f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}")