# Quem conserta o código dos agentes?

**Frequência, autoria e fatores da correção de código gerado por agentes autônomos de IA**

Trabalho Interdisciplinar 6 — Pesquisa em Engenharia de Software (PUC Minas, 2026/2).
Tema da disciplina: *Código gerado por agentes de IA: qualidade e taxa de correção*.

## Grupo
Guilherme Gomes de Brites · Jonathan Sena da Silva · Matheus Ferreira Titton · Murilo Andrade Machado · Pedro Henrique Barbosa Montandon de Araújo · Pedro Luiz Nato Silva

## A pesquisa em uma tela
**Objetivo (GQM):** analisar o código integrado à branch principal por PRs de agentes autônomos de IA, com o propósito de caracterizar sua correção posterior, com respeito a frequência, autoria e fatores associados, do ponto de vista de mantenedores, em repositórios populares do GitHub (AIDev) onde agentes e humanos trabalham juntos.

| Questão | Pergunta | Métrica primária |
|---|---|---|
| **QP1 — Frequência** | O código integrado por agentes é corrigido com mais ou menos frequência que o de PRs conduzidas por humanos, no mesmo repositório? | `fix_rate_w`: linhas da PR corrigidas em até 90 dias ÷ linhas adicionadas |
| **QP2 — Autoria** | Quem corrige o código dos agentes, e isso vai além do que os humanos já fazem no repositório? | `human_fix_excess`: fração corrigida por PRs humanas − fração humana da atividade do repositório |
| **QP3 — Fatores** | Que características da PR (tamanho, complexidade, tipo de tarefa, oportunidade) estão ligadas à correção, e a diferença agente × humano muda com elas? | interação fluxo × log(tamanho) |

**Grupos comparados:** *fluxo autônomo* (FA: Copilot coding agent, Devin e Jules, da tarefa à PR, com conta própria de bot) × *fluxo com humano no loop* (HL: uma pessoa conduz a PR, podendo usar IA). Não é "IA × humano": como o uso de IA por humanos é invisível, comparamos **quem conduz** o trabalho.

**Método:** unidade = PR integrada; `git blame -w -M -C` liga cada mudança posterior à PR de origem; um modelo de linguagem cego ao fluxo classifica a mudança (correção, evolução, refatoração, outro), validado à mão em 80 eventos; modelos com o repositório como agrupamento, Holm nas três hipóteses.

Detalhes em [`docs/01-proposta.md`](docs/01-proposta.md). Visão consolidada (problema, GQM, métricas, pipeline e resultados da rodada Python) em [`docs/03-consolidacao-gqm-resultados.md`](docs/03-consolidacao-gqm-resultados.md).

## Estrutura
| Pasta | Conteúdo |
|---|---|
| [`docs/`](docs) | Proposta atual, desenho do classificador e consolidação GQM + resultados |
| [`docs/material-anterior/`](docs/material-anterior) | Primeira versão do trabalho (metodologia v7.1, sabatina, spike, piloto, resultados Python) e o diagnóstico que levou à nova proposta. Serve de base; não é mais a referência |
| [`pipeline/`](pipeline) | Pipeline de extração e análise (Python + JS/TS); instruções no [README](pipeline/README.md) |
| [`dados/`](dados) | Amostra de repositórios (`amostra.csv`: 24 Python + 56 JS/TS) |
| [`apresentacoes/`](apresentacoes) | Slides de escopo (set.) e de resultados preliminares do piloto (15/10) |

## Situação
- [x] Fase 0 — spike de factibilidade e amostra (13/10)
- [x] Piloto e primeira rodada Python com o desenho anterior (15–18/10)
- [x] Nova proposta com foco em correção e nova pipeline, testada em 6 repositórios Python e 2 TypeScript (19/10)
- [ ] Aprovação da proposta pelo grupo (pré-registro datado)
- [ ] Rodada completa com o AIDev e o classificador por LLM (Python e JS/TS)
- [ ] Validação manual do classificador (80 eventos, kappa)
- [ ] 1ª versão do artigo
- [ ] Artigo final
