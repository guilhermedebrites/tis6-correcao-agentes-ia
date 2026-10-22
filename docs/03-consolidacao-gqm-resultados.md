# Consolidação — problema, GQM, métricas, pipeline e resultados

> **Data:** 22/10/2026 · **Status:** consolidação dos documentos `01-proposta.md`, `02-classificador-correcao.md` e da 1ª rodada Python (21/10/2026).
> **Atenção:** todos os resultados abaixo são **preliminares**. O classificador de correção (LLM) ainda não foi validado contra os 80 eventos rotulados à mão (`pipeline/out/validacao_amostra.csv`). Até lá, nenhum número deve ir para o artigo como conclusão.

---

## 1. Problema de pesquisa

**Título de trabalho:** *"Quem conserta o código dos agentes? Frequência, autoria e fatores da correção de código integrado por agentes autônomos de IA"*.

Agentes de IA (Copilot coding agent, Devin, Jules) já abrem PRs que são integradas à branch principal de repositórios reais. A literatura recente discute se esse código **dura** mais ou menos que o humano, mas quase não pergunta **quem paga a conta** quando ele precisa ser corrigido. Se a correção do código de agente recai sobre os mantenedores humanos, a produtividade do fluxo autônomo esconde um custo transferido para eles.

O estudo compara, **dentro do mesmo repositório**, dois fluxos de trabalho:

| Fluxo | Definição |
|---|---|
| **FA** (fluxo autônomo) | PR aberta e conduzida por Copilot, Devin ou Jules (conta de bot), sem commit humano |
| **HL** (humano no loop) | PR conduzida por um humano, no mesmo repositório e período. Pode ter usado IA (chat, autocompletar): o construto é **quem conduz**, não "IA × humano" |

- **Dataset:** AIDev (`hao-li/AIDev`), revisão fixada `7840b6e`, corte 24/10/2025.
- **Unidade de análise:** PR integrada (diff líquido entre o commit anterior e o posterior ao merge, no 1º pai).
- **Desfecho:** linhas da PR alteradas ou removidas por uma **correção de defeito** em até 90 dias.

---

## 2. GQM

### 2.1 Objetivo (G)
**Analisar** o código integrado à branch principal por PRs de agentes autônomos de IA
**com o propósito de** caracterizar sua correção posterior
**com respeito a** frequência, autoria e fatores associados
**do ponto de vista de** mantenedores de projetos open source
**no contexto de** repositórios populares do GitHub (AIDev) em que o fluxo autônomo convive com o fluxo humano.

### 2.2 Questões (Q) e hipóteses

| Questão | Pergunta | Hipótese confirmatória |
|---|---|---|
| **QP1 — Frequência** | Com que frequência e em quanto tempo o código de PRs FA é corrigido, comparado ao de PRs HL do mesmo repositório? | **H1:** a taxa de correção do código FA difere da do HL (bilateral) |
| **QP2 — Autoria** | Que fração das correções do código FA é feita por humanos, pelo próprio fluxo autônomo ou por outros agentes/bots, e isso difere da atividade normal do repositório? | **H2:** a correção do código FA é feita por humanos **acima** do que a linha de base de atividade humana explica (`human_fix_excess` > 0, unilateral) |
| **QP3 — Fatores** | Quais características da PR estão associadas à correção, e a diferença FA × HL muda com elas? | **H3:** a diferença FA × HL é maior em PRs pequenas (interação `fluxo × log(size_churn)` negativa) |

**Família confirmatória:** H1, H2 e H3, com correção de Holm. Todo o resto é exploratório.

### 2.3 Árvore GQM

```
G: Caracterizar a correção do código integrado por agentes autônomos
│
├── QP1 Frequência ── fix_rate_w (primária) · rework_rate_w · has_fix · tempo até 1ª correção
│                      → H1
├── QP2 Autoria ───── human_fix_excess (primária) · human_fix_share · self_fix_share · origem por condutor
│                      → H2
└── QP3 Fatores ───── interação fluxo × log(size_churn) (primária) · tamanho · churn anterior
                       · complexidade introduzida · tipo de tarefa · novidade
                       → H3
```

---

## 3. Métricas escolhidas (proposta)

