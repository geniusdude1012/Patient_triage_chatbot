# Backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend folder
COPY Backend/ ./Backend/

# Copy system prompt
COPY system_prompt.txt .

# Sessions directory as volume
RUN mkdir -p sessions

EXPOSE 8000

# Uvicorn runs FastAPI — module path is Backend/app.py → Backend.app:app
CMD ["uvicorn", "Backend.app:app", "--host", "0.0.0.0", "--port", "8000"]