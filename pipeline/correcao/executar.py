"""Orquestra a P2 por repositório: clone → unidades → classificação → filtros → blame."""
from __future__ import annotations

import json
import traceback
from pathlib import Path

import pandas as pd

from .blame import rastrear
from .config import CFG
from .git import clonar, git
from .github import GitHub
from .historico import classificar, identificar_unidades, para_tabela
from .metricas import medir


def _pasta(out: Path, repo: str) -> Path:
    p = out / "repos" / repo.replace("/", "__")
    p.mkdir(parents=True, exist_ok=True)
    return p


def processar_repo(repo: str, familia: str, agent_prs: pd.DataFrame, dir_clones: Path, out: Path,
                   fonte_fa: str = "aidev") -> dict:
    pasta = _pasta(out, repo)

    def log(msg: str) -> None:
        print(f"  [{repo}] {msg}", flush=True)

    try:
        log("clonando…")
        repo_dir = clonar(repo, dir_clones / repo.replace("/", "__"))
        log("lendo o histórico")
        snapshot = git(repo_dir, "rev-parse", "HEAD").strip()
        gh = GitHub(out.parent / "data" / "github_cache")
        unidades, frac_sem_marcacao = identificar_unidades(repo_dir, repo, gh)
        unidades, inicio = classificar(unidades, agent_prs[agent_prs["repo"] == repo], fonte_fa)
        tab = para_tabela(unidades)

        log(f"medindo {sum(u.fluxo in ('FA', 'HL') for u in unidades)} PRs FA/HL")
        # Medidas e filtros (E3) só para as PRs FA/HL do período
        medidas = {}
        for u in unidades:
            if u.fluxo in ("FA", "HL"):
                medidas[u.unit_id] = medir(repo_dir, u.sha_b, u.sha_a, familia)
        cols = ["adicionadas", "removidas", "size_churn", "n_arquivos", "frac_arquivo_novo",
                "cc_delta", "cc_depois_max", "so_formatacao", "erro_parse"]
        for c in cols:
            tab[c] = tab["unit_id"].map(lambda uid: getattr(medidas[uid], c) if uid in medidas else None)

        tab["motivo_exclusao"] = ""
        alvo = tab["fluxo"].isin(["FA", "HL"])
        regras = [
            ("sem_arquivo_considerado", tab["n_arquivos"].fillna(0) == 0),
            ("so_formatacao", tab["so_formatacao"].fillna(False).astype(bool)),
            ("sem_linhas_adicionadas", tab["adicionadas"].fillna(0) == 0),
            ("pequena_demais", tab["size_churn"].fillna(0) < CFG.min_size_churn),
            ("grande_demais", tab["size_churn"].fillna(0) > CFG.max_size_churn),
        ]
        for motivo, cond in regras:
            m = alvo & (tab["motivo_exclusao"] == "") & cond
            tab.loc[m, "motivo_exclusao"] = motivo
        ok = alvo & (tab["motivo_exclusao"] == "")
        if ok.any():
            p99 = tab.loc[ok, "size_churn"].quantile(CFG.percentil_max, interpolation="higher")
            tab.loc[ok & (tab["size_churn"] > p99), "motivo_exclusao"] = "acima_p99"
        tab["valida"] = alvo & (tab["motivo_exclusao"] == "")
        n_fa = int((tab["valida"] & (tab["fluxo"] == "FA")).sum())
        n_hl = int((tab["valida"] & (tab["fluxo"] == "HL")).sum())
        incluido = n_fa >= CFG.min_fa_validas and n_hl >= CFG.min_hl_validas

        validas = {r.unit_id: {"data": r.data, "arquivos": medidas[r.unit_id].arquivos}
                   for r in tab[tab["valida"]].itertuples()} if incluido else {}
        if incluido:
            log(f"rastreando correções (blame) de {n_fa} FA e {n_hl} HL")
        arq_texto = pasta / "eventos_texto.jsonl"
        arq_texto.unlink(missing_ok=True)
        arq_texto.touch()
        eventos, oportunidade, atividade = rastrear(repo_dir, unidades, validas, familia, arq_texto)
        if len(oportunidade):
            tab = tab.merge(oportunidade, on="unit_id", how="left")

        tab.to_csv(pasta / "unidades.csv", index=False)
        eventos.to_csv(pasta / "eventos.csv", index=False)
        status = {
            "repo": repo, "familia": familia, "snapshot": snapshot, "fonte_fa": fonte_fa,
            "inicio_periodo": inicio.isoformat() if inicio else None,
            "frac_sem_marcacao": round(frac_sem_marcacao, 3), "api_consultas": gh.consultas,
            "fa_validas": n_fa, "hl_validas": n_hl, "incluido": incluido,
            "atividade_linhas": atividade, "n_eventos": int(eventos["evento"].nunique()) if len(eventos) else 0,
            "funil": tab[alvo].groupby(["fluxo", "motivo_exclusao"]).size().rename("n").reset_index()
                     .to_dict(orient="records"),
            "fluxos": tab["fluxo"].value_counts().to_dict(),
        }
    except Exception as e:  # noqa: BLE001 — um repositório com problema não derruba a execução
        status = {"repo": repo, "familia": familia, "erro": f"{type(e).__name__}: {e}",
                  "traceback": traceback.format_exc()[-2000:], "incluido": False}
    (pasta / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False, default=str),
                                       encoding="utf-8")
    return status
