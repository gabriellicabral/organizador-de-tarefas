"""Formatos de entrada e saída da API (validados automaticamente pelo Pydantic)."""
from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

EXEMPLO = {
    "equipe_disponivel": 5,
    "solicitacoes": [
        {"id": "T1", "titulo": "Corrigir erro no login do sistema",
         "descricao": "Usuários não conseguem entrar desde a última atualização.",
         "prazo": "2026-11-21", "dificuldade": 3, "pessoas_necessarias": 2},
        {"id": "T2", "titulo": "Criar relatório mensal de vendas",
         "descricao": "Relatório para a diretoria com os números do mês.",
         "prazo": "2026-11-30", "dificuldade": 2, "pessoas_necessarias": 1},
        {"id": "T3", "titulo": "Migrar banco de dados para o novo servidor",
         "descricao": "Precisa ser feita antes da atualização do módulo de pagamentos.",
         "prazo": "2026-11-27", "dificuldade": 5, "pessoas_necessarias": 3},
        {"id": "T4", "titulo": "Atualizar módulo de pagamentos",
         "descricao": "Depende da migração do banco de dados.",
         "prazo": "2026-12-04", "dificuldade": 4, "pessoas_necessarias": 2},
        {"id": "T5", "titulo": "Responder chamados de suporte atrasados",
         "descricao": "Fila de chamados abertos há mais de uma semana.",
         "prazo": "2026-11-19", "dificuldade": 1, "pessoas_necessarias": 1},
        {"id": "T6", "titulo": "Treinamento da equipe comercial no novo CRM",
         "descricao": "Workshop presencial com todo o time de vendas.",
         "prazo": "2026-12-10", "dificuldade": 2, "pessoas_necessarias": 6},
    ],
}


# ----------------------------- Entrada -----------------------------
class Solicitacao(BaseModel):
    id: str
    titulo: str
    descricao: Optional[str] = ""
    prazo: date = Field(..., description="Data de entrega (AAAA-MM-DD)")
    dificuldade: int = Field(..., ge=1, le=5, description="1 = muito fácil, 5 = muito difícil")
    pessoas_necessarias: int = Field(..., ge=1)


class PedidoOrganizacao(BaseModel):
    equipe_disponivel: int = Field(..., ge=1, description="Quantas pessoas a equipe tem")
    data_referencia: Optional[date] = Field(None, description="Data usada como 'hoje' (opcional)")
    solicitacoes: List[Solicitacao] = Field(..., min_length=1)

    model_config = {"json_schema_extra": {"example": EXEMPLO}}


# ------------------------------ Saída ------------------------------
class TarefaOrganizada(BaseModel):
    posicao: int
    id: str
    titulo: str
    prazo: date
    dias_restantes: int
    dificuldade: int
    pessoas_necessarias: int
    nivel_prioridade: Literal["Crítica", "Alta", "Média", "Baixa"]
    justificativa: str


class ResultadoOrganizacao(BaseModel):
    origem: Literal["ia", "regra_local"]
    resumo: str
    ordem_execucao: List[TarefaOrganizada]
    alertas: List[str]
