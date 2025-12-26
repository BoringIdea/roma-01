"""Prompt loading utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Iterable

from loguru import logger


class PromptRepository:
    """Load and render prompt templates from disk."""

    def __init__(self, base_dir: Optional[Path] = None):
        package_root = Path(__file__).resolve().parents[3]  # backend/
        default_dir = package_root / "prompts"
        self.base_dir: Path = Path(base_dir) if base_dir else default_dir
        self.templates: Dict[str, str] = {}

    def load(self, base_dir: Optional[str | Path] = None) -> None:
        """Load prompt templates from disk into memory."""
        if base_dir:
            self.base_dir = Path(base_dir)

        if not self.base_dir.exists():
            logger.warning(f"Prompt directory not found: {self.base_dir}")
            self.templates = {}
            return

        new_templates: Dict[str, str] = {}
        for path in self.base_dir.rglob("*.md"):
            key = path.stem.lower()
            new_templates[key] = path.read_text(encoding="utf-8")

        self.templates = new_templates
        logger.info(f"Loaded {len(self.templates)} prompt templates from {self.base_dir}")

    def _candidate_keys(self, name: str, language: Optional[str]) -> Iterable[str]:
        normalized_name = name.lower()
        if language:
            yield f"{normalized_name}_{language.lower()}"
        yield normalized_name

    def get_template(self, name: str, language: Optional[str] = None) -> str:
        """Retrieve a prompt template by name/language."""
        for key in self._candidate_keys(name, language):
            if key in self.templates:
                return self.templates[key]
        raise ValueError(f"Prompt template '{name}' (language={language}) not found in {self.base_dir}")

    def render_prompt(
        self,
        name: str,
        language: Optional[str] = None,
        context: Optional[Dict[str, object]] = None,
        replacements: Optional[Dict[str, str]] = None,
    ) -> str:
        """Render a prompt template with optional formatting and replacements."""
        template = self.get_template(name, language)
        rendered = template.format(**(context or {}))

        if replacements:
            for placeholder, value in replacements.items():
                rendered = rendered.replace(placeholder, value)

        return rendered


_repository = PromptRepository()
_repository.load()


def initialize_prompt_repository(base_dir: Optional[str | Path] = None) -> None:
    """Reload prompt templates, typically during application startup."""
    _repository.load(base_dir)


def render_prompt(
    name: str,
    language: Optional[str] = None,
    context: Optional[Dict[str, object]] = None,
    replacements: Optional[Dict[str, str]] = None,
) -> str:
    """Render prompt by delegating to the global repository."""
    return _repository.render_prompt(name, language, context, replacements)


def get_prompt_template(name: str, language: Optional[str] = None) -> str:
    """Return the raw template string for a prompt."""
    return _repository.get_template(name, language)


