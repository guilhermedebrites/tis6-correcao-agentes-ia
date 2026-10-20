#!/usr/bin/env bash
# Executa a pipeline completa com as chaves de pipeline/.env.
# Uso: bash rodar.sh            (Python e depois JS/TS)
#      bash rodar.sh python     (só uma família)
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || { echo "Rode antes: bash configurar.sh"; exit 1; }
source .venv/bin/activate
source .env
mkdir -p out
LOG="out/execucao_$(date +%Y%m%d_%H%M).log"

[ -f data/aidev/REVISION ] || python -m correcao baixar 2>&1 | tee -a "$LOG"
for fam in ${1:-python jsts}; do
  echo "=== $fam ===" | tee -a "$LOG"
  python -m correcao p1 --familia "$fam" 2>&1 | tee -a "$LOG"
  python -m correcao p2 --familia "$fam" -w 3 2>&1 | tee -a "$LOG"
done
python -m correcao classificar --llm 2>&1 | tee -a "$LOG"
python -m correcao analisar 2>&1 | tee -a "$LOG"
python -m correcao validacao-amostra -n 80 2>&1 | tee -a "$LOG"
echo "Relatório: out/resultados/relatorio.md · Planilha de validação: out/validacao_amostra.csv · Log: $LOG"
