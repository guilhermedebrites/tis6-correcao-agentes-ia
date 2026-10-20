"""Validação do classificador: sorteia eventos para rotulação manual e mede a concordância.

Amostra estratificada: metade dos eventos que o classificador marcou como correção, metade que não,
equilibrada entre eventos que corrigem código FA e código HL. A planilha não mostra o rótulo do
modelo nem quem escreveu o código de origem.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import CFG

CATS = ["corrige_defeito", "evolucao", "refatoracao", "outro"]


def _origens(out: Path) -> pd.DataFrame:
    partes = [pd.read_csv(p, usecols=["origem", "evento"]) for p in (out / "repos").glob("*/eventos.csv")
              if p.stat().st_size > 1]
    ev = pd.concat(partes) if partes else pd.DataFrame(columns=["origem", "evento"])
    unid = pd.concat([pd.read_csv(p, usecols=["unit_id", "fluxo"]) for p in (out / "repos").glob("*/unidades.csv")])
    ev = ev.merge(unid.rename(columns={"unit_id": "origem", "fluxo": "fluxo_origem"}), on="origem", how="left")
    return ev.groupby("evento")["fluxo_origem"].agg(lambda s: "FA" if (s == "FA").any() else "HL").reset_index()


def sortear(out: Path, n: int = 80) -> Path:
    rot = pd.read_csv(out / "rotulos.csv").merge(_origens(out), on="evento", how="left")
    textos = {}
    for linha in (out / "eventos_texto.jsonl").read_text(encoding="utf-8").splitlines():
        t = json.loads(linha)
        textos.setdefault(t["evento"], t)
    rng = np.random.default_rng(CFG.semente)
    escolhidos = []
    por_celula = n // 4
    for corr in (True, False):
        for fl in ("FA", "HL"):
            g = rot[(rot["correcao"] == corr) & (rot["fluxo_origem"] == fl)]
            escolhidos.append(g.sample(min(por_celula, len(g)), random_state=int(rng.integers(1e9))))
    am = pd.concat(escolhidos).sample(frac=1, random_state=CFG.semente)
    linhas = []
    for r in am.itertuples():
        t = textos.get(r.evento, {})
        repo, _, ref = r.evento.partition("#") if "#" in r.evento else (r.evento.split("@")[0], "", "")
        link = f"https://github.com/{repo}/pull/{ref}" if ref else f"https://github.com/{r.evento.split('@')[0]}/commits"
        linhas.append({"evento": r.evento, "link": link, "titulo": t.get("titulo", ""),
                       "descricao": t.get("corpo", "")[:500], "trecho_diff": t.get("trecho_diff", "")[:3000],
                       "rotulo_a": "", "rotulo_b": "", "consenso": ""})
    arq = out / "validacao_amostra.csv"
    pd.DataFrame(linhas).to_csv(arq, index=False)
    am[["evento", "correcao", "fluxo_origem"]].to_csv(out / "validacao_gabarito_oculto.csv", index=False)
    return arq


def _kappa(a: pd.Series, b: pd.Series) -> float:
    cats = sorted(set(a) | set(b))
    po = (a == b).mean()
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def medir(out: Path, arq_rotulado: Path) -> dict:
    df = pd.read_csv(arq_rotulado).dropna(subset=["rotulo_a", "rotulo_b"])
    gab = pd.read_csv(out / "validacao_gabarito_oculto.csv")
    df = df.merge(gab, on="evento")
    df["final"] = np.where(df["rotulo_a"] == df["rotulo_b"], df["rotulo_a"], df["consenso"])
    df = df[df["final"].isin(CATS)]
    humano_fix = df["final"] == "corrige_defeito"
    res = {"n": len(df), "kappa_humanos": _kappa(df["rotulo_a"], df["rotulo_b"]),
           "kappa_humanos_binario": _kappa(df["rotulo_a"] == "corrige_defeito", df["rotulo_b"] == "corrige_defeito")}
    for nome, sub in [("geral", df)] + list(df.groupby("fluxo_origem")):
        h = sub["final"] == "corrige_defeito"
        m = sub["correcao"].astype(bool)
        res[f"precisao_{nome}"] = float((h & m).sum() / m.sum()) if m.sum() else None
        res[f"revocacao_{nome}"] = float((h & m).sum() / h.sum()) if h.sum() else None
    (out / "validacao_resultado.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res
