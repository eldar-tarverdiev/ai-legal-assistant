import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.memory.long_term import save_to_memory, search_memory

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from src.rag.retriever import search_documents, add_documents_to_qdrant
from src.rag.document_parser import parse_document
from src.monitoring.metrics import metrics_middleware, DOCUMENTS_PROCESSED
from src.utils.config import OLLAMA_BASE_URL

from src.agents.document_analyzer import DocumentAnalyzer
from src.agents.risk_detector import RiskDetector

app = FastAPI(
    title="AI Legal Assistant API",
    version="0.2.0",
    description="Интеллектуальный помощник для анализа договоров и compliance"
)

app.middleware("http")(metrics_middleware)

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0.1,
    base_url=OLLAMA_BASE_URL
)

template = """Ты - профессиональный корпоративный юрист-ассистент. 
Твоя задача - ответить на вопрос пользователя, строго опираясь на предоставленный контекст из документов.
Если в контексте нет нужной информации, так и скажи: "В предоставленных документах нет информации по этому вопросу".
Отвечай четко, по делу и на русском языке.

Контекст из документов:
{context}

Вопрос пользователя: {question}

Ответ:"""
prompt = ChatPromptTemplate.from_template(template)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
        {"context": lambda x: format_docs(x["docs"]), "question": lambda x: x["question"]}
        | prompt
        | llm
)

document_analyzer = DocumentAnalyzer()
risk_detector = RiskDetector()


class QueryRequest(BaseModel):
    question: str
    collection: str = "laws_database"
    top_k: int = 3


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list
    context: str


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_count: int
    collection: str


class AnalyzeContractRequest(BaseModel):
    file_path: str


class AnalyzeContractResponse(BaseModel):
    filename: str
    analysis: dict
    risks: dict


@app.get("/")
def read_root():
    return {
        "service": "AI Legal Assistant",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/search", response_model=QueryResponse)
def search_laws(request: QueryRequest):
    try:
        docs = search_documents(
            query=request.question,
            collection_name=request.collection,
            top_k=request.top_k
        )

        if not docs:
            return QueryResponse(
                question=request.question,
                answer="Информация не найдена в базе знаний.",
                sources=[],
                context=""
            )

        context_text = format_docs(docs)
        sources = list(set([doc.metadata.get("source", "unknown") for doc in docs]))

        response = rag_chain.invoke({"docs": docs, "question": request.question})

        return QueryResponse(
            question=request.question,
            answer=response.content,
            sources=sources,
            context=context_text[:500] + "..." if len(context_text) > 500 else context_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке запроса: {str(e)}")


@app.post("/upload")
def upload_document(file_path: str, collection: str = "laws_database"):
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Файл не найден: {file_path}")

        documents = parse_document(file_path)
        add_documents_to_qdrant(documents, collection)

        doc_type = os.path.splitext(file_path)[1].lower().replace(".", "")
        DOCUMENTS_PROCESSED.labels(document_type=doc_type).inc()

        return DocumentUploadResponse(
            filename=os.path.basename(file_path),
            chunks_count=len(documents),
            collection=collection
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки: {str(e)}")


@app.post("/analyze-contract", response_model=AnalyzeContractResponse)
def analyze_contract(request: AnalyzeContractRequest):
    try:
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"Файл не найден: {request.file_path}")

        documents = parse_document(request.file_path)
        full_text = "\n\n".join([doc.page_content for doc in documents])

        analysis = document_analyzer.analyze(full_text)
        risks = risk_detector.detect_risks(full_text)

        # 🧠 СОХРАНЯЕМ В ДОЛГОВРЕМЕННУЮ ПАМЯТЬ
        save_to_memory(
            filename=os.path.basename(request.file_path),
            analysis_summary=analysis.summary,
            risks_summary=risks.summary
        )

        return AnalyzeContractResponse(
            filename=os.path.basename(request.file_path),
            analysis=analysis.model_dump(),
            risks=risks.model_dump()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


class MemoryQueryRequest(BaseModel):
    query: str
    top_k: int = 3


class MemoryQueryResponse(BaseModel):
    query: str
    results: list


@app.post("/memory/query", response_model=MemoryQueryResponse)
def query_memory(request: MemoryQueryRequest):
    """Поиск по истории проанализированных договоров."""
    try:
        docs = search_memory(query=request.query, top_k=request.top_k)

        results = [
            {
                "filename": doc.metadata.get("filename", "unknown"),
                "content": doc.page_content
            }
            for doc in docs
        ]

        return MemoryQueryResponse(query=request.query, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска в памяти: {str(e)}")
