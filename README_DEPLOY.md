# ЛУДИК БОТ — single-container

## Локально
docker build -t ludik .
docker run -p 8000:8000 ludik
# открыть http://localhost:8000

## Деплой Koyeb
1) Залить в GitHub.
2) Koyeb → Create Service → GitHub → Builder: Dockerfile → path `/Dockerfile` → Port 8000 → Deploy.
