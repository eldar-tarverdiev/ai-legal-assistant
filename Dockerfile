FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем CPU-версию PyTorch (легче)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Устанавливаем остальные зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY src/ ./src/
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]