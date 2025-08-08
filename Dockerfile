# ---- Stage 1: build frontend ----
FROM node:20-alpine AS webbuild
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm i
COPY frontend .
RUN npm run build

# ---- Stage 2: run backend + serve web ----
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend .
COPY --from=webbuild /frontend/dist ./web
EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
