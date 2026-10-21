"""P2/E2: percorre o histórico de 1º pai, identifica as PRs integradas e classifica o fluxo de cada uma.

Fluxos possíveis de uma unidade:
- FA            PR de Copilot/Devin/Jules, pura, dentro do período (D15, D7)
- HL            PR conduzida por humano (pode ter usado IA; D0), dentro do período
- fa_mista      PR do FA principal com commit humano
- fa_provavel   PR de Codex, Cursor, Claude Code (D15)
- agente_fora   assinatura de agente no git, mas fora do AIDev
- bot           dependabot, renovate etc.
- direto        commit sem marcação de PR (push direto ou rebase não recuperado)
- fora_periodo  PR antes do 1º merge FA ou depois do corte (só serve como origem/evento)

`quem_conduz` simplifica o fluxo para atribuir quem fez um evento de correção (QP2):
agente_principal · outro_agente · bot · humano.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .config import CFG
from .git import Commit, commits_do_merge, primeiro_pai
from .github import GitHub
from .padroes import (AGENTE_POR_ASSINATURA, ASSINATURA_AUTOR, ASSINATURA_BRANCH, AUTOR_AGENTE, BOT,
                      BRANCH_BOT, IA_DECLARADA, MERGE_PR, MERGE_SINCRONIZACAO, SQUASH_PR, tipo_tarefa)

PRINCIPAIS = {"copilot", "devin", "jules"}


@dataclass
class Unidade:
    unit_id: str
    repo: str
    pr_number: int | None
    modo: str                       # squash · merge · rebase · direto
    sha_b: str
    sha_a: str
    data: datetime
    titulo: str
    corpo: str
    autores: list[str]
    branch: str = ""
    commits: list[str] = field(default_factory=list)   # SHAs que pertencem à unidade (para o blame)
    mensagens: list[str] = field(default_factory=list)
    fluxo: str = ""
    agente: str = ""
    fonte_fa: str = ""
    quem_conduz: str = ""
    ia_declarada: bool = False


def _agente_por_texto(*textos: str) -> str:
    t = " ".join(textos)
    for nome, rx in AGENTE_POR_ASSINATURA:
        if rx.search(t):
            return nome
    return "desconhecido"


def identificar_unidades(repo_dir: Path, repo: str, gh: GitHub | None = None,
                         desde: datetime | None = None) -> tuple[list[Unidade], float]:
    """Retorna as unidades (PRs e commits diretos) na ordem do histórico e a fração de eventos sem marcação.

    `desde`: só os commits a partir dessa data contam para a fração e são consultados na API; os anteriores
    só servem como origem de linhas e não precisam saber a PR.
    """
    hist = primeiro_pai(repo_dir)
    unidades: list[Unidade] = []
    for c in hist:
        if not c.pais:
            continue
        m = MERGE_PR.match(c.assunto)
        if m and len(c.pais) >= 2:
            internos = commits_do_merge(repo_dir, c.sha)
            u = Unidade(f"{repo}#{m[1]}", repo, int(m[1]), "merge", c.pais[0], c.sha, c.data,
                        (c.corpo.strip().split("\n")[0] if c.corpo.strip() else c.assunto),
                        c.corpo, [], branch=m[2])
            u.commits = [c.sha] + [s for s, *_ in internos]
            for s, an, ae, msg in internos:
                if not MERGE_SINCRONIZACAO.match(msg):
                    u.autores.append(f"{an} <{ae}>")
                    u.mensagens.append(msg)
            unidades.append(u)
            continue
        m = SQUASH_PR.search(c.assunto)
        if m and len(c.pais) == 1:
            u = Unidade(f"{repo}#{m[1]}", repo, int(m[1]), "squash", c.pais[0], c.sha, c.data,
                        SQUASH_PR.sub("", c.assunto).strip(), c.corpo, [f"{c.autor} <{c.email}>"],
                        commits=[c.sha], mensagens=[c.assunto + "\n" + c.corpo])
            unidades.append(u)
            continue
        unidades.append(Unidade(f"{repo}@{c.sha[:12]}", repo, None, "direto", c.pais[0], c.sha, c.data,
                                c.assunto, c.corpo, [f"{c.autor} <{c.email}>"], commits=[c.sha],
                                mensagens=[c.assunto + "\n" + c.corpo]))
    janela = [u for u in unidades if desde is None or u.data >= desde]
    n_direto = sum(u.modo == "direto" for u in janela)
    frac = n_direto / len(janela) if janela else 0.0
    if gh is not None and gh.ativo and frac > CFG.limiar_sem_marcacao:
        unidades = _recuperar_rebase_api(unidades, repo, gh, desde)
    # PR que aparece mais de uma vez no histórico: ambígua, sai da análise
    vistos: dict[int, int] = {}
    for u in unidades:
        if u.pr_number is not None:
            vistos[u.pr_number] = vistos.get(u.pr_number, 0) + 1
    for u in unidades:
        if u.pr_number is not None and vistos[u.pr_number] > 1:
            u.fluxo = "pr_repetida"
    return unidades, frac


def _recuperar_rebase_api(unidades: list[Unidade], repo: str, gh: GitHub,
                          desde: datetime | None = None) -> list[Unidade]:
    """Liga commits sem marcação à PR de origem pela API e agrupa blocos contíguos da mesma PR (R-P3)."""
    novas: list[Unidade] = []
    total = sum(u.modo == "direto" and (desde is None or u.data >= desde) for u in unidades)
    feitos = 0
    for u in unidades:
        if u.modo != "direto" or (desde is not None and u.data < desde) or not gh.ativo:
            novas.append(u)
            continue
        feitos += 1
        if feitos % 250 == 0:
            print(f"  [{repo}] API do GitHub: {feitos}/{total} commits sem marcação", flush=True)
        prs = [p for p in gh.prs_do_commit(repo, u.sha_a) if p.get("merged_at")]
        if not prs:
            novas.append(u)
            continue
        p = prs[0]
        anterior = novas[-1] if novas else None
        if anterior is not None and anterior.modo == "rebase" and anterior.pr_number == p["number"]:
            anterior.sha_a = u.sha_a
            anterior.data = u.data
            anterior.commits.append(u.sha_a)
            anterior.mensagens += u.mensagens
            anterior.autores += u.autores
            continue
        login = (p.get("user") or {}).get("login", "")
        novas.append(Unidade(f"{repo}#{p['number']}", repo, p["number"], "rebase", u.sha_b, u.sha_a, u.data,
                             p.get("title") or u.titulo, p.get("body") or "", u.autores + [login],
                             branch=(p.get("head") or {}).get("ref", ""), commits=[u.sha_a],
                             mensagens=list(u.mensagens)))
    return novas


def _recuperar_rebase_fa(unidades: list[Unidade], agent_prs: pd.DataFrame) -> list[Unidade]:
    """PRs FA integradas por rebase: casa os assuntos dos commits do AIDev com commits diretos (±3 dias)."""
    encontrados = {u.pr_number for u in unidades if u.pr_number is not None}
    faltando = agent_prs[(agent_prs["grupo"] == "FA_principal") & agent_prs["merged_at"].notna()
                         & ~agent_prs["pr_number"].isin(encontrados)]
    for _, pr in faltando.iterrows():
        bruto = pr["commit_assuntos"]
        assuntos = set(bruto) if isinstance(bruto, (list, tuple, np.ndarray)) else set()
        if not assuntos:
            continue
        idx = [i for i, u in enumerate(unidades)
               if u.modo == "direto" and u.titulo in assuntos
               and abs((u.data - pr["merged_at"]).total_seconds()) <= 3 * 86400]
        if not idx or idx != list(range(idx[0], idx[-1] + 1)):
            continue
        bloco = [unidades[i] for i in idx]
        u = Unidade(f"{pr['repo']}#{pr['pr_number']}", pr["repo"], int(pr["pr_number"]), "rebase",
                    bloco[0].sha_b, bloco[-1].sha_a, bloco[-1].data, pr["titulo"] or bloco[0].titulo, "",
                    sum((b.autores for b in bloco), []), commits=[b.sha_a for b in bloco],
                    mensagens=sum((b.mensagens for b in bloco), []))
        unidades = unidades[:idx[0]] + [u] + unidades[idx[-1] + 1:]
    return unidades


def classificar(unidades: list[Unidade], agent_prs: pd.DataFrame, fonte_fa: str = "aidev") -> tuple[list[Unidade], datetime | None]:
    """Atribui `fluxo`, `agente` e `quem_conduz`. Devolve também o início do período (1º merge FA)."""
    if fonte_fa == "aidev" and len(agent_prs):
        unidades = _recuperar_rebase_fa(unidades, agent_prs)
    por_numero = {int(r.pr_number): r for r in agent_prs.itertuples()} if len(agent_prs) else {}

    for u in unidades:
        textos = " ".join(u.autores) + " " + u.branch
        assinatura = (any(ASSINATURA_AUTOR.search(a.split(" <")[0].strip()) or ASSINATURA_AUTOR.search(a)
                          for a in u.autores) or bool(ASSINATURA_BRANCH.search(u.branch)))
        u.ia_declarada = any(IA_DECLARADA.search(m) for m in u.mensagens + [u.corpo])
        if u.fluxo == "pr_repetida":
            u.quem_conduz = "humano"
            continue
        r = por_numero.get(u.pr_number) if u.pr_number is not None else None
        if r is not None:
            u.agente = r.agente
            if r.grupo == "FA_principal":
                u.fluxo, u.fonte_fa = ("FA", "aidev") if r.pura else ("fa_mista", "aidev")
            elif r.grupo == "FA_provavel":
                u.fluxo = "fa_provavel"
            else:
                u.fluxo = "agente_fora"
        elif assinatura:
            u.agente = _agente_por_texto(textos)
            puro = all(AUTOR_AGENTE.search(a) or BOT.search(a) for a in u.autores) if u.autores else False
            if fonte_fa == "git" and u.agente in PRINCIPAIS and u.pr_number is not None:
                u.fluxo, u.fonte_fa = ("FA", "git") if puro else ("fa_mista", "git")
            else:
                u.fluxo = "agente_fora"
        elif u.modo == "direto":
            u.fluxo = "bot" if u.autores and all(BOT.search(a) for a in u.autores) else "direto"
        elif (u.autores and all(BOT.search(a) for a in u.autores)) or BRANCH_BOT.search(u.branch):
            u.fluxo = "bot"
        else:
            u.fluxo = "HL"

        if u.fluxo in ("FA", "fa_mista") or u.agente in PRINCIPAIS:
            u.quem_conduz = "agente_principal" if u.fluxo != "fa_mista" else "humano"
        elif u.fluxo in ("fa_provavel", "agente_fora"):
            u.quem_conduz = "outro_agente"
        elif u.fluxo == "bot":
            u.quem_conduz = "bot"
        else:
            u.quem_conduz = "humano"

    datas_fa = [u.data for u in unidades if u.fluxo == "FA"]
    inicio = min(datas_fa) if datas_fa else None
    for u in unidades:
        if u.fluxo in ("FA", "HL") and (inicio is None or u.data < inicio - timedelta(hours=1) or u.data > CFG.corte):
            u.fluxo = "fora_periodo"
    return unidades, inicio


def para_tabela(unidades: list[Unidade]) -> pd.DataFrame:
    return pd.DataFrame([{
        "unit_id": u.unit_id, "repo": u.repo, "pr_number": u.pr_number, "modo": u.modo,
        "fluxo": u.fluxo, "agente": u.agente, "fonte_fa": u.fonte_fa, "quem_conduz": u.quem_conduz,
        "sha_b": u.sha_b, "sha_a": u.sha_a, "data": u.data, "titulo": u.titulo,
        "tipo_tarefa": tipo_tarefa(u.titulo), "ia_declarada": u.ia_declarada, "branch": u.branch,
        "n_commits": len(u.commits),
    } for u in unidades])
