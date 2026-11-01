"""Valida e publica o prompt v2 no LangSmith Prompt Hub."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from utils import check_env_vars, load_yaml, print_section_header, validate_prompt_structure

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = ROOT / "prompts" / "bug_to_user_story_v2.yml"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """Valida os campos necessários antes de publicar."""
    errors = []
    if not isinstance(prompt_data, dict):
        return False, ["A raiz do YAML deve ser um objeto."]
    errors.extend(validate_prompt_structure(prompt_data)[1])
    if not isinstance(prompt_data.get("user_prompt"), str) or not prompt_data["user_prompt"].strip():
        errors.append("user_prompt deve ser uma string não vazia.")
    if "{bug_report}" not in prompt_data.get("user_prompt", ""):
        errors.append("user_prompt deve conter a variável {bug_report}.")
    if not isinstance(prompt_data.get("techniques_applied"), list) or len(prompt_data.get("techniques_applied", [])) < 2:
        errors.append("Liste ao menos duas técnicas em techniques_applied.")
    return not errors, errors


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """Publica o prompt; retorna False para configuração, validação ou API falha."""
    valid, errors = validate_prompt(prompt_data)
    if not valid:
        for error in errors:
            print(f"- {error}")
        return False
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return False
    messages = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])
    try:
        url = Client().push_prompt(
            prompt_name,
            object=messages,
            is_public=True,
            description=prompt_data["description"],
            tags=prompt_data.get("tags", []),
        )
        print(f"Prompt publicado: {url}")
        return True
    except Exception as exc:
        error_text = str(exc).lower()
        if "without first" in error_text and "hub handle" in error_text:
            print("A API key autenticou, mas esta conta ainda não tem um handle público do LangSmith Hub.")
            print("Abra https://smith.langchain.com/prompts usando a mesma conta da API key.")
            print("Publique um prompt de teste com Make Public e confirme o handle escolhido.")
            print("Depois, use exatamente esse handle em USERNAME_LANGSMITH_HUB no .env.")
        else:
            print(f"Falha ao publicar no LangSmith: {exc}")
        return False


def main():
    print_section_header("PUSH DO PROMPT OTIMIZADO")
    prompt_data = load_yaml(str(PROMPT_PATH))
    if not prompt_data:
        return 1
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        print("Preencha esses campos com valores reais no .env; placeholders não são aceitos.")
        return 1
    prompt_name = f"{username}/bug_to_user_story_v2"
    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
