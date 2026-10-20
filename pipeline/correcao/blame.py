"""E5: para cada evento posterior, descobre de que PR vinham as linhas que ele alterou ou removeu.

Lógica estilo SZZ: para cada evento E (PR integrada ou commit direto), as linhas removidas por E
são atribuídas por `git blame -w -M -C` no estado imediatamente anterior (E^1). A linha conta
como retrabalho da PR de origem C se E acontece em até W dias depois de C. Uma linha só pode ser
retrabalhada uma vez (depois de alterada, ela passa a pertencer a E).

Também registra a atividade de cada tipo de condutor no período (linha de base da QP2) e o churn
anterior dos arquivos (oportunidade de correção, QP3).
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import pandas as pd

from .config import CFG
from .git import blame, diff, git
from .historico import Unidade
from .padroes import arquivo_considerado, linha_logica


def _indice_arquivos(repo_dir: Path, desde, ate) -> dict[str, list]:
    """Datas em que cada arquivo foi alterado no 1º pai (para o churn anterior)."""
    out = git(repo_dir, "log", "--first-parent", "-m", "--name-only", "--format=\x1e%cI",
              f"--since={desde.isoformat()}", f"--until={ate.isoformat()}")
    idx: dict[str, list] = defaultdict(list)
    for bloco in out.split("\x1e"):
        linhas = [l for l in bloco.strip().splitlines() if l]
        if not linhas:
            continue
        data = pd.Timestamp(linhas[0])
        for caminho in linhas[1:]:
            idx[caminho].append(data)
    return idx


def rastrear(repo_dir: Path, unidades: list[Unidade], validas: dict[str, dict], familia: str,
             saida_texto: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """`validas`: unit_id → {"data", "arquivos"} das PRs FA/HL válidas (origens que interessam).

    Retorna (eventos, oportunidade, atividade):
    - eventos: uma linha por (origem, evento) com o número de linhas lógicas da origem alteradas;
    - oportunidade: churn dos arquivos da origem nos W dias anteriores;
    - atividade: linhas lógicas removidas por tipo de condutor no período (linha de base da QP2).
    """
    W = timedelta(days=CFG.janela_dias)
    if not validas:
        return pd.DataFrame(), pd.DataFrame(), {}
    ini = min(v["data"] for v in validas.values())
    fim = max(v["data"] for v in validas.values()) + W

    dono: dict[str, str] = {}
    por_id = {}
    for u in unidades:
        por_id[u.unit_id] = u
        for s in u.commits:
            dono.setdefault(s, u.unit_id)

    linhas_eventos = []
    atividade: dict[str, int] = defaultdict(int)
    textos = []
    for e in unidades:
        if not (ini < e.data <= fim):
            continue
        trechos = []
        for d in diff(repo_dir, e.sha_b, e.sha_a):
            if not d.caminho_b or not d.removidas or not arquivo_considerado(d.caminho_b, familia):
                continue
            atrib = blame(repo_dir, e.sha_b, d.caminho_b, d.removidas)
            por_origem: dict[str, list[int]] = defaultdict(list)
            for n, (sha, texto) in atrib.items():
                if not linha_logica(texto, familia):
                    continue
                atividade[e.quem_conduz] += 1
                origem = dono.get(sha)
                if origem is None or origem not in validas or origem == e.unit_id:
                    continue
                dt = e.data - validas[origem]["data"]
                if timedelta(0) < dt <= W:
                    por_origem[origem].append(n)
            if not por_origem:
                continue
            alvo = {n for ns in por_origem.values() for n in ns}
            for ib, nb, ia, na, corpo in d.hunks:
                if any(ib <= n < ib + max(nb, 1) for n in alvo):
                    trechos.append(f"--- {d.caminho_b}\n@@ -{ib},{nb} +{ia},{na} @@\n" + "\n".join(corpo))
            for origem, ns in por_origem.items():
                linhas_eventos.append({
                    "origem": origem, "evento": e.unit_id, "evento_sha": e.sha_a,
                    "evento_quem": e.quem_conduz, "evento_fluxo": e.fluxo, "data_evento": e.data,
                    "dias": (e.data - validas[origem]["data"]).total_seconds() / 86400,
                    "arquivo": d.caminho_b, "linhas": len(ns)})
        if trechos:
            textos.append({"evento": e.unit_id, "repo": e.repo, "titulo": e.titulo,
                           "corpo": (e.corpo or "")[:CFG.max_chars_descricao],
                           "mensagens": [m[:200] for m in e.mensagens[:10]],
                           "trecho_diff": "\n".join("\n".join(trechos).splitlines()[:CFG.max_linhas_diff])})

    with saida_texto.open("a", encoding="utf-8") as f:
        for t in textos:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    eventos = pd.DataFrame(linhas_eventos)
    if len(eventos):
        eventos = (eventos.groupby(["origem", "evento", "evento_sha", "evento_quem", "evento_fluxo",
                                    "data_evento", "dias"], as_index=False)["linhas"].sum())

    idx = _indice_arquivos(repo_dir, ini - W, fim)
    op = []
    for uid, v in validas.items():
        d0 = pd.Timestamp(v["data"])
        n = sum(1 for a in v["arquivos"] for t in idx.get(a, []) if d0 - pd.Timedelta(W) <= t < d0)
        op.append({"unit_id": uid, "churn_anterior": n / max(len(v["arquivos"]), 1)})
    return eventos, pd.DataFrame(op), dict(atividade)
