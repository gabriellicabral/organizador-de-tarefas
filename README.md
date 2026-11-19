# Organizador de Tarefas com IA

Projeto do cenário **4.3 — Organização de Tarefas**.

Uma equipe recebe várias solicitações de atividades e precisa saber **por qual começar**.
Esta API recebe as solicitações, envia para um modelo de IA com um prompt estruturado e
devolve, em **JSON**, a ordem em que as tarefas devem ser feitas, com o nível de prioridade
e a justificativa de cada uma. Um fluxo no **n8n** recebe os pedidos, chama a API e devolve
o plano pronto.

## Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem do back-end |
| FastAPI + Uvicorn | API e servidor |
| Pydantic | Validação dos dados de entrada e saída |
| httpx | Chamadas HTTP para a API da IA |
| Google Gemini ou OpenAI | Modelo de IA que prioriza as tarefas |
| n8n | Fluxo de automação |
| pytest | Testes |

## Estrutura do projeto

```
projeto-ia-automacao/
├── app/
│   ├── main.py                  # inicializa a aplicação FastAPI
│   ├── schemas.py               # formatos de entrada e saída (Pydantic)
│   ├── routes/
│   │   └── tasks.py             # endpoints que recebem as solicitações
│   ├── services/
│   │   ├── ai_service.py        # comunicação com o modelo de IA
│   │   └── task_service.py      # regras de negócio
│   └── prompts/
│       └── task_analysis.txt    # prompt que interpreta e prioriza as tarefas
├── n8n/
│   └── task_automation.json     # workflow exportado do n8n
├── tests/
│   └── test_task_service.py     # testes (rodam sem chave de IA)
├── .env.example                 # modelo das variáveis de ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

## Como funciona

1. O cliente (ou o n8n) envia as solicitações para `POST /tarefas/organizar`.
2. O **Pydantic** valida os dados: dificuldade de 1 a 5, pessoas ≥ 1, data no formato correto.
3. O `task_service.py` calcula os **dias restantes** de cada tarefa e chama o `ai_service.py`.
4. O `ai_service.py` lê o prompt de `task_analysis.txt` e envia prompt + tarefas para a IA.
5. A IA responde em JSON com a ordem, o nível de prioridade e a justificativa.
6. O `task_service.py` confere se a resposta veio completa e junta com os dados originais.
   Se a IA falhar (sem chave, sem internet, resposta inválida), usa uma **regra local**
   (prazo mais próximo primeiro) e avisa nos `alertas`. Assim a API sempre responde.
7. A API devolve o plano em JSON.

### Critérios de priorização (definidos no prompt)

1. **Prazo**: menos dias restantes = mais urgente.
2. **Dificuldade**: com prazos parecidos, a mais difícil começa antes.
3. **Pessoas necessárias**: tarefas que ocupam muita gente com prazo curto são planejadas
   cedo; se precisar de mais pessoas do que a equipe tem, gera alerta.
4. **Caminho lógico**: se uma tarefa depende de outra, a dependência vem antes.

## Instalação

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Criar o arquivo .env a partir do modelo
copy .env.example .env          # Windows
cp .env.example .env            # Linux/Mac
```

No `.env`, coloque a sua chave:

- **Gemini** (gratuito): crie a chave em https://aistudio.google.com e preencha `GEMINI_API_KEY`.
- **OpenAI**: troque para `AI_PROVIDER=openai` e preencha `OPENAI_API_KEY`.

## Execução

```bash
uvicorn app.main:app --reload
```

Acesse **http://localhost:8000/docs** para testar pelo Swagger. O corpo de exemplo já
vem preenchido.

Testes:

```bash
python -m pytest
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Verifica se a API está no ar |
| GET | `/tarefas/exemplo` | Devolve um pedido de exemplo |
| POST | `/tarefas/organizar` | Organiza as solicitações |

### Exemplo de requisição

```json
{
  "equipe_disponivel": 5,
  "solicitacoes": [
    {
      "id": "T1",
      "titulo": "Corrigir erro no login do sistema",
      "descricao": "Usuários não conseguem entrar desde a última atualização.",
      "prazo": "2026-11-21",
      "dificuldade": 3,
      "pessoas_necessarias": 2
    },
    {
      "id": "T5",
      "titulo": "Responder chamados de suporte atrasados",
      "descricao": "Fila de chamados abertos há mais de uma semana.",
      "prazo": "2026-11-19",
      "dificuldade": 1,
      "pessoas_necessarias": 1
    }
  ]
}
```

O campo `data_referencia` (opcional) define qual data considerar como "hoje". Se não for
enviado, a API usa a data atual.

### Exemplo de resposta

```json
{
  "origem": "ia",
  "resumo": "A prioridade é resolver o que já venceu e o que vence amanhã...",
  "ordem_execucao": [
    {
      "posicao": 1,
      "id": "T5",
      "titulo": "Responder chamados de suporte atrasados",
      "prazo": "2026-11-19",
      "dias_restantes": -1,
      "dificuldade": 1,
      "pessoas_necessarias": 1,
      "nivel_prioridade": "Crítica",
      "justificativa": "Prazo vencido, tarefa simples que exige apenas uma pessoa."
    }
  ],
  "alertas": [
    "[T5] Responder chamados de suporte atrasados: prazo vencido há 1 dia(s)."
  ]
}
```

`origem` mostra quem organizou: `"ia"` ou `"regra_local"` (quando a IA falhou).

## Automação com n8n

O arquivo `n8n/task_automation.json` contém o fluxo pronto:

```
Receber Solicitações (Webhook)
        ↓
Validar Entrada (Code)
        ↓
Chamar API (IA) (HTTP Request) ──erro──→ Responder Erro (502)
        ↓
Formatar Plano (Code)
        ↓
Responder Sucesso (200)
```

### 1. Subir o n8n

```bash
npx n8n
```

(precisa do Node.js 18+). Ou, com Docker:

```bash
docker run -it --rm -p 5678:5678 n8nio/n8n
```

Acesse http://localhost:5678.

### 2. Importar o workflow

Crie um workflow em branco → menu **⋯** → **Import from File** → selecione
`n8n/task_automation.json` → **Save**.

### 3. Entendendo cada node (ou criando à mão)

| Node | Tipo | Configuração |
|---|---|---|
| **Receber Solicitações** | Webhook | Method `POST` · Path `organizar-tarefas` · Respond: *Using 'Respond to Webhook' Node* |
| **Validar Entrada** | Code | Confere se `solicitacoes` foi enviado e repassa os dados |
| **Chamar API (IA)** | HTTP Request | Method `POST` · URL `http://127.0.0.1:8000/tarefas/organizar` · Send Body: JSON · Body `{{ JSON.stringify($json) }}` · Timeout `120000` · Settings → On Error: *Continue (using error output)* |
| **Formatar Plano** | Code | Gera `comecar_por` e `plano_em_texto` a partir da resposta da API |
| **Responder Sucesso** | Respond to Webhook | Respond With JSON · Body `{{ JSON.stringify($json) }}` · Código 200 |
| **Responder Erro** | Respond to Webhook | Ligado na saída de erro do HTTP Request · Código 502 |

**Atenção à URL da API no node HTTP Request:**

- n8n rodando com `npx n8n` → `http://127.0.0.1:8000/tarefas/organizar`
  (use `127.0.0.1` e não `localhost`: o Node.js tenta `localhost` pelo IPv6 e o uvicorn
  escuta só no IPv4, o que gera o erro `ECONNREFUSED`)
- n8n rodando no Docker → `http://host.docker.internal:8000/tarefas/organizar`

### 4. Testar o fluxo

Com a API rodando, clique em **Execute workflow** no n8n e envie o pedido de exemplo
(pelo Postman ou terminal):

```bash
curl -X POST http://localhost:5678/webhook-test/organizar-tarefas -H "Content-Type: application/json" -d "{\"equipe_disponivel\": 3, \"solicitacoes\": [{\"id\": \"T1\", \"titulo\": \"Corrigir login\", \"prazo\": \"2026-11-21\", \"dificuldade\": 3, \"pessoas_necessarias\": 2}]}"
```

Depois de ativar o workflow (botão **Active**), a URL passa a ser
`http://localhost:5678/webhook/organizar-tarefas`.

O n8n devolve o JSON da API mais o campo `plano_em_texto`, que pode ser enviado por e-mail,
Telegram ou Slack adicionando um node no final do fluxo.
