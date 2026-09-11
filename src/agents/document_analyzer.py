from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

from src.utils.config import OLLAMA_BASE_URL


class ContractAnalysis(BaseModel):
    """Структурированный результат анализа договора."""
    contract_type: str = Field(description="Тип договора (трудовой, аренды, поставки, услуг и т.д.)")
    parties: List[str] = Field(description="Стороны договора")
    key_dates: dict = Field(description="Ключевые даты (подписание, начало, окончание)")
    financial_terms: Optional[str] = Field(description="Финансовые условия (суммы, платежи)")
    obligations: List[str] = Field(description="Основные обязательства сторон")
    summary: str = Field(description="Краткое содержание договора")


class DocumentAnalyzer:
    """Агент для анализа документов и извлечения структурированной информации."""

    def __init__(self):
        self.llm = ChatOllama(
            model="qwen2.5:7b",
            temperature=0.1,
            base_url=OLLAMA_BASE_URL
        )
        self.parser = JsonOutputParser(pydantic_object=ContractAnalysis)

        self.prompt = ChatPromptTemplate.from_template(
            """Ты - профессиональный юрист-аналитик. Проанализируй следующий договор и извлеки из него структурированную информацию.

{format_instructions}

Договор:
{document_text}

Проанализируй договор и верни JSON со всей запрошенной информацией. Если какая-то информация не найдена, укажи "не указано"."""
        )

    def analyze(self, document_text: str) -> ContractAnalysis:
        """Анализирует текст договора и возвращает структурированный результат."""
        chain = self.prompt | self.llm | self.parser

        result = chain.invoke({
            "document_text": document_text,
            "format_instructions": self.parser.get_format_instructions()
        })

        return ContractAnalysis(**result)