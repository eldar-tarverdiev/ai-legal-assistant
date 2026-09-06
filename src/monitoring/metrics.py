import time
from fastapi import Request
from prometheus_client import Counter, Histogram

# Метрики
REQUEST_COUNT = Counter(
    'legal_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status', 'agent']
)

REQUEST_LATENCY = Histogram(
    'legal_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

RISK_DETECTED = Counter(
    'legal_risks_detected_total',
    'Total number of risks detected',
    ['severity', 'contract_type']
)

DOCUMENTS_PROCESSED = Counter(
    'legal_documents_processed_total',
    'Total number of documents processed',
    ['document_type']
)


async def metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        agent="main"
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.url.path).observe(duration)

    return response