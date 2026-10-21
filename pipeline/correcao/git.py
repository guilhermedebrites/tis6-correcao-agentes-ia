"""Chamadas ao git. Tudo é lido de SHAs fixos (sem checkout), então o resultado não depende da cópia de trabalho."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def git(repo: Path, *args: str, ok_codes: tuple = (0,)) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode not in ok_codes:
        raise RuntimeError(f"git {' '.join(args[:3])}… falhou: {r.stderr.strip()[:300]}")
    return r.stdout


def clonar(full_name: str, destino: Path, desde: str | None = None) -> Path:
    """Clone completo da branch padrão (o blame precisa dos blobs). `desde` encurta repositórios gigantes."""
    if (destino / ".git").exists() or (destino / "HEAD").exists():
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--quiet", "--single-branch", "--no-tags"]
    if desde:
        cmd += [f"--shallow-since={desde}"]
    cmd += [f"https://github.com/{full_name}.git", str(destino)]
    subprocess.run(cmd, check=True)
    return destino


@dataclass
class Commit:
    sha: str
    pais: list[str]
    autor: str
    email: str
    data_autor: datetime
    data: datetime          # data do commit (momento da integração na branch)
    assunto: str
    corpo: str


_SEP, _FIM = "\x1f", "\x1e"


def primeiro_pai(repo: Path, ref: str = "HEAD") -> list[Commit]:
    """Histórico de 1º pai, do mais antigo para o mais novo."""
    fmt = _SEP.join(["%H", "%P", "%an", "%ae", "%aI", "%cI", "%s", "%b"]) + _FIM
    out = git(repo, "log", "--first-parent", "--reverse", f"--format={fmt}", ref)
    commits = []
    for reg in out.split(_FIM):
        reg = reg.strip("\n")
        if not reg:
            continue
        sha, pais, an, ae, ad, cd, s, b = reg.split(_SEP)
        commits.append(Commit(sha, pais.split(), an, ae, datetime.fromisoformat(ad),
                              datetime.fromisoformat(cd), s, b))
    return commits


def commits_do_merge(repo: Path, merge_sha: str) -> list[tuple[str, str, str, str]]:
    """(sha, autor, email, mensagem) dos commits trazidos por um merge commit (M^1..M^2)."""
    fmt = _SEP.join(["%H", "%an", "%ae", "%B"]) + _FIM
    out = git(repo, "log", f"--format={fmt}", f"{merge_sha}^1..{merge_sha}^2")
    res = []
    for reg in out.split(_FIM):
        reg = reg.strip("\n")
        if reg:
            sha, an, ae, msg = reg.split(_SEP, 3)
            res.append((sha, an, ae, msg))
    return res


def mostrar(repo: Path, sha: str, caminho: str) -> str | None:
    r = subprocess.run(["git", "-C", str(repo), "show", f"{sha}:{caminho}"], capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")


@dataclass
class ArquivoDiff:
    status: str              # A, M, D, R
    caminho_b: str | None    # caminho antes
    caminho_a: str | None    # caminho depois
    removidas: list[int]     # números de linha em B
    adicionadas: list[int]   # números de linha em A
    hunks: list[tuple[int, int, int, int, list[str]]]  # (ini_b, n_b, ini_a, n_a, linhas do hunk)


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def diff(repo: Path, b: str, a: str) -> list[ArquivoDiff]:
    """`git diff -U0 -M B A`, com números de linha removidas (em B) e adicionadas (em A) por arquivo."""
    out = git(repo, "diff", "-U0", "-M", "--no-color", "--no-ext-diff", b, a)
    arquivos: list[ArquivoDiff] = []
    atual: ArquivoDiff | None = None
    hunk = None
    lb = la = 0
    for linha in out.splitlines():
        if linha.startswith("diff --git "):
            atual = ArquivoDiff("M", None, None, [], [], [])
            arquivos.append(atual)
            hunk = None
        elif atual is None:
            continue
        elif linha.startswith("--- "):
            atual.caminho_b = None if linha[4:] == "/dev/null" else linha[6:]
        elif linha.startswith("+++ "):
            atual.caminho_a = None if linha[4:] == "/dev/null" else linha[6:]
            if atual.caminho_b is None:
                atual.status = "A"
            elif atual.caminho_a is None:
                atual.status = "D"
            elif atual.caminho_a != atual.caminho_b:
                atual.status = "R"
        elif linha.startswith("rename from "):
            atual.caminho_b, atual.status = linha[12:], "R"
        elif linha.startswith("rename to "):
            atual.caminho_a = linha[10:]
        elif linha.startswith("@@"):
            m = _HUNK.match(linha)
            if not m:
                continue
            ib, nb, ia, na = int(m[1]), int(m[2] or 1), int(m[3]), int(m[4] or 1)
            hunk = (ib, nb, ia, na, [])
            atual.hunks.append(hunk)
            lb, la = ib, ia
        elif hunk is not None and linha[:1] in ("+", "-") and not linha.startswith(("+++", "---")):
            hunk[4].append(linha)
            if linha[0] == "-":
                atual.removidas.append(lb)
                lb += 1
            else:
                atual.adicionadas.append(la)
                la += 1
    return arquivos


def _faixas(linhas: list[int]) -> list[tuple[int, int]]:
    faixas = []
    for n in sorted(set(linhas)):
        if faixas and n == faixas[-1][1] + 1:
            faixas[-1] = (faixas[-1][0], n)
        else:
            faixas.append((n, n))
    return faixas


def blame(repo: Path, rev: str, caminho: str, linhas: list[int]) -> dict[int, tuple[str, str]]:
    """Para cada linha pedida (numeração em `rev`), o commit de origem e o texto. `git blame -w -M -C`."""
    if not linhas:
        return {}
    args = ["blame", "--porcelain", "-w", "-M", "-C"]
    for ini, fim in _faixas(linhas):
        args += ["-L", f"{ini},{fim}"]
    args += [rev, "--", caminho]
    try:
        out = git(repo, *args)
    except RuntimeError:
        return {}
    res: dict[int, tuple[str, str]] = {}
    sha = None
    num = None
    for linha in out.splitlines():
        if linha.startswith("\t"):
            if sha is not None and num is not None:
                res[num] = (sha, linha[1:])
            sha = num = None
        else:
            partes = linha.split(" ")
            if len(partes) >= 3 and len(partes[0]) == 40 and all(c in "0123456789abcdef" for c in partes[0]):
                sha, num = partes[0], int(partes[2])
    return res