### 3.1 Desfechos
| Métrica | Definição | QP | Papel |
|---|---|---|---|
| `fix_rate_w` | linhas da PR alteradas/removidas por eventos de **correção** em até W = 90 dias ÷ linhas adicionadas | QP1 | **Primária (H1)** |
| `rework_rate_w` | o mesmo, para **qualquer** modificação (correção ou evolução) | QP1 | Secundária / sensibilidade |
| `has_fix` | 1 se ao menos uma linha da PR foi corrigida em W | QP1 | Secundária |
| Tempo até a 1ª correção | Kaplan-Meier, Cox | QP1 | Complementar |
| `human_fix_share` | das linhas corrigidas de uma PR, fração corrigida em PRs conduzidas por humanos (HL ou commit direto) | QP2 | Descritiva |
| `self_fix_share` | fração corrigida pelo mesmo fluxo que criou o código (FA→FA, HL→HL) | QP2 | Secundária |
| Linha de base humana | fração das linhas alteradas no repositório, no período, por humanos | QP2 | Controle |
| `human_fix_excess` | `human_fix_share` − linha de base humana do repositório | QP2 | **Primária (H2)** |
| Origem por condutor | linhas corrigidas por humano · agente principal · outro agente · bot | QP2 | Descritiva |

### 3.2 Fatores (QP3) e covariáveis
| Fator | Medida | Uso |
|---|---|---|
| Tamanho | `log(size_churn)`, linhas lógicas adicionadas + removidas | Covariável em todos os modelos; interação com o fluxo = **H3** |
| Oportunidade de correção | `log(1 + churn_anterior)`: alterações nos arquivos da PR nos 90 dias **anteriores** | Covariável e fator |
| Complexidade introduzida | `cc_delta` (Σ variação da complexidade ciclomática nas funções tocadas, Lizard); `cc_depois_max` | Fator |
| Tipo de tarefa | `feat / fix / refactor / docs / test / chore / outro`, pelo título | Covariável |
| Novidade | `frac_arquivo_novo`: fração das linhas adicionadas em arquivos novos | Fator |
| Modo de integração | squash · merge · rebase | Covariável quando houver mais de um |

### 3.3 Classificação de "correção"
Cada **evento** (PR posterior ou commit direto que alterou linhas de uma PR de origem) é classificado por um LLM em `corrige_defeito`, `evolucao`, `refatoracao` ou `outro`; só `corrige_defeito` conta como correção. O classificador é **cego ao fluxo**: recebe título, descrição, rótulos, mensagens de commit e o trecho do diff, mas não sabe quem escreveu o código de origem nem quem fez a mudança. A heurística antiga por palavras-chave é calculada ao lado, como sensibilidade. Detalhes em `02-classificador-correcao.md`.

---

## 4. Pipeline criada e executada (passo a passo)

A pipeline foi escrita do zero (`pipeline/correcao/`) para este desenho. Python e JS/TS usam o mesmo código; a família muda só a lista de arquivos considerados e a regra de comentário. Todos os parâmetros ficam em `correcao/config.py`.

