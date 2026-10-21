# Pipeline de correção — quem conserta o código dos agentes?

Implementa a proposta [`docs/01-proposta.md`](../docs/01-proposta.md) e o classificador de [`docs/02-classificador-correcao.md`](../docs/02-classificador-correcao.md).
Python e JS/TS usam o mesmo código: a família muda só a lista de arquivos considerados e a regra de comentário.

## O que a pipeline faz
| Etapa | Módulo | Saída |
|---|---|---|
| P1 — PRs de agentes do AIDev (revisão fixada, D5) | `aidev.py` | `out/agent_prs_<familia>.parquet` |
| E2 — PRs integradas no 1º pai (squash, merge, rebase) e fluxo de cada uma (FA, HL, bot…) | `historico.py` | `out/repos/<repo>/unidades.csv` |
| E3 — filtros: arquivos de produção, 3 ≤ tamanho ≤ 500, p99, só formatação, sem linhas adicionadas | `executar.py`, `metricas.py` | coluna `motivo_exclusao` |
| E4 — tamanho, novidade e complexidade introduzida (Lizard, nas duas linguagens) | `metricas.py` | colunas em `unidades.csv` |
| E5 — `git blame -w -M -C`: que PRs posteriores alteraram as linhas de cada PR em até 90 dias, e quem as conduziu; churn anterior dos arquivos; atividade por condutor (linha de base da QP2) | `blame.py` | `eventos.csv`, `eventos_texto.jsonl`, `status.json` |
| E5b — cada evento vira `corrige_defeito / evolucao / refatoracao / outro` (LLM cego ao fluxo, com cache) e a heurística antiga ao lado | `classificador.py` | `out/rotulos.csv` |
| E6 — QP1 (frequência), QP2 (autoria com linha de base), QP3 (fatores), Holm nas três hipóteses | `analise.py` | `out/resultados/relatorio.md`, `resultados.json`, `unidades_desfechos.csv` |
| Validação — planilha para duas pessoas, kappa, precisão por fluxo | `validacao.py` | `out/validacao_*.csv/json` |

Parâmetros em `correcao/config.py` e expressões em `correcao/padroes.py`; tudo vai para `out/manifesto.json`.

## Como rodar (macOS ou Linux)

### 1. Obter as chaves (uma vez)
| Chave | Para quê | Como obter |
|---|---|---|
| **Hugging Face** (`hf_…`) | Baixar o AIDev | 1) Entre em [huggingface.co/datasets/hao-li/AIDev](https://huggingface.co/datasets/hao-li/AIDev) logado e, se aparecer, aceite os termos de acesso. 2) Em [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → *Create new token* → tipo **Read** → copie |
| **Claude Code** (login do plano) | Classificador de correção (LLM) | Instale com `npm install -g @anthropic-ai/claude-code`, rode `claude` uma vez no terminal e faça login com a conta do plano. A pipeline chama `claude -p` sem ferramentas e consome o limite do plano, sem chave paga. Alternativa: `--meio api` com `ANTHROPIC_API_KEY` |
| **GitHub** (`github_pat_…`, opcional) | Recuperar PRs integradas por rebase | [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) → *Repository access: Public repositories (read-only)* → sem permissões extras → *Generate* → copie |

**Não cole as chaves no chat, em issues nem em arquivos do repositório.** O script abaixo pergunta os tokens sem mostrar na tela e grava só em `pipeline/.env`, que está no `.gitignore`.

### 2. Configurar e testar as chaves
```bash
cd pipeline
bash configurar.sh      # cria o .venv, instala as dependências, pede e testa cada chave
```
Cada chave aparece com ✓ (funcionou) ou ✗ (com o motivo). Pode rodar de novo quantas vezes quiser; Enter vazio mantém a chave já gravada.

### 3. Rodar
```bash
bash rodar.sh           # baixa o AIDev (1x), roda Python e JS/TS, classifica, analisa e gera a planilha de validação
bash rodar.sh python    # só Python (mais rápido, bom para a primeira vez)
```
Saídas: `out/resultados/relatorio.md`, `out/validacao_amostra.csv` e o log em `out/execucao_*.log`.

### Comandos individuais
```bash
source .venv/bin/activate && source .env
python -m correcao baixar                               # 1x: repository, pull_request, pr_commits
python -m correcao tudo --familia python --llm -w 3     # P1 → P2 → classificação → análise
python -m correcao analisar                             # refaz só a análise (segundos)
```
- A lista de repositórios vem de `../dados/amostra.csv` (status `incluido` e `incluir_confirmar_hl`).
- Os clones ficam em `data/clones/` (vários GB com a amostra inteira). Repositórios gigantes (ex.: `microsoft/vscode`) demoram; dá para rodar uma lista explícita com `--repos dono/nome …`.
- As respostas do LLM ficam em `data/llm_cache/`: rodar de novo não muda os rótulos nem custa nada.

## Validação do classificador
```bash
python -m correcao validacao-amostra -n 80      # gera out/validacao_amostra.csv
# duas pessoas preenchem rotulo_a e rotulo_b (corrige_defeito, evolucao, refatoracao, outro) sem se consultar;
# onde discordarem, preenchem consenso
python -m correcao validacao-medir out/validacao_amostra.csv
```
Critério da proposta: kappa entre pessoas ≥ 0,6 e precisão do classificador ≥ 0,8, **com precisão parecida para eventos que corrigem código FA e HL**.

## Teste sem o AIDev
`--fonte-fa git` identifica o FA pela assinatura do agente no histórico (autor `copilot-swe-agent[bot]`, `Copilot`, `devin-ai-integration[bot]`… ou branch `copilot/`, `devin/`). Serve para testar a pipeline; a análise oficial usa o AIDev (pureza pelos commits da PR e PRs de outros agentes retiradas do HL).

```bash
python -m correcao p2 --repos reflex-dev/reflex-web --fonte-fa git -w 1
python -m pytest -q tests
```

## Diferenças em relação à pipeline anterior (`fa_hl`)
- O desfecho principal é a **taxa de correção** (`fix_rate_w`), não o retrabalho; o retrabalho fica como exploratório.
- **Sem** o filtro "≥ 1 função tocada": código fora de função também pode ser corrigido.
- Complexidade pelo **Lizard nas duas linguagens** (antes, Radon em Python); MI, Halstead e métricas de documentação saíram.
- Verificação de "só formatação" por AST só em Python; em JS/TS não há esse filtro.
- Origem de cada evento registrada por **quem conduziu** (`humano`, `agente_principal`, `outro_agente`, `bot`), com a linha de base de atividade do repositório.
- Modelos: LMM com intercepto por repositório; se ficar singular (poucos repositórios), cai para OLS com erro agrupado por repositório, e o relatório diz qual foi usado.
