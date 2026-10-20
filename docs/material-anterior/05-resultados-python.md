# Primeira expedição — resultados experimentais (repositórios Python)

> **Caráter deste documento:** resultados **experimentais e parciais** da primeira expedição da pesquisa. Ela cobre só a subamostra Python (12 repositórios analisados) e **não representa o todo da pesquisa**: JS/TS (D18) ainda não foi medido. Nenhuma conclusão aqui deve ser lida como resultado final do estudo.
> **Versão:** v2 — 18/10/2026. Substitui a v1 do mesmo dia; os números não mudaram, mas o Holm passou a seguir a D21 e a documentação dos parâmetros foi completada.
> **Base:** `tisl_pipeline/fa_hl_pipeline/fa_hl/out`, execução de 18/10/2026 (18:19–19:00 UTC). Metodologia v7.1, decisões D0–D21.
> **Convenções:**
> - **[pós-hoc]** marca checagens feitas fora da pipeline, sobre os CSVs de `out/diag`, com efeito fixo por repositório e erro-padrão agrupado. É uma aproximação do LMM, usada só para robustez.
> - **[exploratório]** marca resultados que geram hipóteses, mas não sustentam conclusões.
>
> **Para agentes de IA:**
> - Não generalize estes resultados para JS/TS nem para "agentes de IA em geral".
> - Não altere parâmetros sem decisão do grupo. Cite o ID (Dn, R-Pn, V2-n) ao propor mudanças.

---

## 1. O que esta expedição pergunta
A pergunta é se, **no mesmo repositório**, PRs do **fluxo autônomo (FA)** diferem das PRs do **fluxo com humano no loop (HL)**. No FA, um agente de IA vai da tarefa à PR com conta própria de bot. No HL, um humano conduz a PR, podendo usar IA como assistente. As diferenças são medidas em quatro perguntas:

| QP | Pergunta | Métrica primária (R-P5) |
|---|---|---|
| Q1 | Complexidade introduzida | `cc_delta_per_size`: variação da complexidade ciclomática nas funções tocadas, por linha lógica alterada |
| Q2 | Manutenibilidade | `mi_delta_mean`: variação média do Maintainability Index nos arquivos modificados |
| Q3 | Estrutura e tamanho | `size_churn` (linhas lógicas adicionadas + removidas) e `lloc_delta` (crescimento líquido) |
| Q4 | Correção e retrabalho (central) | `rework_rate_w`: fração das linhas adicionadas pela PR que foram alteradas ou removidas em até 90 dias; mais Cox e RMST |

Toda a linguagem é **associativa, não causal** (§11 da metodologia).

---

## 2. Configuração da execução
| Item | Valor |
|---|---|
| Dataset | AIDev-pop (`hao-li/AIDev`), revisão fixada `7840b6e61a5828461cd96806c52c20194ef57979` (D5) |
| Corte do AIDev | 24/10/2025 23:59:59 UTC. Nenhuma PR depois disso é classificada (D7) |
| Linguagem | Python (D18; JS/TS pendente) |
| Lista de entrada | 24 repositórios Python da §14 (`docs/amostra.csv`: 21 `incluido` + 3 `incluir_confirmar_hl`) |
| Clones | Branch padrão, histórico de primeiro pai, snapshot de 18/10/2026; SHA de cada repositório em `out/p2/manifest.json` |
| Ferramentas | Python 3.14.3, Radon 6.0.1, pandas 3.0.6, statsmodels, git 2.51 (Windows 11) |
| API do GitHub | Com `GITHUB_TOKEN`; ~3,2 mil consultas, com cache em `data/github_cache/` |
| Tempo | ~41 min para 20 repositórios (P2), com 3 processos em paralelo |
| Testes automatizados | 14/14 na execução. Depois dela foi acrescentado um teste da D21, que é verificado ao rodar `rodar_e6.bat` |
| Semente | 42 (bootstrap dos IC) |

