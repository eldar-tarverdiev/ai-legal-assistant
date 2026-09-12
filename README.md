# ⚖️ AI Legal Assistant: Мультиагентная система для анализа договоров и compliance

**Enterprise-grade AI-система с долговременной памятью для автоматизации юридического аудита и анализа контрактов.**

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-Multi--Agent-orange?logo=langchain)
![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-red?logo=qdrant)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)
![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-orange?logo=prometheus)

---

## 📋 Описание проекта

Полноценная мультиагентная AI-система, которая читает юридические документы, извлекает структурированные данные, выявляет правовые риски путем сравнения с актуальной базой законов и **помнит историю своих анализов** благодаря реализованной долговременной эпизодической памяти.

### 🎯 Бизнес-ценность
- ⏱️ **Сокращение времени аудита:** Анализ сложного договора за 15 секунд вместо 2-3 часов ручной работы юриста.
- 🛡️ **Снижение правовых рисков:** Автоматическое выявление противоречий с действующим законодательством (ТК РФ, ГК РФ).
- 🧠 **Контекстная память:** Система помнит предыдущие проверки и может отвечать на ретроспективные вопросы ("Какие риски были в прошлом договоре?").
- 🔒 **On-Premise & Zero Cost:** Полная приватность данных. Локальная LLM (Qwen 2.5 через Ollama) и векторная БД не требуют платных API и не передают конфиденциальные данные вовне.

---

## 📂 Структура проекта

```text
├── src/
│   ├── agents/                 # Логика специализированных агентов
│   │   ├── document_analyzer.py# Агент структурирования документов
│   │   └── risk_detector.py    # Агент поиска рисков и compliance
│   ├── api/                    # Точка входа и маршрутизация FastAPI
│   │   └── main.py             # Основной файл приложения и эндпоинты
│   ├── memory/                 # Модуль долговременной (эпизодической) памяти
│   │   └── long_term.py        # Сохранение и семантический поиск в Qdrant
│   ├── rag/                    # RAG-пайплайн
│   │   ├── document_parser.py  # Парсеры PDF/DOCX
│   │   ├── embeddings.py       # Многоязычные эмбеддинги
│   │   └── retriever.py        # Векторный поиск в Qdrant
│   ├── monitoring/             # Сбор метрик
│   │   └── metrics.py          # Prometheus счетчики и гистограммы
│   └── utils/                  # Утилиты и конфигурация
│       └── config.py           # Настройки подключения к сервисам
├── tests/                      # Unit-тесты с моками для изоляции LLM
├── data/                       # Тестовые документы (законы и договоры)
├── create_test_data.py         # Скрипт генерации тестовой базы законов
├── create_test_contract.py     # Скрипт генерации тестового договора с рисками
├── docker-compose.yml          # Оркестрация локальной инфраструктуры
├── Dockerfile                  # Сборка API-контейнера
├── prometheus.yml              # Конфигурация сбора метрик
├── pytest.ini                  # Конфигурация тестирования
├── README.md                   # Этот файл
└── requirements.txt            # Зависимости проекта
```


## 🏗 Архитектура системы

```mermaid
graph TD
    User([👤 Пользователь]) -->|POST /analyze-contract| API[⚡ FastAPI Server]
    
    subgraph Multi-Agent Core [Мультиагентное ядро]
        API -->|1. Парсинг| Parser[📄 Document Parser]
        Parser -->|Текст| Analyzer[🕵️ Document Analyzer Agent]
        Analyzer -->|Структура| RiskDetector[⚠️ Risk Detector Agent]
        RiskDetector -->|RAG запрос| QdrantLaws[(📚 Qdrant: База законов)]
        QdrantLaws -->|Контекст законов| RiskDetector
    end
    
    RiskDetector -->|2. Сохранение выжимки| QdrantMemory[(🧠 Qdrant: Долговременная память)]
    
    User -->|POST /memory/query| MemorySearch[🔍 Semantic Search]
    MemorySearch --> QdrantMemory
    
    subgraph MLOps [Инфраструктура и мониторинг]
        API -.->|/metrics| Prom[📊 Prometheus]
        Prom --> Graf[📈 Grafana Dashboards]
    end

    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef api fill:#009688,stroke:#333,stroke-width:2px,color:#fff;
    classDef agent fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#4caf50,stroke:#333,stroke-width:2px,color:#fff;
    
    class API api;
    class Analyzer,RiskDetector agent;
    class QdrantLaws,QdrantMemory db;