| # | Etapa | O que faz | Módulo | Saída |
|---|---|---|---|---|
| 0 | **Configurar** | `bash configurar.sh`: cria o `.venv`, instala dependências, pede e testa o token do Hugging Face (AIDev), o login do Claude Code e o token do GitHub (opcional). Chaves ficam só em `pipeline/.env`, fora do git | `configurar.sh` | `.venv/`, `.env` |
| 1 | **Baixar o AIDev** | Baixa as tabelas `repository`, `pull_request` e `pr_commits` na revisão fixada `7840b6e` | `aidev.py` (`baixar`) | `data/aidev/` |
| 2 | **P1 — PRs de agentes** | Seleciona as PRs de Copilot/Devin/Jules integradas, por família de linguagem, nos repositórios de `dados/amostra.csv` | `aidev.py` (`p1`) | `out/agent_prs_<familia>.parquet` |
| 3 | **Clone** | Clona cada repositório (snapshot registrado em `status.json`) | `git.py` | `data/clones/` |
| 4 | **E2 — Histórico** | Percorre o 1º pai, identifica cada PR integrada (squash, merge, rebase; rebase recuperado pela API do GitHub quando > 30% dos commits não têm marcação) e classifica o fluxo: FA, HL, `fa_mista`, `fa_provavel`, `agente_fora`, `bot`, `direto`, `fora_periodo` | `historico.py`, `github.py` | `out/repos/<repo>/unidades.csv` |
| 5 | **E3 — Filtros** | Mantém só PRs FA/HL com arquivos de produção, 3 ≤ `size_churn` ≤ 500, abaixo do p99, que não sejam só formatação (AST, em Python) e com linhas adicionadas. Repositório entra se tiver **≥ 5 FA e ≥ 5 HL válidas** | `executar.py` | coluna `motivo_exclusao`, `valida` |
| 6 | **E4 — Medidas da PR** | Tamanho, novidade, complexidade introduzida (Lizard), tipo de tarefa | `metricas.py`, `padroes.py` | colunas em `unidades.csv` |
| 7 | **E5 — Blame** | Para cada evento posterior, `git blame -w -M -C` no estado anterior atribui as linhas alteradas/removidas à PR de origem; conta se ocorre em até 90 dias. Registra quem conduziu o evento (humano, agente principal, outro agente, bot), o churn anterior dos arquivos e a atividade por condutor (linha de base da QP2) | `blame.py` | `eventos.csv`, `eventos_texto.jsonl`, `status.json` |
| 8 | **E5b — Classificação LLM** | Cada evento é classificado uma vez pelo Claude Haiku via `claude -p` (plano do Guilherme, sem ferramentas), com o prompt `prompts/classificador_v1.txt`. Respostas ficam em cache (`data/llm_cache/`), versionado: rodar de novo dá os mesmos rótulos | `classificador.py` | `out/rotulos.csv` |
| 9 | **E6 — Análise** | Calcula os desfechos por PR, roda os modelos de QP1–QP3 e aplica Holm em H1–H3 | `analise.py` | `out/resultados/relatorio.md`, `resultados.json`, `unidades_desfechos.csv`, `status_repos.csv` |
| 10 | **Validação** | Sorteia 80 eventos estratificados para duas pessoas rotularem às cegas; depois mede kappa e precisão/revocação do classificador por fluxo | `validacao.py` | `out/validacao_amostra.csv` |

**Comando único:** `cd pipeline && bash rodar.sh python` executa as etapas 1–10 em sequência (`baixar` → `p1` → `p2` → `classificar --llm` → `analisar` → `validacao-amostra -n 80`).

### 4.1 Execução de 21/10/2026 (família Python)
- Rodada no Mac do Guilherme, com o AIDev na revisão fixada e o classificador pelo Claude Code do plano.
- **24 repositórios Python** na lista de entrada; **23 processados**. `Azure/azure-sdk-for-python` foi abortado (blame lento demais) e fica para a rodada oficial.
- **13 repositórios incluídos** (≥ 5 FA e ≥ 5 HL válidas); 10 ficaram abaixo do mínimo: airbyte, cuda-python, agent-framework, deepmd-kit e opteryx com só 3 FA válidas; foamlib com 4 FA; chaiNNer, QuantEcon e translate com menos de 5 HL; KToolBox sem nenhuma FA válida.
- **150 PRs FA** (91 Copilot, 59 Devin) e **2.387 PRs HL** válidas.
- **1.675 eventos** posteriores classificados pelo LLM, nenhum inválido: 514 `corrige_defeito`, 582 `evolucao`, 444 `refatoracao`, 135 `outro` (a heurística por palavras-chave marcaria 756 como correção).
- 80 eventos sorteados para a validação manual (ainda não rotulados).
- Resultados e cache do LLM versionados no commit `42235f8`.

---

## 5. Métricas efetivamente extraídas pela pipeline

Colunas de `pipeline/out/resultados/unidades_desfechos.csv` (uma linha por PR válida):

| Grupo | Colunas | Correspondência com a proposta |
|---|---|---|
| Identificação | `unit_id`, `repo`, `pr_number`, `fluxo`, `agente`, `quem_conduz`, `modo`, `data`, `titulo` | — |
| Tamanho | `adicionadas`, `removidas`, `size_churn`, `log_size`, `n_arquivos` | Fator tamanho ✓ |
| Complexidade | `cc_delta`, `cc_depois_max` | Fator complexidade ✓ |
| Novidade | `frac_arquivo_novo` | Fator novidade ✓ |
| Tipo de tarefa | `tipo_tarefa` | Covariável ✓ |
| Oportunidade | `churn_anterior`, `log_churn_ant` | Fator oportunidade ✓ |
| IA declarada no HL | `ia_declarada` | Sensibilidade (ameaça) ✓ |
| QP1 | `linhas_retrabalho`, `linhas_fix`, `rework_rate_w`, `fix_rate_w`, `has_fix`, `dias_ate_fix`, `evento_fix`, `dias_ate_retrabalho` | Todas ✓ |
| QP2 | `fix_por_humano`, `fix_por_agente_principal`, `fix_por_outro_agente`, `fix_por_bot`, `human_fix_share`, `self_fix_share`, `base_humana_repo`, `human_fix_excess` | Todas ✓ |
| Filtros | `motivo_exclusao`, `valida`, `so_formatacao`, `erro_parse` | E3 ✓ |

