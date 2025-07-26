import os
from qdrant_client import QdrantClient

qdrant = QdrantClient(
    url=f"http://{os.getenv('QDRANT_HOST', 'localhost')}:{os.getenv('QDRANT_PORT', '6333')}",
    timeout=60,
    prefer_grpc=False,
    https=False
)