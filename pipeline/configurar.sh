#!/usr/bin/env bash
# Prepara o ambiente e guarda as chaves só neste computador (pipeline/.env, fora do git).
# Uso: cd pipeline && bash configurar.sh
set -euo pipefail
cd "$(dirname "$0")"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
falha(){ printf "  \033[31m✗\033[0m %s\n" "$1"; }

echo "1/5 Ambiente Python"
command -v python3 >/dev/null || { falha "python3 não encontrado (instale com: brew install python)"; exit 1; }
command -v git >/dev/null || { falha "git não encontrado (instale com: xcode-select --install)"; exit 1; }
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "dependências instaladas em .venv"

[ -f .env ] && source .env || true

perguntar() {  # nome, texto; mantém o valor atual se Enter vazio
  local atual="${!1:-}" novo
  if [ -n "$atual" ]; then printf "%s [Enter mantém a atual]: " "$2"; else printf "%s: " "$2"; fi
  read -rs novo; echo
  [ -n "$novo" ] && printf -v "$1" '%s' "$novo"
  return 0
}

echo "2/5 Hugging Face (AIDev)"
perguntar HF_TOKEN "Cole o token do Hugging Face (hf_...)"
if python -I - <<PY
import os, sys
from huggingface_hub import HfApi
try:
    HfApi(token="${HF_TOKEN:-}").dataset_info("hao-li/AIDev", revision="7840b6e61a5828461cd96806c52c20194ef57979")
except Exception as e:
    print("   ", type(e).__name__, str(e)[:200]); sys.exit(1)
PY
then ok "token válido e acesso ao AIDev na revisão fixada"
else falha "sem acesso ao AIDev: confira o token e se aceitou os termos em huggingface.co/datasets/hao-li/AIDev"; fi

echo "3/5 Claude Code (classificador de correção, usa o seu plano)"
if ! command -v claude >/dev/null; then
  falha "Claude Code não encontrado: instale com  npm install -g @anthropic-ai/claude-code  e rode  claude  uma vez para fazer login"
else
  resp=$(echo "Responda só: ok" | env -u ANTHROPIC_API_KEY claude -p --model claude-haiku-5-5 --tools "" --strict-mcp-config --no-session-persistence --output-format json 2>/dev/null || true)
  if echo "$resp" | python -c "import sys,json; d=json.load(sys.stdin); sys.exit(1 if d.get('is_error') else 0)" 2>/dev/null; then
    ok "Claude Code logado e respondendo (modelo claude-haiku-5-5)"
  else
    falha "Claude Code não respondeu: abra  claude  no terminal, faça login com a conta do plano e rode este script de novo"
  fi
fi

echo "4/5 GitHub (opcional, recupera PRs integradas por rebase)"
perguntar GITHUB_TOKEN "Cole o token do GitHub (github_pat_...) ou Enter para pular"
if [ -n "${GITHUB_TOKEN:-}" ]; then
  restante=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit | python -c "import sys,json; print(json.load(sys.stdin).get('resources',{}).get('core',{}).get('limit',0))" 2>/dev/null || echo 0)
  if [ "${restante:-0}" -ge 5000 ]; then ok "token válido ($restante consultas/hora)"; else falha "token não aceito pela API"; fi
else
  echo "  - pulado: commits integrados por rebase viram 'commit direto'"
fi

echo "5/5 Gravando pipeline/.env"
umask 077
{
  echo "export HF_TOKEN='${HF_TOKEN:-}'"
  echo "export GITHUB_TOKEN='${GITHUB_TOKEN:-}'"
} > .env
ok ".env gravado (só neste computador; está no .gitignore)"
echo
echo "Próximo passo: bash rodar.sh"
