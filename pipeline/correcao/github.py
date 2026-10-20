"""Consultas à API REST do GitHub, com cache em disco. Só é usada se houver GITHUB_TOKEN."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


class GitHub:
    def __init__(self, dir_cache: Path, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.dir_cache = dir_cache
        self.consultas = 0
        self.falhas_seguidas = 0

    @property
    def ativo(self) -> bool:
        return bool(self.token)

    def get(self, caminho: str):
        arq = self.dir_cache / (caminho.strip("/").replace("/", "__") + ".json")
        if arq.exists():
            return json.loads(arq.read_text(encoding="utf-8"))
        if not self.ativo:
            return None
        req = urllib.request.Request(
            "https://api.github.com" + caminho,
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28"})
        for tentativa in range(4):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    dados = json.load(r)
                    restante = int(r.headers.get("X-RateLimit-Remaining", "100"))
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    dados, restante = None, 100
                    break
                if e.code in (403, 429):
                    reset = int(e.headers.get("X-RateLimit-Reset", time.time() + 60))
                    time.sleep(max(5, reset - time.time() + 1))
                    continue
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(2 ** tentativa)
        else:
            # API inacessível: depois de 3 falhas seguidas, desliga para não travar a execução
            self.falhas_seguidas += 1
            if self.falhas_seguidas >= 3:
                print("  aviso: API do GitHub inacessível; seguindo sem ela", flush=True)
                self.token = None
            return None
        self.falhas_seguidas = 0
        self.consultas += 1
        if restante < 20:
            time.sleep(60)
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(dados), encoding="utf-8")
        return dados

    def prs_do_commit(self, repo: str, sha: str) -> list[dict]:
        return self.get(f"/repos/{repo}/commits/{sha}/pulls") or []

    def pr(self, repo: str, numero: int) -> dict | None:
        return self.get(f"/repos/{repo}/pulls/{numero}")
