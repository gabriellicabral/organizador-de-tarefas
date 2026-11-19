"""Endpoints que recebem as solicitações da equipe."""
from fastapi import APIRouter

from app.schemas import EXEMPLO, PedidoOrganizacao, ResultadoOrganizacao
from app.services import task_service

router = APIRouter(prefix="/tarefas", tags=["Tarefas"])


@router.get("/exemplo")
def exemplo():
    """Devolve um pedido de exemplo para testar a API ou o n8n."""
    return EXEMPLO


@router.post("/organizar", response_model=ResultadoOrganizacao)
def organizar(pedido: PedidoOrganizacao):
    """Recebe as solicitações e devolve a ordem em que a equipe deve executá-las."""
    return task_service.organizar_tarefas(pedido)
