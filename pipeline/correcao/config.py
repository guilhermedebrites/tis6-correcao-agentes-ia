"""Parâmetros da pipeline. Tudo que muda o resultado fica aqui e vai para o manifesto."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Config:
    # Dataset (D5, D7)
    aidev_repo: str = "hao-li/AIDev"
    aidev_revision: str = "7840b6e61a5828461cd96806c52c20194ef57979"
    corte: datetime = datetime(2025, 10, 24, 23, 59, 59, tzinfo=timezone.utc)

    # Janela de observação da correção (dias depois do merge da PR de origem)
    janela_dias: int = 90

    # Mínimos por repositório (D17, D17-bis)
    min_fa_validas: int = 5
    min_hl_validas: int = 5

    # Filtros de tamanho da unidade (E3), em linhas lógicas adicionadas + removidas
    min_size_churn: int = 3
    max_size_churn: int = 500
    percentil_max: float = 0.99

    # Rebase: acima desta fração de eventos sem marcação de PR, tenta recuperar HL pela API
    limiar_sem_marcacao: float = 0.30

    # Classificador de correção (E5b)
    modelo_llm: str = "claude-haiku-5-5"
    prompt_versao: str = "classificador_v1"
    max_linhas_diff: int = 120
    max_chars_descricao: int = 1500

    # Linguagens (D18)
    familias: tuple = ("python", "jsts")

    semente: int = 42

    def manifesto(self) -> dict:
        d = asdict(self)
        d["corte"] = self.corte.isoformat()
        return d


CFG = Config()
