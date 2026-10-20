"""P1: baixa o AIDev na revisão fixada e monta a tabela de PRs de agentes por repositório (`agent_prs`)."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .config import CFG
from .padroes import AGENTE_PRINCIPAL, AGENTE_PROVAVEL, AUTOR_AGENTE, MERGE_SINCRONIZACAO

TABELAS = ["repository", "pull_request", "pr_commits"]


def baixar(dir_dados: Path) -> str:
    from huggingface_hub import hf_hub_download

    dir_dados.mkdir(parents=True, exist_ok=True)
    for nome in TABELAS:
        print(f"Baixando {nome}.parquet …", flush=True)
        hf_hub_download(CFG.aidev_repo, f"{nome}.parquet", repo_type="dataset",
                        revision=CFG.aidev_revision, local_dir=str(dir_dados))
    (dir_dados / "REVISION").write_text(CFG.aidev_revision)
    return CFG.aidev_revision


def _grupo_agente(valor: str) -> tuple[str, str]:
    v = str(valor).lower()
    for chave, rx in AGENTE_PRINCIPAL.items():
        if re.search(rx, v):
            return chave, "FA_principal"
    for chave, rx in AGENTE_PROVAVEL.items():
        if re.search(rx, v):
            return chave, "FA_provavel"
    return "outro", "outro_agente"


def montar_agent_prs(dir_dados: Path, repos: list[str]) -> pd.DataFrame:
    """Uma linha por PR de agente (de qualquer agente) nos repositórios pedidos.

    Pureza (FA principal): todos os commits da PR são do agente, ignorando merges de
    sincronização e bots neutros. As PRs de outros agentes também entram, porque
    precisam sair do grupo HL.
    """
    repo = pd.read_parquet(dir_dados / "repository.parquet", columns=["id", "full_name"])
    repo = repo[repo["full_name"].isin(repos)]
    cols_pr = ["id", "number", "agent", "user", "merged_at", "repo_id"]
    try:
        pr = pd.read_parquet(dir_dados / "pull_request.parquet", columns=cols_pr + ["title"])
    except Exception:  # noqa: BLE001 — revisões sem título
        pr = pd.read_parquet(dir_dados / "pull_request.parquet", columns=cols_pr)
        pr["title"] = ""
    pr = pr[pr["repo_id"].isin(repo["id"])].merge(repo.rename(columns={"id": "repo_id"}), on="repo_id")
    pr["merged_at"] = pd.to_datetime(pr["merged_at"], utc=True, errors="coerce")
    pr[["agente", "grupo"]] = pr["agent"].apply(lambda a: pd.Series(_grupo_agente(a)))

    com = pd.read_parquet(dir_dados / "pr_commits.parquet", columns=["sha", "pr_id", "author", "message"])
    com = com[com["pr_id"].isin(pr["id"])]
    com["assunto"] = com["message"].astype(str).str.split("\n").str[0]
    sinc = com["assunto"].str.match(MERGE_SINCRONIZACAO)
    from .padroes import BOT
    neutro = com["author"].astype(str).str.contains(BOT) & ~com["author"].astype(str).str.contains(AUTOR_AGENTE)
    relevantes = com[~sinc & ~neutro].copy()
    relevantes["do_agente"] = relevantes["author"].astype(str).str.contains(AUTOR_AGENTE)
    pura = relevantes.groupby("pr_id")["do_agente"].all()
    shas = com[~sinc].groupby("pr_id")["sha"].apply(list)
    assuntos = com[~sinc].groupby("pr_id")["assunto"].apply(list)

    pr["pura"] = pr["id"].map(pura).fillna(False).astype(bool)
    pr["commit_shas"] = pr["id"].map(shas)
    pr["commit_assuntos"] = pr["id"].map(assuntos)
    return pr.rename(columns={"full_name": "repo", "number": "pr_number", "title": "titulo",
                              "user": "autor_pr"})[
        ["repo", "pr_number", "agente", "grupo", "autor_pr", "merged_at", "pura", "titulo",
         "commit_shas", "commit_assuntos"]]