**Diferenças entre o proposto e o que a análise usa hoje:**
- `frac_arquivo_novo` e `cc_depois_max` são extraídas, mas **ainda não entram em nenhum modelo** da QP3.
- O tipo de tarefa entra como **covariável**, não como fator testado; não há interação `fluxo × tipo_tarefa`.
- A validação usa 80 eventos (doc 02), e não os ~200 citados na proposta 01.
- As sensibilidades da proposta (janela de 30/180 dias, só arquivos tocados pelos dois fluxos, sem repositórios com > 30% de commits diretos, HL sem IA declarada, heurística em vez do LLM) **ainda não foram rodadas**.

---

## 6. Como cada métrica responde a cada pergunta

| QP / H | Métrica | Modelo | Como se lê |
|---|---|---|---|
| **QP1 / H1** | `fix_rate_w` | LMM: `fix_rate_w ~ fa + log_size + log_churn_ant + C(tipo_tarefa) (+ C(modo)) + (1 \| repo)` | Coeficiente de `fa` = diferença FA − HL na taxa de correção, ajustada por tamanho, oportunidade e tipo de tarefa, comparando dentro do repositório. ≠ 0 confirma H1 |
| QP1 (confirmação) | média de `fix_rate_w` por repositório e fluxo | Wilcoxon pareado por repositório | Verifica se a diferença aparece repositório a repositório, não só no agregado |
| QP1 (tempo) | `dias_ate_fix`, `evento_fix` | Kaplan-Meier e Cox (com `log_size`, erro agrupado por repositório) | HR > 1: código FA corrigido mais cedo |
| QP1 (exploratório) | `rework_rate_w`, `has_fix` | LMM igual ao de H1 | Separa correção de qualquer modificação |
| **QP2 / H2** | `human_fix_excess` (só PRs FA com alguma correção) | LMM só com intercepto e efeito de repositório; teste unilateral do intercepto > 0 | > 0: humanos corrigem o código de agente **mais** do que sua participação normal no repositório explica. Confirma H2 |
| QP2 (descritivo) | `human_fix_share`, linha de base, `fix_por_*` | Bootstrap por repositório | Quanto da correção do FA é humana e quanto é do próprio agente |
| QP2 (descritivo) | `self_fix_share` | Média | Quanto cada fluxo conserta o próprio código |
| **QP3 / H3** | interação `fa × log_size` | LMM: `fix_rate_w ~ fa * log_size + log_churn_ant + C(tipo_tarefa) + (1 \| repo)` | < 0: a diferença FA − HL cresce quanto menor a PR. Confirma H3 |
| QP3 (exploratório) | `log_size`, `log_churn_ant`, `cc_delta` | LMM de H1 + `cc_delta` | Quais características da PR se associam à correção, independentemente do fluxo |

---

## 7. Resultados da rodada Python de 21/10/2026 (preliminares)

**Amostra:** 13 repositórios · 150 PRs FA · 2.387 PRs HL · 1.675 eventos classificados.
Todos os modelos de efeito misto convergiram (LMM com intercepto por repositório).

### 7.1 QP1 — Frequência
| Medida | FA | HL | Diferença ajustada (FA − HL) |
|---|---|---|---|
| `fix_rate_w` (média) | **3,4%** | **3,1%** | +0,35 p.p. (IC −1,6 a +2,3; **p = 0,73**) |
| `rework_rate_w` (média) | 22,6% | 17,1% | +0,64 p.p. (IC −4,1 a +5,4; p = 0,79) |
| `has_fix` (PRs com alguma correção) | 16,0% | 20,6% | — |
| Sem correção em 90 dias (Kaplan-Meier) | 84,0% | 79,4% | Cox HR 0,98 (IC 0,59–1,63; p = 0,95) |

