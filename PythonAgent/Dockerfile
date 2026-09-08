FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# sentence-transformers depends on torch, and by default pip resolves the
# full GPU/CUDA build (hundreds of MB of extra nvidia-* packages) even
# though this container has no GPU and only ever runs CPU inference.
# Installing the small CPU-only wheel from PyTorch's own index first means
# the "torch>=1.11.0" constraint below is already satisfied and pip never
# attempts the much larger GPU download.
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r requirements.txt

COPY main.py rag.py ./
COPY data/ ./data/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
