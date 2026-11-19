"""Inicializa a aplicação FastAPI.

Para rodar (na raiz do projeto):  uvicorn app.main:app --reload
"""
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # lê o arquivo .env (chave da IA, provedor etc.)

from app.routes import tasks  # noqa: E402  (importa depois de carregar o .env)

app = FastAPI(
    title="Organizador de Tarefas com IA",
    description="Recebe solicitações da equipe e devolve, com ajuda de IA, a ordem em que devem ser feitas.",
    version="1.0.0",
)

app.include_router(tasks.router)


@app.get("/", tags=["Status"])
def status():
    return {"status": "ok", "docs": "/docs"}