---

## 3. Parâmetros em vigor para a extração das PRs
Os valores estão em `pipeline/config.py` e `pipeline/patterns.py` e são gravados no manifesto de cada execução.

### 3.1 O que é uma PR FA (fluxo autônomo)
Uma PR só é FA se atender a **todas** as condições abaixo.

| Critério | Regra | Decisão |
|---|---|---|
| Agente | Coluna `agent` do AIDev casa com `copilot`, `devin` ou `jules` (regex, sem diferenciar maiúsculas). Neste recorte só aparecem Copilot e Devin: Jules não tem PRs nos repositórios Python da amostra | D15, D19 |
| Integrada | `merged_at` preenchido e ≤ corte | D7 |
| Pura | **Todos** os commits da PR no `pr_commits` do AIDev são do agente (autor casa com `copilot`, `devin`, `jules` ou `cursor`). Merges de sincronização (`Merge branch/remote-tracking branch/pull request …`) e bots neutros (`github-actions`, `autofix-ci`, `pre-commit-ci`) são ignorados. Um único commit humano torna a PR **`fa_mista`**, que fica fora da análise | D1, D15 |
| Elegível (P1) | ≥ 3 linhas adicionadas em arquivos `.py` de produção (§3.4), contadas **sem** os merges de sincronização | E1 |
| Na branch padrão | O commit integrado precisa ser encontrado no histórico de primeiro pai (§3.3) | D14 |
| Consistência | Contenção ≥ 0,8: pelo menos 80% dos arquivos considerados da unidade aparecem entre os arquivos da PR no `pr_commit_details` | R-P1 |

Período: toda PR FA integrada até o corte. O AIDev só cobre PRs de agentes a partir do fim de 2024.

### 3.2 O que é uma PR HL (humano no loop)
- **Definição:** PR integrada na branch padrão que **não** está nas tabelas de agentes do AIDev, **não** é de bot e **não** tem assinatura de agente.
- **Bot:** todos os autores dos commits casam com `[bot]`, `dependabot`, `renovate`, `pre-commit-ci`, `github-actions` etc., ou a branch tem prefixo de bot.
- **Assinatura de agente:** `copilot-swe-agent`, `devin-ai-integration`, `google-labs-jules`, `cursoragent`, `chatgpt-codex-connector` ou `claude[bot]` no autor, ou branch `copilot/`, `devin/`, `jules/`, `codex/` ou `cursor/`.
- **Janela concorrente (D20):** só entram PRs HL integradas entre o 1º merge FA do repositório e o corte, com folga de 1 h.
- **IA declarada:** PRs HL com trailer de IA (`Co-authored-by` com Claude, Copilot, Cursor etc., ou "Generated with…") **continuam no HL** e são marcadas `ai_assist_declared`. Neste recorte são 141 de 2.500 (5,6%).

### 3.3 Unidade de análise e estados antes/depois (D14)
- **Unidade:** a PR integrada, medida pelo diff líquido que trouxe à branch padrão. Os estados antes (B) e depois (A) dependem do modo de integração:

| Modo | Como é reconhecido | B → A |
|---|---|---|
| Squash | Commit com 1 pai e assunto terminando em `(#N)` | `S^1` → `S` |
| Merge | Commit com 2 pais e assunto `Merge pull request #N from …` | `M^1` → `M` |
| Rebase | Bloco contíguo de commits lineares da PR #N | pai do 1º → último |

- **Rebase FA:** a PR é ligada ao bloco pelos commits do AIDev, por SHA ou pela mensagem, com ±3 dias do merge.
- **Rebase HL:** a PR é ligada pela API do GitHub, só em repositórios com > 30% de eventos sem marcação de PR (R-P3).
- **O resto vira "commit direto":** fica fora da análise, mas conta como **origem** de retrabalho em Q4.
- **Fora da análise principal:**
  - `FA_provavel` (Codex, Cursor, Claude Code; D15);
  - `fa_mista`;
  - `outro_agente` e `agente_fora_do_aidev`;
  - bots;
  - PRs com o mesmo número repetido no histórico.