Wilcoxon por repositório: mediana da diferença −0,2 p.p., FA maior em 5 dos 13 repositórios, p = 0,89.
**H1 não confirmada** (Holm = 1,0): o código FA não é corrigido com frequência nem rapidez diferentes do HL.

### 7.2 QP2 — Autoria
- Só **24 PRs FA** (de 150) tiveram alguma linha corrigida, contra 491 HL.
- Linhas corrigidas do código FA: **117 por humanos** e **15 pelo próprio agente** (nenhuma por outro agente ou bot).
- Fração do código FA corrigida por humanos: **81%** (IC 67%–98%). Linha de base humana nos mesmos repositórios: **97%**.
- `human_fix_excess` = −0,05 (IC −0,26 a +0,16; p bilateral = 0,64; unilateral = 0,68).
- Autocorreção: o FA conserta 19% do próprio código corrigido; o HL, 96%.

**H2 não confirmada** (Holm = 1,0): humanos fazem a maior parte da correção do código de agente, mas **não acima** do que já fazem no repositório. Se algo, o agente corrige o próprio código um pouco mais do que sua participação na atividade sugere. A amostra (24 PRs) é pequena.

### 7.3 QP3 — Fatores
| Termo | Efeito em `fix_rate_w` | IC 95% | p | Leitura |
|---|---|---|---|---|
| **Interação FA × log(tamanho)** (H3) | −0,014 | −0,030 a +0,002 | 0,094 (Holm 0,28) | Sinal na direção prevista, mas não significativo |
| log(tamanho) | −0,008 | −0,012 a −0,004 | < 0,001 | PRs maiores têm **menor** fração de linhas corrigidas |
| log(churn anterior) | +0,008 | +0,002 a +0,013 | 0,004 | Arquivos mais mexidos antes são **mais** corrigidos depois (oportunidade) |
| `cc_delta` | +0,0001 | −0,00003 a +0,0003 | 0,099 | Sem associação clara |

**H3 não confirmada.** Tamanho e churn prévio importam para a correção, mas do mesmo jeito para FA e HL.

### 7.4 Síntese
| Hipótese | Resultado | p bruto | p Holm |
|---|---|---|---|
| H1 — taxa de correção FA ≠ HL | Não confirmada | 0,73 | 1,00 |
| H2 — excesso de correção humana no FA | Não confirmada | 0,68 (unilateral) | 1,00 |
| H3 — diferença maior em PRs pequenas | Não confirmada | 0,094 | 0,28 |

**Leitura preliminar:** nesta amostra Python, o código integrado por agentes autônomos é corrigido com a mesma frequência que o humano, é corrigido por humanos na mesma proporção em que humanos já mexem no repositório, e a correção se explica por tamanho e oportunidade, não pelo fluxo. É um **resultado nulo**, que precisa ser tratado como tal no artigo (inclusive discutindo poder estatístico: só 150 PRs FA e 24 com correção).

### 7.5 Limites destes números
1. **Classificador não validado.** Os 80 eventos de `validacao_amostra.csv` precisam ser rotulados por duas pessoas (kappa ≥ 0,6; precisão ≥ 0,8, parecida em FA e HL). Se o critério falhar, os números mudam.
2. **Só Python.** JS/TS ainda não foi rodado; Azure SDK ficou de fora.
3. **Concentração:** mlflow (33 FA) e crewAI (23 FA) somam 37% das PRs FA.
4. **Sensibilidades pendentes** (seção 5).
5. **Associação, não causa:** agentes recebem tarefas diferentes; tamanho e tipo de tarefa são controlados, mas não eliminam a confusão.

---

## 8. Próximos passos
1. Duas pessoas rotulam `pipeline/out/validacao_amostra.csv` e rodam `python -m correcao validacao-medir` (nunca compartilhar o gabarito oculto).
2. Rodar a família JS/TS (`bash rodar.sh jsts`).
3. Congelar a proposta como pré-registro datado antes de ver os resultados JS/TS.
4. Rodar as sensibilidades e incluir `frac_arquivo_novo` / `cc_depois_max` na QP3, se o grupo mantiver esses fatores.
5. Escrever a 1ª versão do artigo com estes resultados marcados como preliminares.
