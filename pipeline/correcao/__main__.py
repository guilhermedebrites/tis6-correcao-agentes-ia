"""Linha de comando.

    python -m correcao baixar                      # baixa o AIDev (1x, ~200 MB sem pr_commit_details)
    python -m correcao p1 --familia python         # monta out/agent_prs.parquet a partir de ../dados/amostra.csv
    python -m correcao p2 --familia python -w 3    # processa os repositórios da amostra
    python -m correcao classificar [--llm]         # rotula os eventos (heurística ou LLM)
    python -m correcao analisar                    # QP1–QP3 → out/resultados/relatorio.md
    python -m correcao tudo --familia python --llm # tudo em sequência
    python -m correcao validacao-amostra -n 80     # planilha para duas pessoas rotularem
    python -m correcao validacao-medir arq.csv     # kappa entre pessoas, precisão do classificador
"""
from __future__ import annotations

import argparse
import json
import sys
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import CFG

RAIZ = Path.cwd()


def _repos_da_amostra(amostra: Path, familia: str, repos: list[str] | None) -> list[str]:
    if repos:
        return repos
    df = pd.read_csv(amostra)
    df = df[(df["familia"] == familia) & df["status"].isin(["incluido", "incluir_confirmar_hl"])]
    return df["full_name"].tolist()


def cmd_baixar(a):
    from .aidev import baixar
    baixar(Path(a.dados))


def cmd_p1(a):
    from .aidev import montar_agent_prs
    repos = _repos_da_amostra(Path(a.amostra), a.familia, a.repos)
    df = montar_agent_prs(Path(a.dados), repos)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    arq = out / f"agent_prs_{a.familia}.parquet"
    df.to_parquet(arq, index=False)
    print(f"{len(df)} PRs de agentes em {df['repo'].nunique()} repositórios → {arq}")


def cmd_p2(a):
    from .executar import processar_repo
    out = Path(a.out)
    repos = _repos_da_amostra(Path(a.amostra), a.familia, a.repos)
    arq = out / f"agent_prs_{a.familia}.parquet"
    if a.fonte_fa == "aidev":
        if not arq.exists():
            sys.exit(f"{arq} não existe: rode `python -m correcao p1` antes (ou use --fonte-fa git).")
        agent_prs = pd.read_parquet(arq)
    else:
        agent_prs = pd.DataFrame(columns=["repo", "pr_number", "agente", "grupo", "merged_at", "pura",
                                          "titulo", "commit_shas", "commit_assuntos"])
    dir_clones = Path(a.clones)
    print(f"Processando {len(repos)} repositórios ({a.familia}, FA por {a.fonte_fa}) com {a.workers} processos")
    # spawn evita travamentos de fork com threads de bibliotecas numéricas
    with ProcessPoolExecutor(max_workers=a.workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(processar_repo, r, a.familia, agent_prs, dir_clones, out, a.fonte_fa): r for r in repos}
        for f in as_completed(futs):
            s = f.result()
            if "erro" in s:
                print(f"  ERRO {s['repo']}: {s['erro']}")
            else:
                print(flush=True, end="")
                print(f"  {s['repo']}: FA {s['fa_validas']} · HL {s['hl_validas']} · "
                      f"{'incluído' if s['incluido'] else 'excluído'} · eventos {s['n_eventos']}")
    _manifesto(out, a)


def cmd_classificar(a):
    from .classificador import classificar_eventos
    out = Path(a.out)
    todos = out / "eventos_texto.jsonl"
    with todos.open("w", encoding="utf-8") as f:
        for p in sorted((out / "repos").glob("*/eventos_texto.jsonl")):
            f.write(p.read_text(encoding="utf-8"))
    df = classificar_eventos(todos, Path(a.cache), a.llm)
    df.to_csv(out / "rotulos.csv", index=False)
    print(f"{len(df)} eventos rotulados ({'llm' if a.llm else 'heurística'}) → {out / 'rotulos.csv'}")
    if len(df) and a.llm:
        print(pd.crosstab(df["categoria_llm"], df["heuristica"]))


def cmd_analisar(a):
    from .analise import analisar
    out = Path(a.out)
    rot = pd.read_csv(out / "rotulos.csv") if (out / "rotulos.csv").exists() else pd.DataFrame(columns=["evento", "correcao"])
    analisar(out, rot)
    print(f"Relatório em {out / 'resultados' / 'relatorio.md'}")


def cmd_validacao_amostra(a):
    from .validacao import sortear
    print(f"Planilha para rotular: {sortear(Path(a.out), a.n)}")


def cmd_validacao_medir(a):
    from .validacao import medir
    print(json.dumps(medir(Path(a.out), Path(a.arquivo)), indent=2))


def cmd_tudo(a):
    if a.fonte_fa == "aidev":
        cmd_p1(a)
    cmd_p2(a)
    cmd_classificar(a)
    cmd_analisar(a)


def _manifesto(out: Path, a):
    import platform
    import subprocess
    import lizard
    m = {"executado_em": datetime.now(timezone.utc).isoformat(), "parametros": CFG.manifesto(),
         "argumentos": {k: v for k, v in vars(a).items() if k != "func"},
         "python": platform.python_version(), "lizard": getattr(lizard, "version", "?"),
         "git": subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()}
    (out / "manifesto.json").write_text(json.dumps(m, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(prog="correcao", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="out")
    ap.add_argument("--dados", default="data/aidev")
    ap.add_argument("--clones", default="data/clones")
    ap.add_argument("--cache", default="data/llm_cache")
    ap.add_argument("--amostra", default="../dados/amostra.csv")
    sub = ap.add_subparsers(required=True)

    def comum(p):
        p.add_argument("--familia", default="python", choices=CFG.familias)
        p.add_argument("--repos", nargs="*", help="lista explícita (owner/nome); padrão: amostra")
        p.add_argument("--fonte-fa", default="aidev", choices=["aidev", "git"],
                       help="git = identifica FA por assinatura no histórico (só para teste, sem AIDev)")
        p.add_argument("-w", "--workers", type=int, default=3)

    sub.add_parser("baixar").set_defaults(func=cmd_baixar)
    p = sub.add_parser("p1"); comum(p); p.set_defaults(func=cmd_p1)
    p = sub.add_parser("p2"); comum(p); p.set_defaults(func=cmd_p2)
    p = sub.add_parser("classificar"); p.add_argument("--llm", action="store_true"); p.set_defaults(func=cmd_classificar)
    sub.add_parser("analisar").set_defaults(func=cmd_analisar)
    p = sub.add_parser("validacao-amostra"); p.add_argument("-n", type=int, default=80)
    p.set_defaults(func=cmd_validacao_amostra)
    p = sub.add_parser("validacao-medir"); p.add_argument("arquivo"); p.set_defaults(func=cmd_validacao_medir)
    p = sub.add_parser("tudo"); comum(p); p.add_argument("--llm", action="store_true"); p.set_defaults(func=cmd_tudo)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