### 3.4 Arquivos considerados
São considerados arquivos `.py` de **produção**. Ficam fora:

| Categoria | Padrões excluídos |
|---|---|
| Testes | `test/`, `tests/`, `testing/`, `spec/`, `test_*.py`, `*_test.py`, `conftest.py` |
| Migrações | `migrations/`, `alembic/versions/` |
| Vendorizado e build | `vendor/`, `third_party/`, `externals/`, `node_modules/`, `site-packages/`, `.venv/`, `build/`, `dist/` |
| Gerados | `*_pb2.py`, `generated/`, `*_generated.py` |
| Configuração | `setup.py`, `noxfile.py`, `docs/conf.py` |

**Proporção de Python no repositório:** o parâmetro `min_lang_ratio = 0,60` (Tier B) existe na configuração, mas **não é aplicado como filtro nesta versão**: a proporção só é registrada (`lang_ratio` em `repo_status.csv`). Por isso `mlflow/mlflow`, com 44% de Python, está na análise. Como cada repositório é comparado consigo mesmo e só arquivos `.py` são medidos, isso não enviesa o contraste FA × HL, mas é uma divergência entre configuração e implementação, a resolver pelo grupo (§5.2).

### 3.5 Filtros de unidade (E3), na ordem em que são aplicados
| # | Filtro | Regra |
|---|---|---|
| 1 | Arquivo considerado | A PR toca ao menos 1 arquivo considerado |
| 2 | Consistência FA | Contenção ≥ 0,8 (§3.1) |
| 3 | Parse | Arquivos que o `ast` do Python não consegue ler saem da unidade. Se nenhum sobra, a unidade sai |
| 4 | Reformatação | Sai a unidade cujos arquivos têm a mesma AST antes e depois (só formatação ou comentários) |
| 5 | Funções | Ao menos 1 função modificada ou nova |
| 6 | Tamanho | 3 ≤ `size_churn` ≤ 500 linhas lógicas, que são as linhas sem as vazias e sem as só de comentário |
| 7 | p99 | Sai a unidade acima do percentil 99 de `size_churn` do repositório (método `higher`) |

### 3.6 Mínimos por repositório
| Etapa | Regra | Decisão |
|---|---|---|
| P1 | ≥ 5 PRs FA elegíveis | D17 |
| P2 e E6 | ≥ 5 FA **e** ≥ 5 HL **válidas**, em todas as análises | D17-bis |

### 3.7 Métricas
- **Q1–Q3:** Radon, calculadas sobre as funções tocadas em B e A (Δ = A − B). Funções novas têm B = 0; o MI é calculado por arquivo. Lista completa na §E4 da metodologia.
- **Q4:**
  - Para cada evento posterior que altera ou remove linhas em arquivos considerados, roda `git blame -w -M -C` no estado anterior ao evento, ao estilo SZZ.
  - A linha conta como retrabalho da unidade de origem se o evento cai em até W = 90 dias do merge.
  - Numerador e denominador usam as mesmas linhas lógicas.
  - O subconjunto ***fix*** é o retrabalho vindo de eventos com título `fix:` ou palavras como *fix, bug, error, crash, regression, broken, wrong*.
- **Tipo de tarefa (D11-lite):** prefixo de *conventional commits* no título; se não houver, palavras-chave; senão, "outro".

### 3.8 Análise estatística (E6)
| Componente | Especificação |
|---|---|
| **Principal**: modelos por unidade | LMM `métrica ~ fluxo + log(size_churn) + modo + tipo_tarefa + (1 \| repo)`. Q3 sem `log(size_churn)` (R-P4). Binárias: GEE logística agrupada por repositório |
| Tempo até retrabalho | Kaplan-Meier, RMST até 90 dias (IC por bootstrap de repositórios) e Cox com variância robusta por repositório |
| Confirmação | Wilcoxon pareado sobre as medianas FA × HL de cada repositório, com Cliff's delta e IC bootstrap |
| Correção múltipla | Holm em duas famílias (D21): confirmatória = 5 primárias; exploratória = demais métricas, por QP (§7) |

---

## 4. Funil

### 4.1 Repositórios
| Etapa | Repositórios | PRs FA |
|---|---|---|
| Lista de entrada (§14) | 24 | 1.873 do FA principal no AIDev |
| Integradas até o corte | 24 | 1.007 |
| Puras | 24 | 695 |
| Elegíveis | 24 | 226 |
| **P1:** ≥ 5 FA elegíveis | **20** | 212 |
| **P2:** ≥ 5 FA e ≥ 5 HL válidas | **12** | **138 FA × 2.500 HL** |

Repositórios que saíram, e por quê:
- **P1, < 5 FA elegíveis:** `microsoft/agent-framework`, `mabel-dev/opteryx`, `NVIDIA/cuda-python` e `airbytehq/airbyte`. As linhas dos merges de sincronização inflavam a contagem do spike.
- **P2, < 5 FA válidas:** `gerlero/foamlib` (4), `deepmodeling/deepmd-kit` (3), `xtekky/gpt4free` (3), `vlm-run/vlmrun-hub` (1) e `Ljzd-PRO/KToolBox` (0: 10 das suas PRs FA elegíveis não foram encontradas no histórico, com 87% de eventos sem marcação de PR).
- **P2, < 5 HL válidas:** `QuantEcon/QuantEcon.py` (3), `chaiNNer-org/chaiNNer` (4; o 1º merge FA foi 5 dias antes do corte) e `translate/translate` (0).

### 4.2 Destino das 212 PRs FA elegíveis dos 20 repositórios
| Destino | PRs |
|---|---|
| **Válida** | **160 (75%)** |
| Nenhuma função tocada | 20 |
| Não encontrada no histórico (KToolBox 10, crewAI 2, foamlib 1, chaiNNer 1) | 14 |
| Nenhum arquivo considerado | 9 |
| `size_churn` > 500 | 5 |
| `size_churn` < 3 | 4 |
| Inconsistente (contenção < 0,8) | **0** |

- **Vazamento entre critérios:** outras 11 PRs FA que não eram elegíveis em P1 (< 3 linhas adicionadas) viraram unidades válidas, porque a P2 conta também remoções. É o mesmo critério do HL, logo coerente. Excluí-las não muda Q3 (§6.1).
- **Total:** 171 FA válidas, das quais 138 estão em repositórios que passam no mínimo de 5 + 5.

### 4.3 Unidades por repositório analisado
| Repositório | Agente | FA | HL | Modo principal | Eventos sem marcação de PR |
|---|---|---|---|---|---|
| mlflow/mlflow | Copilot | 29 | 479 | squash | 0% |
| crewAIInc/crewAI | Devin | 22 | 220 | squash | 14% |
| reflex-dev/reflex-web | Devin | 18 | 109 | squash | 0% |
| microsoft/lisa | Copilot | 13 | 131 | squash + rebase | 62% (API) |
| jeroenterheerdt/HAsmartirrigation | Copilot | 12 | 7 | merge | 51% (API) |
| NewFuture/DDNS | Copilot | 8 | 6 | squash | 13% |
| Azure/azure-sdk-for-python | Copilot | 7 | 314 | squash | 0% |
| marimo-team/marimo | Copilot + Devin | 7 | 841 | squash | 7% |
| microsoft/fabric-cicd | Copilot | 7 | 25 | squash | 0% |
| AgentOps-AI/agentops | Devin | 5 | 18 | squash | 0% |
| BerriAI/litellm | Copilot | 5 | 201 | squash | 50% (API) |
| polarsource/polar | Copilot | 5 | 149 | squash + rebase | 72% (API) |
| **Total** | Copilot 87 · Devin 51 | **138** | **2.500** | 122 squash · 12 merge · 4 rebase (FA) | — |

---

## 5. O que é válido no processo
A tabela separa o que esta expedição **confirmou com evidência** do que **ainda não foi validado**.

### 5.1 Confirmado
| Aspecto | Evidência |
|---|---|
| Identificação do FA | 100% das PRs Copilot e Devin no AIDev têm como autor a conta de bot (`Copilot`, `devin-ai-integration[bot]`) |
| Pareamento PR ↔ commit integrado | Nas 138 FA, a data no git e o `merged_at` do AIDev diferem no máximo 8 minutos; nenhuma passa de 3 dias (V2-2 encerrada) |
| Consistência (contenção) | 0 exclusões; a v1, com Jaccard, perdia ~40% das FA elegíveis |
| Rendimento do FA | 75% das elegíveis viram unidades válidas (47% na v1). A projeção do doc 04 (§4.1) previa 12 repositórios Python, e foram 12 |
| Rebase | API acionada em 6 repositórios; em lisa e polar, ~1.140 PRs HL rebaseadas recuperadas |
| Observação de Q4 | Todas as unidades têm os 90 dias completos até o snapshot, sem censura |
| Reprodutibilidade | SHAs fixos por repositório, revisão do AIDev, parâmetros e versões no manifesto; semente fixa; testes automatizados |
| Custo | ~41 min para 20 repositórios; a E6 sozinha leva segundos |

### 5.2 Ainda não validado
| Aspecto | Risco | Efeito provável |
|---|---|---|
| Tipo de tarefa (D11-lite) | A heurística pelo título nunca foi conferida à mão (V2-4) | Controle imperfeito do confundidor tarefa |
| Subconjunto *fix* | É inferido por palavras no título | Q4-*fix* com ruído |
| HL "contaminado" por IA não declarada | Só 5,6% declaram IA; o uso real deve ser maior | Aproxima FA e HL, puxando o resultado para "sem diferença" |
| Agente × repositório | O Devin aparece em só 4 repositórios; mlflow, crewAI e reflex-web têm 50% das FA | Não dá para separar efeito do agente e do projeto |
| Primárias escolhidas após o piloto | O piloto v1 (crewAI, lisa) faz parte desta amostra | O pré-registro não é pleno (ressalva da D21) |
| Atribuição de origem em repositórios com push direto | Em HAsmartirrigation, o mantenedor commita direto na `main` | Infla a origem "commit direto" em Q4 (§6.4) |
| `min_lang_ratio` não aplicado | O parâmetro existe, mas a pipeline só registra a proporção (§3.4) | Baixo para o contraste dentro do repositório; o grupo precisa decidir se aplica (mlflow sairia) ou se remove o parâmetro |
| Python 3.14 | Os testes passaram, mas o plano era 3.13 | Baixo; a versão está registrada |

---

## 6. Resultados parciais
Efeito = FA − HL. "Holm" é o p ajustado na família confirmatória (D21, §7).

| QP | Métrica | Efeito FA | IC 95% | p | **p Holm** | Wilcoxon por repositório (12): p · p Holm · Cliff δ | Leitura |
|---|---|---|---|---|---|---|---|
| Q1 | `cc_delta_per_size` | +0,021 | −0,002 a 0,044 | 0,073 | 0,29 | 0,76 · 1 · +0,08 | sem diferença detectável |
| Q2 | `mi_delta_mean` | −0,22 | −0,76 a 0,32 | 0,42 | 0,84 | 0,91 · 1 · +0,30 | sem diferença detectável |
| **Q3** | **`size_churn`** | **−30 linhas** | **−46 a −14** | **0,0003** | **0,0017** | 0,025 · 0,13 · **−0,60** | **PRs FA menores** |
| Q3 | `lloc_delta` | −2,4 | −9,1 a 4,4 | 0,49 | 0,84 | 0,98 · 1 · −0,15 | sem diferença detectável |
| Q4 | `rework_rate_w` | +0,040 | −0,010 a 0,091 | 0,12 | 0,35 | 0,90 · 1 · −0,08 | sem diferença detectável |

Estimativas complementares de Q4, apresentadas com IC e fora do Holm:

| Estimativa | FA | HL | Diferença / razão |
|---|---|---|---|
| Sem retrabalho em 90 dias (Kaplan-Meier) | 0,48 | 0,44 | — |
| Sem *fix* em 90 dias (Kaplan-Meier) | 0,80 | 0,78 | — |
| RMST, dias sem retrabalho (de 90) | 53,4 | 51,4 | +2,0 (IC −10,9 a 13,0) |
| Cox, retrabalho | — | — | HR 1,17 (IC 0,80–1,71; p 0,42) |
| Cox, *fix* | — | — | HR 1,01 (IC 0,70–1,46; p 0,95) |

### 6.1 Q3 — PRs FA são menores (o resultado mais firme da expedição)
- **Tamanho:** mediana de 20 linhas lógicas no FA contra 36 no HL; o modelo dá −30 linhas.
- **Robustez [pós-hoc]:**
  - removendo um repositório por vez, o efeito fica entre −29 e −40 linhas, com p < 0,04 nas 12 rodadas;
  - sem as 11 FA não elegíveis em P1, o efeito é −30,7 (p 0,013);
  - em 11 dos 12 repositórios a mediana FA é menor (a exceção é HAsmartirrigation);
  - por agente, Copilot −41 (p 0,01) e Devin −20 (p 0,23).
- **No nível de repositório:** δ de Cliff −0,60 (efeito grande), mas p Holm = 0,13. Com 12 pares, o Wilcoxon tem pouco poder; é a confirmação, não a análise principal.
- **`lloc_delta` sem diferença:** as PRs FA fazem o código crescer tanto quanto as HL, mas mexem em menos linhas. Ou seja, **removem ou reescrevem menos código existente**.
- **Leitura cautelosa:** o agente pode estar recebendo tarefas menores (seleção de tarefa). O tipo de tarefa está no modelo, mas não foi validado.

### 6.2 Q1 — sem diferença detectável na primária
- A primária `cc_delta_per_size` tem p 0,07 (bruto) e 0,29 (Holm); a checagem com efeito fixo dá p 0,36.
- **Sinal [exploratório] — Halstead:** com ajuste por log(tamanho), as PRs FA aumentam mais o vocabulário, volume e dificuldade de Halstead:

| Medida (Halstead) | Efeito FA | p Holm na família exploratória Q1 |
|---|---|---|
| Vocabulário | +3,7 | 0,006 |
| Volume | +24,6 | 0,011 |
| Dificuldade | +0,62 | 0,010 |
| Vocabulário por linha | — | 0,043 |

  - O sinal **não** aparece no Wilcoxon por repositório (todos os p ≥ 0,37).
  - Pode refletir ajuste incompleto por tamanho (as PRs FA são menores) ou uma diferença real de estilo. É uma hipótese para a próxima expedição, não um resultado.

### 6.3 Q2 — sem diferença detectável
134 das 138 FA têm MI calculável; nenhuma métrica de Q2 difere.

### 6.4 Q4 — inconclusivo (não "equivalente")
- **O sinal do piloto não se manteve:** com 18 FA, o HR era 0,56 e o código FA parecia sobreviver mais. Com 138 FA, o HR é 1,17.
- **Não dá para afirmar igualdade:** o IC do HR (0,80–1,71) admite desde ~20% menos até ~70% mais risco de retrabalho no FA. A amostra não tem poder para fechar Q4.
- **Origem do retrabalho [exploratório]** (linhas retrabalhadas em 90 dias):

