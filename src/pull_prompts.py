"""Baixa o prompt público de referência do LangSmith Hub para YAML."""

import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

from utils import print_section_header, save_yaml

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = ROOT / "prompts" / "bug_to_user_story_v1.yml"


def _serialize_prompt(client: Client) -> dict:
    """Baixa o prompt e retorna sua representação YAML."""
    prompt = client.pull_prompt(
        PROMPT_NAME, dangerously_pull_public_prompt=True
    )
    messages = []
    for message in prompt.messages:
        template = getattr(message, "prompt", None)
        template = getattr(template, "template", None)
        if template is None:
            template = getattr(message, "content", "")
        role = getattr(message, "type", message.__class__.__name__.lower())
        messages.append({"role": role, "template": template})
    return {
        "source": PROMPT_NAME,
        "description": "Prompt semente baixado do LangSmith Prompt Hub.",
        "messages": messages,
    }


def pull_prompts_from_langsmith():
    """Puxa o prompt público, usando chave primeiro e acesso público como fallback."""
    api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    if not api_key:
        print("LANGSMITH_API_KEY ausente; tentando o pull público sem autenticação...")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="API key must be provided when using hosted LangSmith API")
            return _serialize_prompt(Client(api_key=""))
    try:
        return _serialize_prompt(Client())
    except Exception as exc:
        error_text = str(exc).lower()
        if "403" not in error_text and "forbidden" not in error_text:
            raise
        # Um token de workspace pode ser válido, mas sem permissão para ler
        # prompts públicos de terceiros. Tente a rota pública sem credencial.
        print("Chave recebeu 403; tentando o pull público sem autenticação...")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="API key must be provided when using hosted LangSmith API")
            return _serialize_prompt(Client(api_key=""))


def main():
    print_section_header("PULL DO PROMPT SEMENTE")
    try:
        data = pull_prompts_from_langsmith()
        if not save_yaml(data, str(OUTPUT_PATH)):
            return 1
        print(f"Prompt salvo em: {OUTPUT_PATH}")
        return 0
    except Exception as exc:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None) or getattr(exc, "status_code", None)
        error_text = str(exc).lower()
        if status is None and "403" in error_text and "forbidden" in error_text:
            status = 403
        elif status is None and "401" in error_text and "unauthorized" in error_text:
            status = 401
        if status == 401:
            print("LangSmith recusou a autenticação (HTTP 401). Verifique LANGSMITH_API_KEY no .env.")
        elif status == 403:
            print(f"O LangSmith negou o pull autenticado e o pull público de {PROMPT_NAME}.")
            print("Confirme que o prompt está público e que o handle está correto.")
            if OUTPUT_PATH.exists():
                print(f"A cópia local foi preservada em: {OUTPUT_PATH}")
        else:
            print(f"Falha ao baixar {PROMPT_NAME}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
