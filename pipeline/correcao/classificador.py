"""E5b: classifica cada evento de retrabalho em corrige_defeito / evolucao / refatoracao / outro.

- `llm`: modelo de linguagem com versão fixa, prompt versionado e cache por entrada. Dois meios de chamar:
  `claude_code` (padrão) usa o Claude Code instalado e logado no computador, consumindo o plano do usuário;
  `api` usa a API da Anthropic com ANTHROPIC_API_KEY (temperatura 0).
- `heuristica`: palavras-chave no título e nas mensagens (sempre calculada, como sensibilidade).

O classificador é cego ao fluxo: nomes de agentes, trailers de coautoria e branches são removidos
do texto antes de enviar, e ele nunca recebe quem escreveu o código de origem.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from .config import CFG
from .padroes import CORRECAO_HEURISTICA

CATEGORIAS = ("corrige_defeito", "evolucao", "refatoracao", "outro")
_RAIZ = Path(__file__).resolve().parent.parent
_TRAILER = re.compile(r"^\s*(?:Co-authored-by|Signed-off-by|Generated with|🤖).*$", re.I | re.M)
_AGENTES = re.compile(r"copilot|devin|jules|codex|cursor|claude|chatgpt|openai|anthropic|gemini|\[bot\]", re.I)


def cegar(texto: str) -> str:
    return _AGENTES.sub("[ferramenta]", _TRAILER.sub("", texto or ""))


def montar_entrada(ev: dict) -> str:
    msgs = "\n".join(f"- {cegar(m).strip()}" for m in ev.get("mensagens", []) if m.strip())
    return (f"TÍTULO: {cegar(ev.get('titulo', ''))}\n\n"
            f"DESCRIÇÃO:\n{cegar(ev.get('corpo', '')).strip() or '(vazia)'}\n\n"
            f"MENSAGENS DE COMMIT:\n{msgs or '(nenhuma)'}\n\n"
            f"TRECHO DO DIFF NAS LINHAS ALTERADAS:\n{ev.get('trecho_diff', '')}")


def heuristica(ev: dict) -> str:
    texto = " ".join([ev.get("titulo", "")] + ev.get("mensagens", [])[:3])
    return "corrige_defeito" if CORRECAO_HEURISTICA.search(texto) else "nao_correcao"


class ClassificadorLLM:
    def __init__(self, dir_cache: Path, modelo: str = CFG.modelo_llm, meio: str = "claude_code"):
        self.modelo = modelo
        self.meio = meio
        self.prompt = (_RAIZ / "prompts" / f"{CFG.prompt_versao}.txt").read_text(encoding="utf-8")
        self.dir_cache = dir_cache
        self.dir_cache.mkdir(parents=True, exist_ok=True)
        self._cliente = None

    @property
    def cliente(self):
        if self._cliente is None:
            import anthropic
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError("Defina ANTHROPIC_API_KEY para usar o classificador por LLM.")
            self._cliente = anthropic.Anthropic()
        return self._cliente

    def _chave(self, entrada: str) -> str:
        return hashlib.sha256(f"{self.modelo}|{CFG.prompt_versao}|{entrada}".encode()).hexdigest()

    def _chamar_api(self, entrada: str) -> str:
        msg = self.cliente.messages.create(
            model=self.modelo, max_tokens=200, temperature=0, system=self.prompt,
            messages=[{"role": "user", "content": entrada}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    def _chamar_cli(self, entrada: str) -> str:
        """Claude Code em modo não interativo, sem ferramentas e sem MCP: só responde ao texto."""
        if not shutil.which("claude"):
            raise RuntimeError("Claude Code não encontrado: instale e faça login (`claude` no terminal).")
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}  # força o login do plano
        cmd = ["claude", "-p", "--model", self.modelo, "--tools", "", "--strict-mcp-config",
               "--no-session-persistence", "--system-prompt", self.prompt, "--output-format", "json"]
        try:
            r = subprocess.run(cmd, input=entrada, capture_output=True, text=True, timeout=180, env=env)
            d = json.loads(r.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return ""
        if d.get("is_error"):
            raise RuntimeError(f"Claude Code recusou a chamada: {str(d.get('result'))[:300]}")
        return d.get("result") or ""

    def classificar(self, entrada: str) -> dict:
        arq = self.dir_cache / f"{self._chave(entrada)}.json"
        if arq.exists():
            return json.loads(arq.read_text(encoding="utf-8"))
        res = None
        for _ in range(2):
            texto = self._chamar_cli(entrada) if self.meio == "claude_code" else self._chamar_api(entrada)
            m = re.search(r"\{.*\}", texto or "", re.S)
            try:
                res = json.loads(m.group(0)) if m else None
            except json.JSONDecodeError:
                res = None
            if res and res.get("categoria") in CATEGORIAS:
                break
            res = None
        if res is None:
            res = {"categoria": "outro", "confianca": "baixa", "justificativa": "resposta inválida", "invalida": True}
        res["modelo"] = self.modelo
        res["prompt"] = CFG.prompt_versao
        arq.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        return res


def classificar_eventos(arq_textos: Path, dir_cache: Path, usar_llm: bool, meio: str = "claude_code",
                        paralelo: int = 4) -> pd.DataFrame:
    eventos, vistos = [], set()
    for linha in arq_textos.read_text(encoding="utf-8").splitlines():
        ev = json.loads(linha)
        if ev["evento"] not in vistos:
            vistos.add(ev["evento"])
            eventos.append(ev)
    llm = ClassificadorLLM(dir_cache, meio=meio) if usar_llm else None

    def um(ev: dict) -> dict:
        reg = {"evento": ev["evento"], "repo": ev["repo"], "heuristica": heuristica(ev)}
        if llm is not None:
            r = llm.classificar(montar_entrada(ev))
            reg.update({"categoria_llm": r["categoria"], "confianca": r.get("confianca"),
                        "justificativa": r.get("justificativa")})
        return reg

    linhas = []
    with ThreadPoolExecutor(max_workers=max(1, paralelo if usar_llm else 1)) as ex:
        for i, reg in enumerate(ex.map(um, eventos), 1):
            linhas.append(reg)
            if usar_llm and i % 50 == 0:
                print(f"  {i}/{len(eventos)} eventos classificados", flush=True)
    df = pd.DataFrame(linhas)
    if len(df):
        df["correcao"] = (df["categoria_llm"] == "corrige_defeito") if usar_llm else \
            (df["heuristica"] == "corrige_defeito")
        df["fonte_rotulo"] = f"llm:{meio}" if usar_llm else "heuristica"
    return df