| Código de origem | Por PRs HL | Por commit direto | Pelo próprio FA | FA-provável/outros |
|---|---|---|---|---|
| FA (1.335 linhas) | 56% | 35% | 6% | 4% |
| HL (21.420 linhas) | 93% | 3% | 1% | 3% |

  - O código FA é corrigido quase sempre por humanos e raramente pelo próprio agente (D13, "custo humano escondido").
  - Os 35% de commit direto vêm quase todos de HAsmartirrigation, com 425 das 461 linhas.
- **PRs pequenas [exploratório]:** nas PRs de até 10 linhas, a taxa média de retrabalho é 0,36 no FA contra 0,19 no HL (41 × 546 unidades). Nas faixas maiores, as taxas são próximas.

### 6.5 Resumo
| Pode ser dito (com as ressalvas da §5.2) | Não pode ser dito |
|---|---|
| Nos 12 repositórios Python analisados, as PRs integradas de Copilot e Devin são menores que as humanas do mesmo período e repositório, sobretudo porque removem e reescrevem menos código | Que o código de agentes é igual, melhor ou pior em complexidade, manutenibilidade ou retrabalho |
| Não houve diferença detectável em complexidade, MI ou retrabalho | Qualquer generalização para JS/TS, para outros agentes ou para "IA" |
| O código FA retrabalhado é corrigido principalmente por humanos | Relação causal (o agente "causa" PRs menores) |

---

## 7. Correção de Holm (D21)

### 7.1 O problema que ela resolve
- **O que é o p:** a chance de ver uma diferença pelo menos tão grande quanto a observada **se, na verdade, não houvesse diferença**. Com o limite usual de 0,05, aceita-se errar (o "falso positivo") em 5% dos testes em que não há efeito real.
- **O problema de muitos testes:** a chance de **pelo menos um** falso positivo cresce com o número de testes. Com testes independentes e nenhum efeito real:
  - 5 testes → 1 − 0,95⁵ ≈ **23%**;
  - 39 testes (todas as métricas da E6) → ≈ **86%**.
- **Consequência:** sem correção, quase certamente alguma métrica "daria significativa" por acaso.

### 7.2 O que é o Holm
É um procedimento que garante que a chance de **qualquer** falso positivo dentro de uma família de testes fique ≤ 5%. Ele é menos conservador que o Bonferroni (que multiplica todos os p pelo número de testes).
1. Ordenar os *m* valores-p do menor para o maior.
2. Multiplicar o 1º por *m*, o 2º por *m* − 1, …, o último por 1.
3. Forçar a sequência a não diminuir (cada p ajustado é no mínimo o anterior) e limitar a 1.
4. É significativo o que ficar < 0,05.

Exemplo real, com as 5 primárias dos modelos:

| Ordem | Métrica | p bruto | × | Ajustado | Final |
|---|---|---|---|---|---|
| 1 | `size_churn` | 0,00034 | 5 | 0,0017 | **0,0017** |
| 2 | `cc_delta_per_size` | 0,0727 | 4 | 0,291 | 0,29 |
| 3 | `rework_rate_w` | 0,118 | 3 | 0,354 | 0,35 |
| 4 | `mi_delta_mean` | 0,422 | 2 | 0,844 | 0,84 |
| 5 | `lloc_delta` | 0,493 | 1 | 0,493 | 0,84 (não pode ser menor que o anterior) |

### 7.3 O que mudou
- **Antes (v1 e v2 até 18/10):** Holm dentro de cada QP, com **todas** as métricas da QP, primárias e exploratórias (12 na Q1, 3 na Q2, 17 na Q3 e 7 na Q4). Isso tinha dois defeitos:
  - **Penalizava as primárias pelas exploratórias:** o `size_churn` era multiplicado por 17 por causa de métricas sobre as quais não fazemos afirmação nenhuma.
  - **Não controlava o erro entre QPs:** quatro famílias separadas, cada uma a 5%, deixam ~19% de chance de algum falso positivo entre as QPs.
