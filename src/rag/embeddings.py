from langchain_huggingface import HuggingFaceEmbeddings
from src.utils.config import EMBEDDING_MODEL


def get_embeddings() -> HuggingFaceEmbeddings:
    """Возвращает многоязычную модель эмбеддингов."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )