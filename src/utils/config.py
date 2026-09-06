import os
from dotenv import load_dotenv

load_dotenv()

# URLs сервисов (из переменных окружения Docker)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Модели
LLM_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# RAG параметры
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K = 3

# Коллекции Qdrant
LAWS_COLLECTION = "laws_database"
CONTRACTS_COLLECTION = "contracts_memory"