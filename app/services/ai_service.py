"""Comunicação com o modelo de IA (Google Gemini ou OpenAI).

O provedor é escolhido no .env pela variável AI_PROVIDER ("gemini" ou "openai").
"""
import json
import os
from pathlib import Path

import httpx

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "task_analysis.txt"


def carregar_prompt() -> str:
    """Lê o prompt de sistema do arquivo task_analysis.txt."""
    return PROMPT_PATH.read_text(encoding="utf-8")


def chamar_gemini(prompt: str, mensagem: str) -> str:
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    corpo = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": [{"role": "user", "parts": [{"text": mensagem}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    resposta = httpx.post(url, params={"key": os.getenv("GEMINI_API_KEY")}, json=corpo, timeout=60)
    resposta.raise_for_status()
    return resposta.json()["candidates"][0]["content"]["parts"][0]["text"]


def chamar_openai(prompt: str, mensagem: str) -> str:
    corpo = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": mensagem},
        ],
    }
    cabecalho = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
    resposta = httpx.post("https://api.openai.com/v1/chat/completions",
                          headers=cabecalho, json=corpo, timeout=60)
    resposta.raise_for_status()
    return resposta.json()["choices"][0]["message"]["content"]


def converter_para_json(texto: str) -> dict:
    """Transforma o texto da IA em dicionário, removendo ```json ... ``` se vier."""
    texto = texto.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    return json.loads(texto)


def analisar_tarefas(dados: dict) -> dict:
    """Envia as tarefas para a IA e devolve a resposta já convertida em dicionário."""
    prompt = carregar_prompt()
    mensagem = json.dumps(dados, ensure_ascii=False, indent=2)

    provedor = os.getenv("AI_PROVIDER", "gemini").lower()
    if provedor == "openai":
        texto = chamar_openai(prompt, mensagem)
    elif provedor == "gemini":
        texto = chamar_gemini(prompt, mensagem)
    else:
        raise ValueError(f"AI_PROVIDER '{provedor}' não é válido (use gemini ou openai).")

    return converter_para_json(texto)
