from typing import List
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.documents import Document

from src.rag.embeddings import get_embeddings
from src.utils.config import QDRANT_URL, LAWS_COLLECTION, CHUNK_SIZE, CHUNK_OVERLAP


def initialize_qdrant_collection(collection_name: str, vector_size: int = 384):
    """Создает коллекцию в Qdrant, если она не существует."""
    client = QdrantClient(url=QDRANT_URL)

    collections = [c.name for c in client.get_collections().collections]

    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"✅ Коллекция '{collection_name}' создана")
    else:
        print(f"ℹ️  Коллекция '{collection_name}' уже существует")

    return client


def get_vector_store(collection_name: str = LAWS_COLLECTION) -> QdrantVectorStore:
    """Возвращает векторное хранилище Qdrant."""
    embeddings = get_embeddings()

    return QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=collection_name,
        url=QDRANT_URL,
    )


def add_documents_to_qdrant(
        documents: List[Document],
        collection_name: str = LAWS_COLLECTION
) -> None:
    """Добавляет документы в Qdrant."""
    initialize_qdrant_collection(collection_name)
    vector_store = get_vector_store(collection_name)
    vector_store.add_documents(documents)
    print(f"✅ Добавлено {len(documents)} документов в коллекцию '{collection_name}'")


def search_documents(query: str, collection_name: str = LAWS_COLLECTION, top_k: int = 3) -> List[Document]:
    """Ищет релевантные документы по запросу."""
    vector_store = get_vector_store(collection_name)
    return vector_store.similarity_search(query, k=top_k)