"""E3/E4: filtros da unidade e medidas da PR de origem (tamanho, novidade, complexidade introduzida).

A complexidade usa o Lizard nas duas famílias (Python e JS/TS), o que deixa a medida uniforme.
Ela é um fator explicativo da QP3, não uma pergunta própria.
"""
from __future__ import annotations

import ast
import warnings
from dataclasses import dataclass
from pathlib import Path

import lizard

from .git import diff, mostrar
from .padroes import arquivo_considerado, linha_logica


@dataclass
class MedidaUnidade:
    adicionadas: int = 0          # linhas lógicas adicionadas (denominador da taxa de correção)
    removidas: int = 0
    n_arquivos: int = 0
    frac_arquivo_novo: float = 0.0
    cc_delta: float = 0.0         # Σ [CC(A) − CC(B)] nas funções tocadas
    cc_depois_max: float = 0.0
    so_formatacao: bool = False
    erro_parse: int = 0
    arquivos: tuple = ()

    @property
    def size_churn(self) -> int:
        return self.adicionadas + self.removidas


def _ast_igual(b: str | None, a: str | None) -> bool | None:
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    try:
        tb = ast.dump(ast.parse(b or ""), annotate_fields=False, include_attributes=False)
        ta = ast.dump(ast.parse(a or ""), annotate_fields=False, include_attributes=False)
    except (SyntaxError, ValueError):
        return None
    return tb == ta


def _funcoes(caminho: str, codigo: str | None):
    if not codigo:
        return []
    try:
        return lizard.analyze_file.analyze_source_code(caminho, codigo).function_list
    except Exception:  # noqa: BLE001 — o Lizard falha em alguns arquivos; a unidade segue sem CC
        return []


def _tocadas(funcs, linhas: set[int]) -> dict[str, int]:
    res: dict[str, int] = {}
    for f in funcs:
        if any(f.start_line <= n <= f.end_line for n in linhas):
            res[f.long_name] = f.cyclomatic_complexity
    return res


def medir(repo_dir: Path, sha_b: str, sha_a: str, familia: str) -> MedidaUnidade:
    m = MedidaUnidade()
    arquivos = [d for d in diff(repo_dir, sha_b, sha_a)
                if arquivo_considerado(d.caminho_a or d.caminho_b or "", familia)]
    formatacao = []
    novos = 0
    nomes = []
    for d in arquivos:
        cod_b = mostrar(repo_dir, sha_b, d.caminho_b) if d.caminho_b else None
        cod_a = mostrar(repo_dir, sha_a, d.caminho_a) if d.caminho_a else None
        lin_b = (cod_b or "").splitlines()
        lin_a = (cod_a or "").splitlines()
        add = [n for n in d.adicionadas if 0 < n <= len(lin_a) and linha_logica(lin_a[n - 1], familia)]
        rem = [n for n in d.removidas if 0 < n <= len(lin_b) and linha_logica(lin_b[n - 1], familia)]
        if not add and not rem:
            continue
        nomes.append(d.caminho_a or d.caminho_b)
        m.adicionadas += len(add)
        m.removidas += len(rem)
        if d.status == "A":
            novos += len(add)
        if familia == "python":
            igual = _ast_igual(cod_b, cod_a)
            if igual is None:
                m.erro_parse += 1
            formatacao.append(bool(igual))
        else:
            formatacao.append(False)
        fb = _tocadas(_funcoes(d.caminho_b or "x", cod_b), set(rem))
        fa = _tocadas(_funcoes(d.caminho_a or "x", cod_a), set(add))
        for nome, cc in fa.items():
            m.cc_delta += cc - fb.get(nome, 0)
            m.cc_depois_max = max(m.cc_depois_max, cc)
    m.n_arquivos = len(nomes)
    m.arquivos = tuple(nomes)
    m.frac_arquivo_novo = novos / m.adicionadas if m.adicionadas else 0.0
    m.so_formatacao = bool(formatacao) and all(formatacao)
    return m