- **Agora (D21):** duas famílias, aplicadas separadamente nos modelos e no Wilcoxon.
  - **Confirmatória:** as 5 primárias das quatro QPs juntas. Só ela sustenta conclusões.
  - **Exploratória:** as demais métricas, por QP, marcadas como exploratórias (coluna `familia_holm` nos CSVs).
  - Cox e RMST ficam fora da família, como estimativas complementares de Q4 com IC. Incluir o Cox, com p = 0,42, não mudaria nada.

### 7.4 Impacto nos números
| Métrica primária | Modelos: Holm antigo → novo | Wilcoxon: Holm antigo → novo |
|---|---|---|
| `cc_delta_per_size` | 0,36 → 0,29 | 1 → 1 |
| `mi_delta_mean` | 1 → 0,84 | 1 → 1 |
| `size_churn` | 0,0058 → **0,0017** | 0,43 → 0,13 |
| `lloc_delta` | 1 → 0,84 | 1 → 1 |
| `rework_rate_w` | 0,79 → 0,35 | 1 → 1 |

- **Nenhuma conclusão muda:** só o `size_churn` é significativo, antes e depois. As exploratórias também quase não mudam (ex.: Halstead vocabulário 0,0065 → 0,0059).
- **O ganho é de coerência, não de resultado:** o p das primárias passa a depender só das hipóteses que testamos de fato.
- **Ressalva:** as primárias foram fixadas depois do piloto v1, que usou dois repositórios desta amostra. A família confirmatória é "quase pré-registrada". Na próxima expedição (JS/TS), as primárias já estarão fixadas antes dos dados.

---

## 8. Limitações desta expedição
1. **Amostra pequena e concentrada:** 12 repositórios, 138 FA, dois agentes, metade das FA em três projetos.
2. **Só Python.** Os resultados podem não valer para TS, onde está a maior parte da amostra planejada.
3. **Poder insuficiente para Q4,** a pergunta central.
4. **Confundidores parcialmente controlados:** tamanho e tipo de tarefa (heurística não validada) e uso de IA não declarado no HL.
5. **Validade de construto do retrabalho:** linhas alteradas em até 90 dias incluem evolução legítima, não só correção. O *fix* é inferido pelo título.

---

## 9. Próximas expedições
| Ordem | Ação | Por quê |
|---|---|---|
| 1 | Implementar JS/TS (`lang/jsts.py`; R-P7, V2-6) e rodar a mesma pipeline | Projeção de 28–37 repositórios; é a maior alavanca de N para Q4 |
| 2 | Validar o tipo de tarefa: rotular 50–100 títulos à mão (V2-4) | Controle do principal confundidor |
| 3 | Decidir se o Python se amplia para o AIDev-pop inteiro (`--source aidev`, D22 proposta) | Teto de ~16 repositórios extras antes do filtro de HL |
| 4 | Sensibilidades: janela ampliada (D20), FA-provável, `ai_assist_declared` | Robustez |

---

## 10. Reprodução
| O quê | Como |
|---|---|
| Execução completa | `fa_hl\rodar_python.bat` (P1 → P2 → E6 → diagnóstico) |
| Só a E6, depois de mudar a análise (como na D21) | `fa_hl\rodar_e6.bat` |
| Relatório da pipeline | `out\e6\relatorio.md` |
| Tabelas completas | `out\e6\modelos_por_unidade.csv`, `teste_por_repositorio.csv`, `cox.csv`, `rmst.csv`, `kaplan_meier.csv` |
| Funis e exclusões | `out\p1\funil_p1.csv`, `out\p2\funil_p2.csv`, `out\diag\exclusions.csv`, `fa_destino.csv` |
| Parâmetros e versões | `out\p1\manifest.json`, `out\p2\manifest.json`, `out\e6\manifest.json` |
| Resultados do piloto anterior | `out_v1_piloto\` |
