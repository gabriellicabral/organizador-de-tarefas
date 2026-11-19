"""Regras de negócio: prepara os dados, pede a ordem para a IA, confere a resposta
e, se a IA falhar, organiza com uma regra simples para o sistema nunca ficar sem resposta."""
import logging
from datetime import date

from app.schemas import PedidoOrganizacao
from app.services import ai_service

log = logging.getLogger(__name__)


def preparar_tarefas(pedido: PedidoOrganizacao, hoje: date) -> list:
    """Converte as solicitações em dicionários e calcula os dias restantes de cada uma."""
    tarefas = []
    for s in pedido.solicitacoes:
        tarefa = s.model_dump()
        tarefa["dias_restantes"] = (s.prazo - hoje).days
        tarefas.append(tarefa)
    return tarefas


def nivel_por_prazo(dias: int) -> str:
    if dias <= 1:
        return "Crítica"
    if dias <= 3:
        return "Alta"
    if dias <= 7:
        return "Média"
    return "Baixa"


def texto_prazo(dias: int) -> str:
    if dias < 0:
        return f"Prazo vencido há {-dias} dia(s)"
    if dias == 0:
        return "Vence hoje"
    return f"Faltam {dias} dia(s)"


def organizar_sem_ia(tarefas: list) -> dict:
    """Plano B: menor prazo primeiro; empate -> mais difícil e com mais pessoas primeiro."""
    ordenadas = sorted(
        tarefas, key=lambda t: (t["dias_restantes"], -t["dificuldade"], -t["pessoas_necessarias"])
    )
    return {
        "resumo": "Ordem definida pela regra local: prazo mais próximo primeiro e, em caso de "
                  "empate, a tarefa mais difícil e que exige mais pessoas.",
        "ordem_execucao": [
            {
                "id": t["id"],
                "nivel_prioridade": nivel_por_prazo(t["dias_restantes"]),
                "justificativa": f"{texto_prazo(t['dias_restantes'])}, dificuldade "
                                 f"{t['dificuldade']}/5 e {t['pessoas_necessarias']} pessoa(s).",
            }
            for t in ordenadas
        ],
        "alertas": [],
    }


NIVEIS = ["Crítica", "Alta", "Média", "Baixa"]


def resposta_valida(resposta: dict, tarefas: list) -> bool:
    """Confere se a IA devolveu todas as tarefas (uma vez cada) e no formato combinado."""
    itens = resposta.get("ordem_execucao", [])
    ids_recebidos = [item.get("id") for item in itens]
    ids_enviados = [t["id"] for t in tarefas]
    if sorted(ids_recebidos) != sorted(ids_enviados):
        return False
    if "resumo" not in resposta:
        return False
    return all(item.get("nivel_prioridade") in NIVEIS and item.get("justificativa") for item in itens)


def gerar_alertas(tarefas: list, equipe: int) -> list:
    alertas = []
    for t in tarefas:
        if t["dias_restantes"] < 0:
            alertas.append(f"[{t['id']}] {t['titulo']}: prazo vencido há {-t['dias_restantes']} dia(s).")
        if t["pessoas_necessarias"] > equipe:
            alertas.append(f"[{t['id']}] {t['titulo']}: precisa de {t['pessoas_necessarias']} "
                           f"pessoas, mas a equipe tem {equipe}.")
    return alertas


def organizar_tarefas(pedido: PedidoOrganizacao) -> dict:
    hoje = pedido.data_referencia or date.today()
    tarefas = preparar_tarefas(pedido, hoje)
    alertas = []

    # 1) Tenta organizar com a IA
    try:
        resposta = ai_service.analisar_tarefas({
            "data_de_hoje": hoje.isoformat(),
            "equipe_disponivel": pedido.equipe_disponivel,
            "solicitacoes": [{**t, "prazo": t["prazo"].isoformat()} for t in tarefas],
        })
        if not resposta_valida(resposta, tarefas):
            raise ValueError("resposta fora do formato combinado ou com tarefas faltando")
        origem = "ia"
    # 2) Se der qualquer erro (sem chave, sem internet, JSON inválido...), usa a regra local
    except Exception as erro:
        log.warning("Falha na IA, usando regra local: %s", erro)
        resposta = organizar_sem_ia(tarefas)
        origem = "regra_local"
        alertas.append(f"A IA não respondeu corretamente ({erro}); foi usada a regra local.")

    # 3) Monta o resultado final juntando a ordem da IA com os dados originais
    por_id = {t["id"]: t for t in tarefas}
    ordem_execucao = []
    for posicao, item in enumerate(resposta["ordem_execucao"], start=1):
        t = por_id[item["id"]]
        ordem_execucao.append({
            "posicao": posicao,
            "id": t["id"],
            "titulo": t["titulo"],
            "prazo": t["prazo"],
            "dias_restantes": t["dias_restantes"],
            "dificuldade": t["dificuldade"],
            "pessoas_necessarias": t["pessoas_necessarias"],
            "nivel_prioridade": item["nivel_prioridade"],
            "justificativa": item["justificativa"],
        })

    # junta os alertas da IA com os calculados aqui, sem repetir
    for alerta in resposta.get("alertas", []) + gerar_alertas(tarefas, pedido.equipe_disponivel):
        if alerta not in alertas:
            alertas.append(alerta)

    return {
        "origem": origem,
        "resumo": resposta["resumo"],
        "ordem_execucao": ordem_execucao,
        "alertas": alertas,
    }
