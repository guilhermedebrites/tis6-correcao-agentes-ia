"""Teste com um repositório git sintético: uma PR de agente, uma correção humana e uma evolução."""
import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from correcao.blame import rastrear
from correcao.historico import classificar, identificar_unidades
from correcao.metricas import medir
from correcao.padroes import tipo_tarefa


def _commit(repo, msg, autor, data, arquivos):
    for nome, texto in arquivos.items():
        (repo / nome).write_text(texto)
        subprocess.run(["git", "-C", repo, "add", nome], check=True)
    env = {**os.environ, "GIT_AUTHOR_NAME": autor, "GIT_AUTHOR_EMAIL": f"{autor}@x", "GIT_COMMITTER_NAME": "gh",
           "GIT_COMMITTER_EMAIL": "gh@x", "GIT_AUTHOR_DATE": data, "GIT_COMMITTER_DATE": data}
    subprocess.run(["git", "-C", repo, "commit", "-q", "-m", msg], check=True, env=env)


def test_atribuicao_de_correcao():
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        subprocess.run(["git", "init", "-q", "-b", "main", repo], check=True)
        _commit(repo, "base", "ana", "2025-06-01T10:00:00Z", {"app.py": "def a():\n    return 1\n"})
        _commit(repo, "Add soma (#1)", "Copilot", "2025-06-10T10:00:00Z",
                {"app.py": "def a():\n    return 1\n\ndef soma(x, y):\n    if x:\n        return x - y\n    return y\n"})
        _commit(repo, "Fix soma sign (#2)", "bruno", "2025-06-20T10:00:00Z",
                {"app.py": "def a():\n    return 1\n\ndef soma(x, y):\n    if x:\n        return x + y\n    return y\n"})
        _commit(repo, "Add mult (#3)", "carla", "2025-12-20T10:00:00Z",
                {"app.py": "def a():\n    return 2\n\ndef soma(x, y):\n    if x:\n        return x + y\n    return y\n"})
        unidades, _ = identificar_unidades(repo, "o/r")
        unidades, inicio = classificar(unidades, pd.DataFrame(columns=["repo"]), fonte_fa="git")
        fluxos = {u.pr_number: u.fluxo for u in unidades}
        assert fluxos[1] == "FA" and fluxos[2] == "HL"
        assert fluxos[3] == "fora_periodo"          # depois do corte
        u1 = next(u for u in unidades if u.pr_number == 1)
        m = medir(repo, u1.sha_b, u1.sha_a, "python")
        assert m.adicionadas == 4 and m.cc_delta == 2
        validas = {u1.unit_id: {"data": u1.data, "arquivos": m.arquivos}}
        arq = repo / "textos.jsonl"
        arq.touch()
        eventos, _, atividade = rastrear(repo, unidades, validas, "python", arq)
        assert len(eventos) == 1
        e = eventos.iloc[0]
        assert e["evento"] == "o/r#2" and e["evento_quem"] == "humano" and e["linhas"] == 1
        assert "Fix soma" in arq.read_text()


def test_tipo_tarefa():
    assert tipo_tarefa("fix(api): crash on empty") == "fix"
    assert tipo_tarefa("Add retry option") == "feat"
    assert tipo_tarefa("Refactor parser") == "refactor"
