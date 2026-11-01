"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = load_prompts(str(PROMPT_FILE))
        assert isinstance(prompt.get("system_prompt"), str)
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        prompt = load_prompts(str(PROMPT_FILE))
        assert any(term in prompt["system_prompt"].lower() for term in ("você é", "product manager", "persona"))

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt = load_prompts(str(PROMPT_FILE))
        content = f'{prompt["system_prompt"]}\n{prompt.get("user_prompt", "")}'.lower()
        assert "markdown" in content
        assert "user story" in content

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt = load_prompts(str(PROMPT_FILE))
        content = prompt["system_prompt"].lower()
        assert "few-shot" in content or "exemplos" in content
        assert "entrada:" in content and "saída:" in content
        assert content.count("entrada:") >= 2

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt = load_prompts(str(PROMPT_FILE))
        assert "[todo]" not in str(prompt).lower()

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt = load_prompts(str(PROMPT_FILE))
        assert isinstance(prompt.get("techniques_applied"), list)
        assert len(prompt["techniques_applied"]) >= 2
        assert validate_prompt_structure(prompt)[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
