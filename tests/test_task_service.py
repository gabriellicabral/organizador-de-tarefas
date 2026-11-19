"""Testes das regras de negócio. A IA é substituída por funções falsas,
então os testes rodam sem chave e sem internet.

Rodar na raiz do projeto:  python -m pytest
"""
from datetime import date

from app.schemas import EXEMPLO, PedidoOrganizacao
from app.services import ai_service, task_service

PEDIDO = PedidoOrganizacao(**EXEMPLO, data_referencia=date(2026, 11, 20))


def test_usa_ordem_da_ia(monkeypatch):
    ordem = ["T5", "T1", "T3", "T4", "T2", "T6"]

    def ia_falsa(dados):
        return {
            "resumo": "Começar pelos prazos vencidos.",
            "ordem_execucao": [
                {"id": i, "nivel_prioridade": "Alta", "justificativa": "teste"} for i in ordem
            ],
            "alertas": [],
        }

    monkeypatch.setattr(ai_service, "analisar_tarefas", ia_falsa)
    resultado = task_service.organizar_tarefas(PEDIDO)

    assert resultado["origem"] == "ia"
    assert [t["id"] for t in resultado["ordem_execucao"]] == ordem
    assert resultado["ordem_execucao"][0]["dias_restantes"] == -1


def test_ia_com_erro_usa_regra_local(monkeypatch):
    def ia_quebrada(dados):
        raise ConnectionError("sem internet")

    monkeypatch.setattr(ai_service, "analisar_tarefas", ia_quebrada)
    resultado = task_service.organizar_tarefas(PEDIDO)

    assert resultado["origem"] == "regra_local"
    assert resultado["ordem_execucao"][0]["id"] == "T5"  # prazo vencido vem primeiro
    assert len(resultado["ordem_execucao"]) == 6


def test_ia_esquecendo_tarefa_usa_regra_local(monkeypatch):
    def ia_incompleta(dados):
        return {"resumo": "x", "ordem_execucao": [
            {"id": "T1", "nivel_prioridade": "Alta", "justificativa": "x"}]}

    monkeypatch.setattr(ai_service, "analisar_tarefas", ia_incompleta)
    assert task_service.organizar_tarefas(PEDIDO)["origem"] == "regra_local"


def test_ia_com_nivel_invalido_usa_regra_local(monkeypatch):
    def ia_nivel_errado(dados):
        return {"resumo": "x", "ordem_execucao": [
            {"id": s["id"], "nivel_prioridade": "Urgentíssima", "justificativa": "x"}
            for s in dados["solicitacoes"]]}

    monkeypatch.setattr(ai_service, "analisar_tarefas", ia_nivel_errado)
    assert task_service.organizar_tarefas(PEDIDO)["origem"] == "regra_local"


def test_alertas_de_prazo_e_equipe():
    tarefas = task_service.preparar_tarefas(PEDIDO, date(2026, 11, 20))
    alertas = task_service.gerar_alertas(tarefas, equipe=5)
    assert any("T5" in a and "vencido" in a for a in alertas)
    assert any("T6" in a and "6 pessoas" in a for a in alertas)


def test_converter_json_com_markdown():
    assert ai_service.converter_para_json('```json\n{"a": 1}\n```') == {"a": 1}
