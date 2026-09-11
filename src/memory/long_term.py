from typing import List
from langchain_core.documents import Document
from src.rag.embeddings import get_embeddings
from src.utils.config import QDRANT_URL
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore

MEMORY_COLLECTION = "contract_memories"


def init_memory_collection():
    """Инициализирует коллекцию для долговременной памяти."""
    client = QdrantClient(url=QDRANT_URL)
    collections = [c.name for c in client.get_collections().collections]

    if MEMORY_COLLECTION not in collections:
        client.create_collection(
            collection_name=MEMORY_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"✅ Коллекция памяти '{MEMORY_COLLECTION}' создана")


def save_to_memory(filename: str, analysis_summary: str, risks_summary: str):
    """Сохраняет выжимку из анализа договора в память."""
    init_memory_collection()

    # Формируем богатый текстовый документ для семантического поиска
    memory_text = f"Документ: {filename}\nКраткое содержание: {analysis_summary}\nВыявленные риски: {risks_summary}"

    doc = Document(
        page_content=memory_text,
        metadata={"filename": filename, "type": "contract_analysis"}
    )

    embeddings = get_embeddings()
    vector_store = QdrantVectorStore.from_documents(
        documents=[doc],
        embedding=embeddings,
        collection_name=MEMORY_COLLECTION,
        url=QDRANT_URL
    )
    print(f"✅ Анализ '{filename}' сохранен в долговременную память")


def search_memory(query: str, top_k: int = 3) -> List[Document]:
    """Ищет в долговременной памяти по запросу пользователя."""
    init_memory_collection()
    embeddings = get_embeddings()

    vector_store = QdrantVectorStore.from_existing_collection(
        embedding=embeddings,
        collection_name=MEMORY_COLLECTION,
        url=QDRANT_URL
    )

    return vector_store.similarity_search(query, k=top_k)