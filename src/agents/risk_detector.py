from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

from src.utils.config import OLLAMA_BASE_URL
from src.rag.retriever import search_documents


class Risk(BaseModel):
    """Описание выявленного риска."""
    risk_level: str = Field(description="Уровень риска: низкий, средний, высокий")
    description: str = Field(description="Описание риска")
    contract_clause: str = Field(description="Цитата из договора")
    legal_reference: str = Field(description="Ссылка на закон или нормативный акт")
    recommendation: str = Field(description="Рекомендация по устранению риска")


class RiskDetectionResult(BaseModel):
    """Результат анализа рисков."""
    risks: List[Risk] = Field(description="Список выявленных рисков")
    overall_risk_level: str = Field(description="Общий уровень риска договора")
    summary: str = Field(description="Краткое резюме анализа")


class RiskDetector:
    """Агент для обнаружения рисков в договорах."""

    def __init__(self):
        self.llm = ChatOllama(
            model="qwen2.5:7b",
            temperature=0.1,
            base_url=OLLAMA_BASE_URL
        )
        self.parser = JsonOutputParser(pydantic_object=RiskDetectionResult)

        self.prompt = ChatPromptTemplate.from_template(
            """Ты - опытный юрист по compliance. Проанализируй договор и выяви риски, сравнив его условия с предоставленными законами и нормативными актами.

{format_instructions}

Договор:
{contract_text}

Релевантные законы и нормативные акты:
{legal_context}

Проанализируй договор и выяви все риски. Для каждого риска укажи уровень (низкий/средний/высокий), описание, цитату из договора, ссылку на закон и рекомендацию."""
        )

    def detect_risks(self, contract_text: str, top_k: int = 5) -> RiskDetectionResult:
        """Анализирует договор и выявляет риски."""
        # 1. Ищем релевантные законы через RAG
        legal_docs = search_documents(
            query=contract_text[:500],  # Используем начало договора как запрос
            collection_name="laws_database",
            top_k=top_k
        )

        legal_context = "\n\n".join([doc.page_content for doc in legal_docs])

        # 2. Анализируем риски
        chain = self.prompt | self.llm | self.parser

        result = chain.invoke({
            "contract_text": contract_text,
            "legal_context": legal_context,
            "format_instructions": self.parser.get_format_instructions()
        })

        return RiskDetectionResult(**result)