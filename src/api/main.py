import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.rag.retriever import search_documents, add_documents_to_qdrant
from src.rag.document_parser import parse_document
from src.monitoring.metrics import metrics_middleware, DOCUMENTS_PROCESSED

app = FastAPI(
    title="AI Legal Assistant API",
    version="0.1.0",
    description="Интеллектуальный помощник для анализа договоров и compliance"
)

# Middleware
app.middleware("http")(metrics_middleware)


# === Схемы данных ===

class QueryRequest(BaseModel):
    question: str
    collection: str = "laws_database"
    top_k: int = 3


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list
    context: str  # Для отладки (потом уберем)


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_count: int
    collection: str


# === Эндпоинты ===

@app.get("/")
def read_root():
    return {
        "service": "AI Legal Assistant",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    """Эндпоинт для Prometheus."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/search", response_model=QueryResponse)
def search_laws(request: QueryRequest):
    """Поиск по базе законов."""
    try:
        docs = search_documents(
            query=request.question,
            collection_name=request.collection,
            top_k=request.top_k
        )

        if not docs:
            return QueryResponse(
                question=request.question,
                answer="Информация не найдена в базе законов.",
                sources=[],
                context=""
            )

        # Формируем контекст
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))

        # Пока просто возвращаем контекст (позже подключим LLM)
        answer = f"Найдено {len(docs)} релевантных фрагментов. Полный ответ будет доступен после подключения LLM-агента."

        return QueryResponse(
            question=request.question,
            answer=answer,
            sources=sources,
            context=context[:500] + "..." if len(context) > 500 else context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")


@app.post("/upload")
def upload_document(file_path: str, collection: str = "laws_database"):
    """Загружает документ в векторную базу."""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Файл не найден: {file_path}")

        documents = parse_document(file_path)
        add_documents_to_qdrant(documents, collection)

        # Метрика
        doc_type = os.path.splitext(file_path)[1].lower().replace(".", "")
        DOCUMENTS_PROCESSED.labels(document_type=doc_type).inc()

        return DocumentUploadResponse(
            filename=os.path.basename(file_path),
            chunks_count=len(documents),
            collection=collection
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")