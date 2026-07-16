FROM python:3.11-slim

# OpenCV runtime deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

# CPU-only PyTorch first to avoid pulling CUDA wheels
RUN pip install --no-cache-dir torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake OCR models into the image so the demo needs no internet
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"

COPY app/ ./app/

EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
