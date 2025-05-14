FROM python:3.10-slim

# 1. Create a non-root user
RUN addgroup --system appgroup && \
    adduser --system appuser --ingroup appgroup

WORKDIR /app

# 2. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy code
COPY . .

# 4. Drop to non-root
USER appuser

# 5. Environment vars (optional defaults)
ENV APP_NAME="docker_app" \
    MODEL_NAME="gemini-2.0-flash"

# 6. Expose the FastAPI port
EXPOSE 8080

# 7. Launch via Uvicorn
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"] 