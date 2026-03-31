FROM python:3.13-alpine

# Pillow needs these native libs on Alpine
RUN apk add --no-cache \
    jpeg-dev \
    zlib-dev \
    libwebp-dev \
    gcc \
    musl-dev

WORKDIR /app

# Install Python dependencies (cached layer — only rebuilds if requirements change)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Remove build tools after install to keep image small
RUN apk del gcc musl-dev

# Copy app source
COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
