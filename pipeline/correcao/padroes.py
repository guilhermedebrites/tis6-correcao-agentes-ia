"""Expressões regulares: arquivos considerados, agentes, bots, tipo de tarefa e heurística de correção."""
from __future__ import annotations

import re

# --- Arquivos considerados (E3) ---------------------------------------------
EXT = {
    "python": (".py",),
    "jsts": (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"),
}
ARQUIVO_EXCLUIDO = re.compile(
    r"(?:^|/)(?:tests?|testing|spec|__tests__|__mocks__)/"
    r"|(?:^|/)test_[^/]*\.py$|_test\.py$|(?:^|/)conftest\.py$"
    r"|\.(?:test|spec)\.[cm]?[jt]sx?$"
    r"|(?:^|/)(?:migrations|alembic/versions)/"
    r"|(?:^|/)(?:vendor|vendored|third_party|externals|node_modules|site-packages|\.venv|build|dist|generated)/"
    r"|_pb2\.py$|_generated\.py$|\.min\.js$|\.d\.ts$"
    r"|(?:^|/)(?:setup\.py|noxfile\.py|conf\.py)$"
    r"|(?:^|/)[^/]*\.config\.[cm]?[jt]s$"
)


def familia_do_arquivo(caminho: str) -> str | None:
    for fam, exts in EXT.items():
        if caminho.endswith(exts):
            return fam
    return None


def arquivo_considerado(caminho: str, familia: str) -> bool:
    return caminho.endswith(EXT[familia]) and not ARQUIVO_EXCLUIDO.search(caminho)


# --- Linhas lógicas: sem vazias e sem linhas só de comentário -------------------
_COMENTARIO = {
    "python": re.compile(r"^\s*(?:#.*)?$"),
    "jsts": re.compile(r"^\s*(?://.*|/\*.*|\*.*|\*/\s*)?$"),
}


def linha_logica(texto: str, familia: str) -> bool:
    return not _COMENTARIO[familia].match(texto)


# --- Agentes (D15) ------------------------------------------------------------
# Coluna `agent` do AIDev
AGENTE_PRINCIPAL = {"copilot": r"copilot", "devin": r"devin", "jules": r"jules"}
AGENTE_PROVAVEL = {"codex": r"codex", "cursor": r"cursor", "claude_code": r"claude"}

# Autor de commit que é o próprio agente (pureza)
AUTOR_AGENTE = re.compile(r"copilot|devin|jules|google-labs|cursoragent|cursor agent", re.I)

# Assinatura de agente no git (para PRs fora do AIDev ou depois do corte)
ASSINATURA_AUTOR = re.compile(
    r"copilot-swe-agent|^copilot$|devin-ai-integration|google-labs-jules|cursoragent"
    r"|chatgpt-codex-connector|claude\[bot\]",
    re.I,
)
ASSINATURA_BRANCH = re.compile(r"(?:^|/)(?:copilot|devin|jules|codex|cursor|claude)/", re.I)
AGENTE_POR_ASSINATURA = [
    ("copilot", re.compile(r"copilot", re.I)),
    ("devin", re.compile(r"devin", re.I)),
    ("jules", re.compile(r"jules", re.I)),
    ("codex", re.compile(r"codex", re.I)),
    ("cursor", re.compile(r"cursor", re.I)),
    ("claude_code", re.compile(r"claude", re.I)),
]

# Bots de automação (não são agentes)
BOT = re.compile(
    r"\[bot\]|dependabot|renovate|pre-commit-ci|github-actions|autofix-ci|snyk-bot|greenkeeper|allcontributors",
    re.I,
)
BRANCH_BOT = re.compile(r"(?:^|/)(?:dependabot|renovate|pre-commit-ci|release-please|changeset-release)[/-]", re.I)

# Merges de sincronização dentro da PR (neutros para pureza)
MERGE_SINCRONIZACAO = re.compile(r"^Merge (?:branch|remote-tracking branch|pull request)\b")

# IA declarada em PR humana (fica no HL, só marcada)
IA_DECLARADA = re.compile(
    r"Co-authored-by:.*(?:claude|copilot|cursor|codex|chatgpt|openai|gemini|devin|aider|anthropic)"
    r"|Generated with \[?(?:Claude|Cursor|Copilot|Codex|Aider)",
    re.I,
)

# --- Marcação de PR no histórico de 1º pai (D14) -------------------------------
MERGE_PR = re.compile(r"^Merge pull request #(\d+) from (\S+)")
SQUASH_PR = re.compile(r"\(#(\d+)\)\s*$")

# --- Tipo de tarefa (D11-lite) ------------------------------------------------
_CONVENTIONAL = re.compile(r"^\s*(\w+)(?:\([^)]*\))?!?:", re.I)
_MAPA_CONVENTIONAL = {
    "feat": "feat", "feature": "feat", "fix": "fix", "bugfix": "fix", "hotfix": "fix",
    "refactor": "refactor", "perf": "refactor", "style": "refactor",
    "docs": "docs", "doc": "docs", "test": "test", "tests": "test",
    "chore": "chore", "build": "chore", "ci": "chore", "deps": "chore", "revert": "chore",
}
_PALAVRAS_TAREFA = [
    ("fix", re.compile(r"\b(?:fix(?:e[sd])?|bug|error|crash|regression|broken|wrong|incorrect|issue)\b", re.I)),
    ("refactor", re.compile(r"\b(?:refactor|clean ?up|rename|simplif|reorgani[sz]e|move)\w*", re.I)),
    ("docs", re.compile(r"\b(?:docs?|documentation|readme|docstring|typo)\b", re.I)),
    ("test", re.compile(r"\b(?:tests?|testing|coverage)\b", re.I)),
    ("chore", re.compile(r"\b(?:bump|upgrade|update dependenc|version|release|ci|lint)\w*", re.I)),
    ("feat", re.compile(r"\b(?:add|implement|support|introduce|new|enable|allow)\w*", re.I)),
]


def tipo_tarefa(titulo: str) -> str:
    m = _CONVENTIONAL.match(titulo or "")
    if m and m.group(1).lower() in _MAPA_CONVENTIONAL:
        return _MAPA_CONVENTIONAL[m.group(1).lower()]
    for tipo, rx in _PALAVRAS_TAREFA:
        if rx.search(titulo or ""):
            return tipo
    return "outro"


# --- Heurística de correção (sensibilidade do classificador) -------------------
CORRECAO_HEURISTICA = re.compile(
    r"^\s*fix(?:\([^)]*\))?!?:|\b(?:fix(?:e[sd]|ing)?|bug|bugs|error|crash|regression|broken|wrong|incorrect|hotfix)\b",
    re.I,
)
