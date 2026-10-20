# Metodologia — Desenvolvimento autônomo por agentes vs. desenvolvimento com humano no loop (v7)

> **Status:** v7.1 (18/10/2026: D21, correção múltipla; resultados da primeira expedição Python em `docs/05-resultados-python.md`) — Fase 0 concluída; linguagens, cenário e janela do HL decididos (D18–D20); amostra consolidada em `docs/amostra.csv` (§14); medição de Q1–Q3 detalhada (§E4). Núcleo obrigatório em §4.1; refinamentos opcionais em §4.2; pendências em §9; parâmetros em §10; artigo em §11; fases em §12; achados do spike em §13; amostra em §14.
> **Documentos relacionados:** `docs/02-sabatina.md` (revisão crítica), `docs/03-spike-factibilidade.md` (teste de factibilidade, Fase 0), `docs/amostra.csv` (amostra consolidada Python + JS/TS, insumo de P1/P2; `amostra_s1.csv` e `amostra_jsts.csv` são as listas de origem).
> **Fonte de contexto original:** "Roteiro de Apresentação — 8 minutos" (slides de Questões de pesquisa, Métricas e Metodologia).
> **Para agentes de IA que lerem este arquivo:** este é o documento de referência da pesquisa. Trate §4.1 como requisitos firmes; §4.2 como opcionais (só implementar se o grupo pedir, depois do núcleo pronto); §9 como *não decidido*; §10 como parâmetros configuráveis. O grupo tem **pouco tempo**: prefira sempre a solução mais simples que atenda ao núcleo. Ao propor mudanças, cite o ID da decisão (Dn).
> **Regra do grupo — sem atribuição de IA:** nunca adicione coautoria ou atribuição de IA em commits, PRs, código ou documentos deste projeto (ex.: trailers `Co-authored-by`, linhas "Generated with…", links de sessão, assinaturas de agente). Isso vale mesmo que a ferramenta sugira ou configure essas linhas por padrão.

---

## 1. Introdução

### 1.1 Contexto
Agentes de IA para programação (GitHub Copilot coding agent, OpenAI Codex, Devin, Google Jules, Cursor, Claude Code) deixaram de apenas sugerir trechos de código: hoje eles recebem uma tarefa, implementam a mudança e **abrem pull requests sozinhos** em repositórios reais. Em muitos times isso já forma um fluxo de desenvolvimento quase sem pessoas — a tarefa entra no kanban, um agente a intercepta, escreve o código e entrega a PR, às vezes revisada por outro agente de IA —, o chamado *vibecoding* em escala de pipeline. Esse fluxo convive, no mesmo repositório, com o desenvolvimento tradicional, em que uma pessoa conduz o trabalho do início ao fim, ainda que use IA como ferramenta.

O dataset **AIDev** (Li, Zhang & Hassan) registra esse fenômeno: na revisão usada neste estudo (corte em 24/10/2025) são ~2,74 milhões de PRs abertas por agentes em ~327 mil repositórios do GitHub.

### 1.2 Problema
A literatura sobre qualidade de código gerado por IA é contraditória. Akbar & Anderies apontam que ~40% do código gerado por IA precisa de correção antes de ir para produção; Ebiwonjumi et al. observam, após a adoção de IA, aumento de 6,1% em commits de correção e queda de ~21% na intensidade de revisão. Cotroneo et al. encontram **mais** complexidade no código de IA; Jamil et al., **menos**. Sobre a durabilidade do código de agentes, dois estudos de 2026 chegam a conclusões **opostas** (§1.6). Parte dessa divergência vem de comparações entre projetos diferentes, de definições difusas de "código de IA" — que misturam autocompletar, chat e agentes autônomos — e da falta de controle por tipo de tarefa e tamanho da mudança.

### 1.3 Objetivo
**Avaliar se o código produzido por um fluxo de desenvolvimento autônomo, conduzido por agentes de IA da tarefa até a PR, difere do código produzido por um fluxo com humano no loop — em complexidade, manutenibilidade, estrutura e, principalmente, na frequência com que precisa ser corrigido depois.** A comparação é feita **dentro do mesmo repositório**, para isolar o efeito do fluxo de desenvolvimento das diferenças entre projetos (Kitchenham, Pfleeger & Fenton, 1995).

### 1.4 O que este estudo **não** é
- **Não** é "IA vs. sem IA". O grupo de comparação pode ter usado IA (autocompletar, chat, agente no terminal). O que o distingue é a **presença de um humano conduzindo o processo**.
- **Não** avalia um agente específico como produto. Comparações entre agentes são análises secundárias.
- **Não** mede produtividade (velocidade, volume entregue), e sim características do código entregue e seu comportamento posterior.
- **Não** assume que o FA é "sem revisão": o fluxo autônomo pode incluir revisores humanos ou de IA (§2.1). O que se avalia é o **sistema autônomo como um todo**, e apenas o código **que passou pelo portão de merge**.

### 1.5 Visão geral do método (em uma frase)
Selecionamos repositórios Python do AIDev em que os dois fluxos convivem; em cada um, tomamos como unidade **cada PR integrada à branch principal** (o diff líquido que ela trouxe), classificamos cada PR como **Fluxo Autônomo (FA)** ou **Humano no Loop (HL)**, medimos com o Radon o código antes e depois de cada PR, rastreamos com `git blame`/`git log` quantas vezes e por quem as linhas introduzidas são retrabalhadas depois e comparamos os fluxos com testes pareados por repositório e modelos mistos.

### 1.6 Relação com trabalhos anteriores e fragilidade de novidade
O AIDev foi o dataset do **MSR 2026 Mining Challenge**, e já existem trabalhos muito próximos deste:

| Trabalho | Sobreposição |
|---|---|
| Rahman & Shihab, *Will It Survive?* (EASE 2026) | Praticamente a nossa Q4: AIDev, comparação intra-repositório, sobrevivência de linhas via `git blame`, Kaplan-Meier/Cox, intenção das modificações. Concluem que código de agente **sobrevive mais** (HR 0,842), mas recebe mais modificações corretivas. |
| Popescu et al. (GitHub/TU Delft, arXiv 2604.00917) | Q4: concluem o **oposto** — código de agente sobrevive menos e tem mais churn (efeitos pequenos). |
| *More Code, Less Reuse* (arXiv 2601.21276) | Q1/Q3 com Radon em Python (AIDev, > 500 estrelas): diferenças mínimas; ~85% dos pares sem variação de CC. |
| Agarwal, He & Vasilescu (MSR 2026) | Q1/Q2 em nível de repositório: +18% warnings estáticos, +39% complexidade cognitiva após adoção de agentes. |

**Fragilidade reconhecida:** como pesquisa de "primeira medição", este trabalho seria em grande parte redundante. Seu diferencial está em: (1) o construto **FA × HL** (fluxo, não autoria); (2) a unidade **PR integrada** nos dois grupos; (3) o FA restrito a agentes com sinal de identidade confiável; (4) controles que os trabalhos anteriores não usam (tamanho, e opcionalmente tipo de tarefa e nível de autonomia).

**Estratégia adotada:** manter as quatro QPs no desenho, executar um **piloto com uma amostra de repositórios** (§12, Fase 1) e, à luz dos resultados, decidir se a Q4 passa a ser a questão principal, com o enquadramento de **reconciliar a contradição** Rahman & Shihab × Popescu et al. Essa decisão fica registrada como pendente (§9, P1).

---

## 2. Construto: os dois fluxos de desenvolvimento

| | **Fluxo Autônomo (FA)** — "vibecode" | **Fluxo com Humano no Loop (HL)** |
|---|---|---|
| Quem conduz | Agente de IA, da captura da tarefa até a abertura da PR | Uma pessoa, durante todo o processo |
| Uso de IA | Total: o agente escreve todo o código | Permitido (autocompletar, chat, agente interativo), sob condução humana |
| Revisão | Humana e/ou por agente revisor de IA | Humana (eventualmente com revisores de IA) |
| Papel humano permitido | Criar/atribuir a tarefa; revisar, comentar e aprovar/mergear a PR | Tudo |
| O que o descaracteriza | Humano commitar código na PR do agente → PR **mista** | — |
| Evidência no dado (núcleo) | PR do AIDev de agente com conta própria de bot (D15), mergeada e pura | PR mergeada no mesmo repositório, não ligada a agente e não aberta por bot |

**Fronteira importante:** revisão e aprovação humana *depois* da PR fazem parte do fluxo autônomo — são o portão de qualidade do pipeline, não condução do desenvolvimento. Já código escrito por humano dentro da PR descaracteriza o FA.

**Consequência metodológica:** PRs humanas com sinais de uso de IA (ex.: trailer `Co-authored-by: Claude`) **pertencem ao HL** por definição. O uso invisível de IA por humanos deixa de ser uma ameaça de contaminação e passa a fazer parte do construto HL.

### 2.1 Revisores de IA no fluxo autônomo
Pipelines autônomos frequentemente incluem um **segundo agente atuando como revisor** (ex.: CodeRabbit, Copilot code review, Gemini Code Assist, Sourcery, Qodo/PR-Agent, Greptile, Ellipsis, Cursor Bugbot). Esses revisores comentam e podem pedir mudanças, e o agente autor itera em resposta — sem nenhum humano no circuito. Portanto **pedido de mudança ≠ intervenção humana**. No núcleo, isso é apenas reconhecido no texto do artigo (§11); a medição do tipo de revisor e do nível de autonomia é o refinamento opcional D9.

---

## 3. Questões de pesquisa

| QP | Pergunta | Literatura de apoio |
|---|---|---|
| Q1 — Complexidade | PRs do FA introduzem mais ou menos complexidade (ciclomática, Halstead) que PRs do HL? | Cotroneo et al.; Patel et al.; Jamil et al.; Idrisov & Schlippe |
| Q2 — Manutenibilidade | O código fica mais fácil ou mais difícil de manter após uma PR do FA, comparado ao HL? | Jamil et al.; Molison et al.; Li et al. |
| Q3 — Estrutura e tamanho | Como diferem tamanho, documentação e espalhamento das PRs entre FA e HL? | Idrisov & Schlippe; Cotroneo et al.; Patel et al. |
| **Q4 — Correção** | Com que frequência, em quanto tempo e por quem o código introduzido pelo FA é retrabalhado/corrigido, comparado ao HL? | Akbar & Anderies; Ebiwonjumi et al.; Przymus et al.; Rahman & Shihab; Popescu et al. |

Base metodológica: Li, Zhang & Hassan (AIDev); Kitchenham, Pfleeger & Fenton (1995) — validade de medição; Ying, Towey & Zhang (2025) — avaliação de código gerado por IA.

---

## 4. Registro de decisões

### 4.1 Núcleo (obrigatório)

| ID | Decisão | Justificativa |
|---|---|---|
| D0 | **Os grupos comparados são fluxos de desenvolvimento (FA vs. HL), não autoria IA vs. humano** (§2). | Reflete o objetivo real da pesquisa e resolve a ambiguidade de "código de IA" na literatura. |
| D1 | **Squash não exclui repositórios**: o commit squash é a forma como a PR aparece na branch principal e é tratado pela regra geral de D14. | Sem isso, Q4 é impossível em repositórios com política de squash, que são muitos. |
| D2 | **Pareamento = repositório.** Teste principal: Wilcoxon pareado sobre medianas FA vs. HL por repositório + Cliff's delta. Complemento no nível de unidade: modelo misto com efeito aleatório de repositório. | Isola o efeito do projeto sem depender de casamento unidade a unidade, que é frágil. |
| D3 | **Q4 mede retrabalho (qualquer modificação posterior das linhas) e, como subconjunto, correções classificadas como *fix*.** | Retrabalho é objetivo e reprodutível; *fix* responde à pergunta de defeito, mas depende de heurística. |
| D4 | **Seleção de repositórios é uma pipeline separada (P1)**, que entrega uma lista versionada para a pipeline principal (P2). | Desacopla a amostragem (barata, iterável) da extração de métricas (cara). |
| D5 | Versão do AIDev **fixada** na revisão `7840b6e61a5828461cd96806c52c20194ef57979` do Hugging Face (corte: 24/10/2025). | O dataset mudou entre versões (933k → 2,74M PRs) e versões diferentes têm tabelas diferentes (§6.0). Revisão usada no spike de 13/10/2026. |
| D6 | Fonte da seleção = **subconjunto AIDev-pop** (repos > 100 estrelas). | `pr_commits` e `pr_commit_details` só existem nesse subconjunto. |
| D7 | **Unidades classificadas só até o corte do AIDev**; o rastreamento de retrabalho (Q4) pode ir até o snapshot do clone. | Depois do corte, PRs de agentes não estão no AIDev e vazariam para o HL sem serem detectadas. |
| D8 | Seleção em dois níveis em P1 (Tier A: metadados; Tier B: clone leve); corte final de validade por grupo em P2. | Aprovado pelo grupo na v1. |
| **D14** | **Unidade de análise = PR integrada**: o diff líquido que cada PR mergeada trouxe à branch principal, **igual para FA e HL** (§6.2). Substitui a unidade "commit" das versões anteriores. | Ver justificativa detalhada abaixo. |
| **D15** | **FA principal = agentes que operam com conta própria de bot** (Copilot coding agent, Devin, Google Jules). Codex, Cursor e Claude Code formam o estrato **FA-provável**, fora da análise principal (sensibilidade opcional). | Para esses três agentes, autoria do agente e pureza da PR são verificáveis pelo autor dos commits. Codex e Claude Code costumam commitar com a conta do humano, o que torna a pureza inverificável e o modo de acionamento ambíguo. |
| **D16** | **Fase 0 obrigatória: spike de factibilidade** antes de implementar P2 (`docs/03-spike-factibilidade.md`). **Executada em 13/10/2026**: NO-GO pelo critério original (≥ 30 repositórios com ≥ 10 PRs FA e ≥ 10 HL; só 4 atendiam). Critério substituído por D17. | O número de repositórios que sobrevivem aos filtros era desconhecido. |
| **D17** | **Amostra inicial: cenário S1 (Copilot, Devin, Jules) no AIDev-pop, com ≥ 5 PRs FA elegíveis e ≥ 5 PRs HL no período, por repositório** → **21 repositórios confirmados + 3 a confirmar** (HL subestimado por falha do script) = até 24 (§14, `docs/amostra_s1.csv`). A lista é de **entrada**: repositórios que, após E3 na Fase 1, ficarem abaixo de 5 unidades válidas em algum grupo saem e são registrados no funil. | Mantém o construto rigoroso de D15 e o AIDev-pop (dados de commits disponíveis); ≥ 10 PRs deixaria só ~4–5 repositórios. Custo aceito: poder estatístico menor no teste por repositório (§13.3). |
| **D17-bis** | **O mínimo de ≥ 5 PRs FA e ≥ 5 PRs HL válidas por repositório vale para TODAS as análises** — modelos por unidade (análise principal) e Wilcoxon (confirmação). A proposta R-P2 de aceitar repositórios com 1–4 FA nos modelos foi **rejeitada**. | Decisão do grupo em 18/10/2026: manter, em cada repositório, uma base mínima de comparação entre as abordagens. Custo aceito: PRs FA de repositórios com 1–4 FA ficam fora. |
| **D18** | **Linguagens: Python e JavaScript/TypeScript** (família ECMAScript tratada em conjunto; linguagem como estrato/covariável). Python é medido com Radon; JS/TS com **Lizard** (limites de função, CC, NLOC) e **tree-sitter** (filtro de reformatação). Halstead e MI (Q2) só existem para Python. | Spike JS/TS (§13.4): +56 repositórios no S1, sem mudar D15. A comparação é pareada por repositório, então ferramentas diferentes por linguagem não enviesam o contraste FA × HL; só valores absolutos não são comparáveis entre linguagens. |
| **D19** | **Cenário S1 confirmado** (Copilot, Devin, Jules). S2 (Cursor) e AIDev completo **não adotados**. | Decisão do grupo em 13/10/2026: manter o construto mais rigoroso; com JS/TS a amostra já chega a ~80 repositórios. |
| **D20** | **Janela de seleção do HL = concorrente** (do 1º merge FA no repositório até o corte do AIDev). A janela **ampliada** (início 180 dias antes do 1º merge FA, com o mês do merge como covariável) é usada **só como análise de sensibilidade**, se houver tempo; repositórios com status `incluir_se_hl_ampliado` entram apenas nela. | Mantém FA e HL no mesmo momento do projeto, evitando confusão temporal em Q4; a ampliada ganharia só ~3–5 repositórios (§13.5). Decisão do grupo em 13/10/2026. |
| **D21** | **Correção múltipla em duas famílias (Holm):** família confirmatória = métricas primárias de todas as QPs (R-P5: `cc_delta_per_size`, `mi_delta_mean`, `size_churn`, `lloc_delta`, `rework_rate_w`); família exploratória = demais métricas, por QP. Substitui "Holm dentro de cada QP". Cox e RMST de Q4 são reportados com IC, como estimativas complementares do mesmo desfecho. | Autorizada pelo grupo em 18/10/2026 (V2-1 do doc 04). Antes, as primárias eram penalizadas pelas métricas exploratórias da mesma QP (17 na Q3) e nada controlava o erro entre QPs. **Ressalva:** as primárias foram fixadas depois do piloto v1 (crewAI e lisa), que faz parte da amostra atual; não são um pré-registro pleno. |

#### Justificativa de D14 — por que a unidade é a PR integrada, e não o commit
1. **A granularidade de commits difere sistematicamente entre os grupos.** Agentes produzem commits de plano ("Initial plan"), de trabalho em andamento e de iteração; o número de commits por PR é a maior diferença estrutural entre PRs de agentes e de humanos (Cliff's δ = 0,54, arXiv 2601.17581). Comparar commit a commit mediria o *hábito de commitar*, não o código entregue.
2. **A PR é a unidade de entrega e de decisão nos dois fluxos.** O FA é definido no nível da PR (a tarefa vira uma PR), e o portão de qualidade — revisão e merge — atua sobre a PR inteira. É o que efetivamente passa a existir no produto.
3. **Commits intermediários contêm código que nunca foi entregue.** Uma linha escrita e desfeita dentro da mesma PR geraria um falso "retrabalho" e falsas variações de complexidade; o diff líquido representa só o que chegou à branch.
4. **Harmoniza os modos de integração.** Com squash, a PR já aparece como um único commit; com merge commit, como um conjunto de commits. Tomando a PR como unidade, os dois casos ficam equivalentes e o tratamento é o mesmo para FA e HL.
5. **Alinha com a literatura comparável.** Rahman & Shihab definem o "nascimento" do código como o merge da PR.
6. **Reduz custo.** Menos unidades e menos execuções do Radon e do `git blame`.

**Custos aceitos:** PRs grandes agregam várias mudanças (mitigado por covariável de tamanho e normalização); perde-se a granularidade intra-PR; é preciso identificar as fronteiras das PRs no histórico git (§6.2), o que torna repositórios que integram por *rebase* difíceis de tratar sem a API do GitHub (no núcleo, essas PRs são excluídas e contadas no funil).

### 4.2 Refinamentos opcionais (para lapidar a pesquisa depois do núcleo pronto)
Decisões já discutidas e aprovadas em conceito, mas **fora do escopo mínimo**. Só devem ser implementadas se houver tempo, na ordem sugerida.

| ID | Refinamento | Custo | Observação |
|---|---|---|---|
| D13 | **"Custo humano escondido"** em Q4: fração do retrabalho do código FA feita por PRs HL (e vice-versa). | Quase zero (sai do E5) | Primeiro da fila: só exige reportar um número que o núcleo já calcula. |
| D11 | **Controle por tipo de tarefa** (`feat/fix/refactor/docs/test/chore/outro`). Versão *lite*: prefixo de conventional commits + palavras-chave no título da PR. Versão completa: classificador LLM + validação manual (~200 itens). | Lite: baixo · Completa: médio | Fortemente recomendado na versão lite: é o principal confundidor apontado na sabatina. Versões antigas do AIDev traziam uma tabela `pr_task_type` pronta (§6.0). |
| D12 | **HL só via PR; pushes diretos como sensibilidade.** | Zero | **Já absorvido pelo núcleo** via D14: como a unidade é a PR, pushes diretos não entram. Fica aqui só como registro. |
| D9 | **Gradiente de autonomia** (FA-direto / FA-iterado-IA / FA-iterado-humano) e **tipo de revisor** (`humano`, `revisor_ia`, `outro_bot`), com lista de revisores de IA curada a partir de `pr_reviews`, `pr_review_comments` e `pr_comments`. | Médio | Contribuição nova, mas depende de curadoria e de inferência temporal. |
| D10 | **Modo de acionamento** (fila vs. interativo) por evidências, para incluir Codex/Cursor/Claude Code no FA. | Médio-alto | No núcleo, substituído pela regra simples de D15. |

---

## 5. Arquitetura conceitual

```
AIDev-pop (pin) ──► Fase 0: spike (P1 Tier A) ──► go/no-go
                         │
                         ▼
                    P1: Seleção ──► selected_repos + agent_prs (+ manifesto, funil)
                                              │
                                              ▼
   P2: clone → E2 PRs integradas e classificação FA/HL → E3 filtros → E4 métricas Radon
            → E5 retrabalho e origem
                                              │
                                              ▼
                                  E6 análise estatística → resultados por QP
```

### Contrato P1 → P2
`selected_repos.parquet` (núcleo): `repo_full_name`, `default_branch`, `stars`, `n_fa_prs_eligible`, `n_hl_prs_estimated`, `agents` (lista), `first_fa_merge`, `last_fa_merge`, `aidev_revision`, `selection_run_id`.

`agent_prs.parquet` (núcleo; uma linha por PR de agente do repositório, de qualquer agente — necessária para tirar PRs de agentes do HL): `repo_full_name`, `pr_number`, `agent`, `agent_group ∈ {FA_principal, FA_provavel}`, `merged_at`, `is_pure`, `pr_author_login`, `py_additions`.
Campos **opcionais** (D9/D11): `task_type`, `task_type_source`, `reviewer_kinds`, `n_change_requests_human`, `n_change_requests_ai`, `autonomy_level`, `ambiguity_flags`.

`manifest.json`: critérios, parâmetros, revisão do AIDev e contagem de eliminados em cada filtro (funil, para o artigo).

---

## 6. Etapas

### 6.0 — Versão do dataset
A revisão fixada (D5: `7840b6e…`, corte 24/10/2025) contém: `all_pull_request`, `all_repository`, `all_user`, `pull_request`, `repository`, `user`, `pr_comments`, `pr_reviews`, `pr_review_comments`, `pr_commits`, `pr_commit_details`. Revisões anteriores incluíam também `pr_task_type` (tipo de tarefa classificado por LLM), `human_pull_request`/`human_pr_task_type` (amostra de PRs humanas), `pr_timeline`, `issue` e `related_issue`, que **não estão na revisão atual**. Decisão (D5): usar a revisão atual, aceitando a ausência dessas tabelas; o controle por tipo de tarefa (D11, opcional) será feito na versão *lite* a partir dos títulos das PRs.

### E1 — Seleção de repositórios (P1)
**Tier A** (só metadados do AIDev; é o que o spike da Fase 0 executa):
- `repository.language ∈ {Python, JavaScript, TypeScript}` (D18).
- PRs do FA principal (D15) mergeadas **até o corte do AIDev** (D7), puras (todos os commits — exceto merges de sincronização e commits de bots de automação como `github-actions[bot]`/`autofix-ci[bot]`, que são neutros — de autoria do agente) e que adicionam ≥ 3 linhas em arquivos `.py` que não são teste, migration ou vendorizado.
- ≥ N PRs elegíveis por repositório (N = 5, D17).

**Tier B** (por repositório candidato):
- Estimativa de PRs HL mergeadas no período: listagem de PRs da API REST do GitHub por id do repositório (a API de busca foi descartada por limites secundários), excluindo bots e PRs de agentes do AIDev; ou, na Fase 1, contagem direta no clone.
- Proporção de código `.py` na árvore ≥ limiar (ex.: 60%).
- Modo de integração predominante (merge, squash, rebase).

Repositórios que, após E3 em P2, ficarem abaixo de N unidades válidas por grupo são excluídos e registrados no funil.

### E2 — Unidade (PR integrada) e classificação do fluxo
**Snapshot:** SHA do HEAD da branch padrão registrado na clonagem.
**Período de observação (D7):** do primeiro merge de PR do FA principal no repositório até o corte do AIDev (24/10/2025). O retrabalho é observado até o snapshot do clone; como o snapshot é posterior ao corte em mais de W (353 dias em 13/10/2026), toda unidade tem janela W completa.

**Identificação das PRs integradas** — percorrer o histórico de **primeiro pai** da branch padrão:
| Modo | Como aparece | Unidade (antes → depois) | Commits pertencentes à unidade |
|---|---|---|---|
| Merge commit | commit com 2 pais e mensagem `Merge pull request #N from …` | `M^1 → M` | `git rev-list M^1..M` |
| Squash | commit com 1 pai e assunto terminando em `(#N)` | `S^1 → S` | `S` |
| Rebase | commits lineares sem marcação de PR | — | Núcleo: não identificável sem API; PRs FA nesse modo são excluídas e contadas no funil |

Fallback para PRs do FA não encontradas: API do GitHub `GET /repos/{owner}/{repo}/pulls/{n}` → `merge_commit_sha`.

**Classificação** (pelo número `#N` da PR cruzado com `agent_prs`):
- **FA** — PR do FA principal, mergeada e pura.
- **HL** — PR mergeada que não está em `agent_prs` (de nenhum agente), cujo autor não é bot. PRs com trailers de IA permanecem no HL com a flag `ai_assist_declared` (D0).
- **Fora da análise principal (contadas no funil):** PRs do FA-provável; PRs de agentes mistas; PRs de bots que não são agentes (dependabot, renovate, pre-commit-ci, github-actions…); PRs com assinatura de agente autônomo que não estão no AIDev (ex.: autor `copilot-swe-agent[bot]`); commits diretos na branch (não são PRs).

**Verificação de consistência (FA):** o conjunto de arquivos e o total de linhas adicionadas/removidas da unidade devem bater (com tolerância) com o diff da PR em `pr_commit_details`. Divergência → descartar e registrar.

Cada unidade carrega `integration_mode ∈ {merge, squash}`, usada como covariável/estrato.

### E3 — Filtros
Os filtros definem a **população de análise**, que é a mesma para todas as QPs: uma unidade que sai aqui não entra em Q1–Q4.
- **Arquivos considerados:** só código-fonte da família do repositório — Python: `.py`; JS/TS: `.js .jsx .mjs .cjs .ts .tsx .mts .cts` — que não é teste, migration, vendorizado, gerado ou configuração (padrões em `spike_aidev.py`: `LANG_EXT`, `TEST_FILE`, `EXCLUDED_FILE`; incluem `node_modules/`, `dist/`, `build/`, `*.min.js`, `*.d.ts`, `*.test.ts`, `__tests__/`). Os demais arquivos da PR (Markdown, testes, configuração) são ignorados nas métricas.
- **Tamanho da unidade** (`size_churn`): linhas lógicas adicionadas + removidas nos arquivos considerados, contadas nos hunks de `git diff -U0 B A`, sem linhas em branco e sem linhas só de comentário (§E4, passo 3).
- **Mínimo:** ≥ 1 função tocada (§E4, passo 5) e `size_churn` ≥ 3.
- **Máximo:** `size_churn` > 500 ou acima do p99 do repositório → descartar (mudanças em massa).
- **Reformatação:** se, para todos os arquivos considerados, a árvore sintática em B é igual à de A, a unidade é só formatação → descartar. Python: `ast.dump` sem atributos de posição. JS/TS: árvore do tree-sitter serializada sem posições e sem nós de comentário.
- **Parse:** arquivo que não faz parse em B ou em A (Python 2, erro de sintaxe) é removido da unidade e registrado; se não sobrar arquivo, a unidade é descartada.

### E3b — Tipo de tarefa (opcional, D11)
Versão lite: prefixo de conventional commits (`feat:`, `fix:`…) no título da PR → palavras-chave no título → `outro`. Versão completa: classificador LLM sobre título + descrição + arquivos, com prompt e modelo versionados, validado em amostra manual (kappa).

### E4 — Métricas de código antes e depois da unidade (Q1–Q3)

#### 6.4.1 Ideia central
Cada unidade U (uma PR integrada, D14) tem dois estados do repositório:
- **B — antes:** o commit da branch principal imediatamente anterior à PR (`M^1` para merge commit, `S^1` para squash);
- **A — depois:** o commit que trouxe a PR para a branch (`M` ou `S`).

As métricas são calculadas **nos dois estados, sobre o mesmo recorte de código**, e o efeito da PR é a diferença **Δ = valor(A) − valor(B)**. Registra-se também o **nível depois** (valor em A), que descreve o código que a PR deixou. O diff da PR **não é medido diretamente**: ele serve para localizar o que mudou (arquivos → linhas → funções). Medir arquivos inteiros em vez de trechos do diff é necessário porque métricas como complexidade ciclomática e Halstead só fazem sentido sobre código sintaticamente completo.

A comparação FA × HL é feita **sobre esses valores por unidade**: para cada repositório, compara-se a distribuição das Δ das unidades FA com a das unidades HL (E6).

#### 6.4.2 Procedimento por unidade
1. **Arquivos.** `git diff --name-status -M B A` lista os arquivos alterados e o tipo de mudança: `A` (adicionado), `M` (modificado), `R` (renomeado: caminho antigo em B, novo em A), `D` (removido). Mantêm-se só os arquivos considerados (E3).
2. **Conteúdo.** `git show B:<caminho_em_B>` e `git show A:<caminho_em_A>`. Ler pelo objeto git, sem checkout, garante que o resultado não depende do estado da cópia de trabalho.
3. **Linhas alteradas.** `git diff -U0 -M B A -- <arquivo>` → para cada hunk, as linhas **removidas** (numeração de B) e **adicionadas** (numeração de A). Uma linha modificada aparece como uma removida + uma adicionada.
4. **Funções.** `radon.complexity.cc_visit` no conteúdo de B e de A → lista de funções e métodos com nome, classe, `lineno`, `endline` e complexidade. Usam-se **funções e métodos**; blocos de classe não entram (evita contar o mesmo código duas vezes). O nome qualificado é `Classe.metodo` ou `funcao`.
5. **Funções tocadas.**
   - Em A: funções cujo intervalo `[lineno, endline]` contém ao menos uma linha **adicionada**.
   - Em B: funções cujo intervalo contém ao menos uma linha **removida**.
   - Une-se pelos nomes qualificados (chave: caminho em A + nome qualificado + ordinal para homônimos no mesmo arquivo). Cada função tocada recebe um status:

   | Status | Situação | Como entra nas deltas |
   |---|---|---|
   | `modificada` | existe em B e em A | Δ = A − B |
   | `nova` | existe só em A | B = 0 nas métricas aditivas; `is_new = True` |
   | `removida` | existe só em B | só na contagem de funções removidas (Q3); fora das deltas por função |

   Funções não tocadas são ignoradas: por definição, não mudaram e têm Δ = 0. Uma função renomeada aparece como `removida` + `nova` (limitação aceita). Código fora de funções (nível de módulo) não entra em Q1, mas entra nas métricas por arquivo (Q2 e Q3).
6. **Métricas por função tocada** (em B e em A):
   - **CC:** complexidade ciclomática do `cc_visit`.
   - **Halstead:** `radon.metrics.h_visit` aplicado ao **trecho da função** (`lineno..endline`, com `textwrap.dedent`), usando o campo `total`: vocabulário η, volume V, dificuldade D, esforço E. (O relatório por função do `h_visit` sobre o arquivo identifica funções só pelo nome, sem a classe, e métodos homônimos colidiriam.)
   - **Tamanho e documentação:** `radon.raw.analyze` sobre o trecho `lineno..endline` → LLOC e linhas de comentário; linhas de docstring via `ast.get_docstring`.
7. **Métricas por arquivo** (em B e em A, arquivo inteiro):
   - **MI:** `radon.metrics.mi_visit(código, multi=True)` e faixa (A ≥ 20, B 10–19, C < 10). Arquivo **adicionado** não tem MI em B → só `mi_after`, `is_new_file = True`, fora das deltas de Q2. Arquivo **removido** → fora de Q2.
   - **Raw:** `radon.raw.analyze` → LLOC, SLOC, comentários, linhas de strings multilinha.
8. **Agregação por unidade** — tabela 6.4.3.

#### 6.4.3 Métricas por unidade (o que entra em E6)
"Tocadas" = funções com status `modificada` ou `nova`. A coluna **Primária** indica a métrica proposta para a análise confirmatória de cada QP; as demais são secundárias/exploratórias. A escolha final deve ser fixada antes da Fase 2 (pendência P3).

| QP | Coluna | Definição | Primária |
|---|---|---|---|
| Q1 | `cc_delta_sum` | Σ sobre funções tocadas de [CC(A) − CC(B)] (nova: CC(B) = 0) — complexidade líquida adicionada | ✔ |
| Q1 | `cc_delta_per_size` | `cc_delta_sum` ÷ `size_churn` | |
| Q1 | `cc_after_max` | maior CC(A) entre as funções tocadas — pior função que a PR deixou | |
| Q1 | `cc_after_mean` | média de CC(A) entre as funções tocadas | |
| Q1 | `hal_{vocab,volume,difficulty,effort}_delta_sum` | Σ sobre funções tocadas de [H(A) − H(B)] | |
| Q2 | `mi_delta_mean` | média, entre arquivos `M`/`R`, de MI(A) − MI(B) | ✔ |
| Q2 | `mi_worsened` | 1 se algum arquivo `M`/`R` tem MI(A) < MI(B) | |
| Q2 | `mi_rank_drop` | 1 se algum arquivo cai de faixa (A→B, B→C, A→C) | |
| Q2 | `mi_after_min` | menor MI(A) entre os arquivos considerados (inclui novos) | |
| Q3 | `size_churn` | linhas lógicas adicionadas + removidas (também covariável de tamanho em E6) | |
| Q3 | `lloc_delta` | Σ arquivos [LLOC(A) − LLOC(B)] (arquivo novo: B = 0; removido: A = 0) — crescimento líquido | ✔ |
| Q3 | `comment_delta`, `docstring_delta` | Σ das variações de linhas de comentário e de docstring nas funções tocadas | |
| Q3 | `doc_ratio_after`, `doc_ratio_delta` | (comentários + linhas de docstring) ÷ LLOC nas funções tocadas, em A e A − B | |
| Q3 | `n_files`, `n_funcs_modified`, `n_funcs_new`, `n_funcs_removed` | espalhamento da mudança | |

Toda métrica é reportada **bruta e normalizada** por `size_churn`, e E6 inclui `log(size_churn)` como covariável. Reporta-se também a correlação de cada métrica com o tamanho (sabatina S1): se uma métrica for quase só tamanho, isso é dito explicitamente.

#### 6.4.4 Exemplo calculado
PR com um arquivo modificado. **Antes (B):**
```python
def preco(total, cliente):
    if cliente.vip:
        return total * 0.9
    return total
```
**Depois (A):**
```python
def preco(total, cliente, cupom=None):
    """Aplica descontos."""
    if cliente.vip:
        total *= 0.9
    if cupom and cupom.valido:
        total -= cupom.valor
    return max(total, 0)

def frete(cep):
    return 10 if cep.startswith("3") else 20
```
- Funções tocadas: `preco` (`modificada`: linhas adicionadas e removidas dentro dela) e `frete` (`nova`).
- CC no Radon: 1 + 1 por `if`, `and`/`or` e expressão condicional. `preco`: B = 2 (um `if`); A = 4 (dois `if` + um `and`). `frete`: A = 2 (uma expressão condicional); B = 0 porque é nova.
- `cc_delta_sum` = (4 − 2) + (2 − 0) = **4**; `cc_after_max` = 4; `n_funcs_modified` = 1; `n_funcs_new` = 1; `docstring_delta` = +1.
- `mi_delta_mean` = MI(A) − MI(B) do arquivo inteiro, e assim por diante para as demais colunas.

Se outra função do mesmo arquivo, não tocada, tivesse CC = 10, ela não entraria em nenhuma das contas acima.

#### 6.4.5 Saídas (contrato E4 → E6)
- `function_metrics.parquet` — uma linha por função tocada: `unit_id`, `repo`, `file_path`, `qualname`, `status`, `cc_b`, `cc_a`, `hal_vocab_b/_a`, `hal_volume_b/_a`, `hal_difficulty_b/_a`, `hal_effort_b/_a`, `lloc_b/_a`, `comments_b/_a`, `docstring_lines_b/_a`.
- `file_metrics.parquet` — uma linha por arquivo considerado: `unit_id`, `path_b`, `path_a`, `change_type`, `parse_ok_b`, `parse_ok_a`, `mi_b`, `mi_a`, `mi_rank_b`, `mi_rank_a`, `lloc_b`, `lloc_a`, `sloc_b`, `sloc_a`, `comments_b`, `comments_a`.
- `unit_metrics.parquet` — uma linha por unidade: `unit_id`, `repo`, `pr_number`, `flow` (FA/HL), `agent`, `integration_mode`, `sha_b`, `sha_a`, `merged_at`, `size_churn` e todas as colunas da tabela 6.4.3.
- `exclusions.parquet` — arquivos e unidades descartados, com o motivo (funil).

#### 6.4.6 Reprodutibilidade e idempotência
- `unit_id` = `<owner>/<repo>#<pr_number>`; cada execução sobrescreve as linhas da mesma unidade, então reprocessar uma unidade não duplica dados.
- Tudo é lido de SHAs fixos (`sha_b`, `sha_a`) por `git show`; o resultado não depende da cópia de trabalho nem da data de execução.
- Versões fixadas e registradas no manifesto: Python usado para o parse (ex.: 3.12), Radon (ex.: 6.0.1) e Git.
- Processamento por unidade é independente → pode ser paralelizado por repositório.

#### 6.4.7 JavaScript/TypeScript (D18)
O Radon só lê Python. Para JS/TS, o **Lizard** fornece limites de função (`start_line`, `end_line`), CC e NLOC, e entra nos passos 4–6 no lugar de `cc_visit`; o filtro de reformatação usa tree-sitter no lugar de `ast`. Não há Halstead nem MI equivalentes maduros → Q2 e as colunas de Halstead ficam restritas a Python (vazias para JS/TS). Linhas de comentário vêm do Lizard/tree-sitter; docstrings não se aplicam (JSDoc conta como comentário). Alternativa, se o grupo preferir uniformidade: usar o Lizard também para a CC de Python. Como a comparação é pareada por repositório, ferramentas diferentes por linguagem não enviesam o contraste FA × HL; só valores absolutos não podem ser comparados entre linguagens.

### E5 — Retrabalho, correção e origem (Q4)
- Mapear cada commit da branch padrão à sua unidade (tabela `commit → unidade` de E2).
- Para cada unidade posterior P que toca um arquivo de C: `git blame -w -M -C` no estado **antes** de P sobre as linhas removidas/alteradas por P → cada linha é atribuída a um commit, e daí à unidade de origem (lógica estilo SZZ).
- Métricas por unidade C:
  - taxa de retrabalho = linhas de C alteradas/removidas em até W ÷ linhas adicionadas por C;
  - `has_rework` (≥ 1 linha retrabalhada em W);
  - tempo até o primeiro retrabalho (sobrevivência, com censura em W ou no snapshot);
  - origem do retrabalho: FA, HL, FA-provável, bot, commit direto;
  - subconjunto *fix*: P classificada como correção (palavras-chave `fix|bug|error|crash|regression…` ou prefixo `fix:` no título da PR/mensagem).
- Opcional (D13): custo humano escondido = fração das linhas retrabalhadas de C cujo retrabalho veio do HL.

### E6 — Análise estatística
- **Principal (D2):** por repositório, mediana de cada métrica por grupo → Wilcoxon pareado (signed-rank) + Cliff's delta com IC.
- **Nível unidade (núcleo):** `métrica ~ fluxo + log(tamanho) + integration_mode + (1 | repo)`; Q4 binária → logística mista; tempo → Kaplan-Meier e Cox com frailty por repositório.
- Termos opcionais: `+ task_type` (D11); `fluxo` desdobrado em níveis de autonomia (D9).
- Correção para comparações múltiplas (D21): Holm em duas famílias, separadamente nos modelos por unidade e no Wilcoxon — **confirmatória** = as métricas primárias das quatro QPs juntas (hoje 5); **exploratória** = as demais métricas, dentro de cada QP. Só a família confirmatória sustenta conclusões; as exploratórias geram hipóteses.
- Secundárias (se houver tempo): por agente; FA-provável como sensibilidade; HL com vs. sem `ai_assist_declared`.

---

## 7. Ameaças à validade (iniciais)
- **Novidade:** sobreposição com trabalhos de 2026 (§1.6); mitigada pelo construto FA × HL, pela unidade PR e pelos controles, e pela decisão pós-piloto sobre a ênfase em Q4.
- **Construto do FA:** restrito a Copilot coding agent, Devin e Jules (D15); generaliza para agentes "de fila" com conta própria, não para todos os agentes. Os resultados descrevem o sistema autônomo (autor + eventuais revisores), não o agente isolado.
- **Viés do merge:** só PRs mergeadas entram; medimos a qualidade do que passou pelo portão, não a do fluxo como um todo.
- **Construto do HL:** uso de IA não declarado por humanos é parte do construto (D0), mas limita a interpretação: o HL é "conduzido por humano", não "sem IA".
- **Tipo de tarefa e localização:** agentes podem receber tarefas menores ou módulos periféricos; sem D11, o controle é só por tamanho e repositório.
- **Rebase:** PRs integradas por rebase são excluídas no núcleo; repositórios com essa política ficam sub-representados.
- **Retrabalho ≠ qualidade:** código em arquivos pouco tocados sobrevive por falta de oportunidade; heurística de *fix* tem erros → retrabalho total é a medida principal de Q4.
- **Tamanho e concentração da amostra:** ~21–24 repositórios e ~200–260 PRs FA (antes dos filtros finos); 3 repositórios concentram ~37% das PRs FA. O teste por repositório só detecta efeitos médios/grandes; o modelo misto por unidade é a principal fonte de poder (§13.3).
- **Agentes recentes:** a maior parte das PRs do Copilot coding agent é de jun–out/2025; o FA reflete essa janela curta e versões iniciais dos agentes.
- **Linguagens e ferramentas:** Python e JS/TS são medidos com ferramentas diferentes (Radon × Lizard); a comparação FA × HL é sempre intra-repositório, mas valores absolutos não são comparáveis entre linguagens, e Q2/Halstead cobrem só os repositórios Python.
- **Generalização:** repositórios > 100 estrelas, Python e JS/TS. **Ferramental:** Radon só analisa Python 3 válido.

---

## 8. Glossário
- **FA (Fluxo Autônomo):** desenvolvimento em que um agente de IA conduz o trabalho da tarefa até a PR, sem código humano na PR. No núcleo, só Copilot coding agent, Devin e Jules (D15).
- **FA-provável:** PRs de Codex, Cursor e Claude Code; autonomia e pureza não verificáveis com segurança.
- **HL (Humano no Loop):** desenvolvimento conduzido por uma pessoa, com ou sem ferramentas de IA.
- **PR pura / mista:** PR do agente sem / com commits de humanos.
- **Unidade / PR integrada:** diff líquido que uma PR mergeada trouxe à branch principal (D14).
- **Retrabalho:** modificação ou remoção posterior de linhas introduzidas por uma unidade.
- **Snapshot:** estado do repositório (SHA do HEAD) no momento da clonagem.
- **Estados B e A:** o commit da branch principal imediatamente antes da PR (B) e o commit que a integrou (A); as métricas de Q1–Q3 são Δ = A − B (§E4).
- **Função tocada:** função ou método cujo intervalo de linhas contém uma linha adicionada (em A) ou removida (em B) pela PR.
- **Nível depois:** valor da métrica em A, descrevendo o código que a PR deixou.
- **Spike:** teste rápido de factibilidade (Fase 0).
- **P1 / P2:** pipeline de seleção de repositórios / pipeline principal de extração e análise.

---

## 9. Pendências
| ID | Pendência | Quando decidir |
|---|---|---|
| P1 | **Ênfase em Q4** e reposicionamento como reconciliação da contradição Rahman & Shihab × Popescu et al. | Após o piloto (Fase 1) |
| ~~P2~~ | ~~Revisão do AIDev a fixar~~ — **resolvida** em D5 (revisão atual `7840b6e…`). | — |
| P4 | **Confirmar HL** de `mlflow/mlflow`, `airbytehq/airbyte` e `BerriAI/litellm` (estimativa falhou/saiu 0 por erro do script; repositórios muito ativos). | Rodada corrigida do spike ou início da Fase 1 |
| ~~P5~~ | ~~Janela do HL~~ — **resolvida** em D20: concorrente como regra; ampliada (180 dias) só como sensibilidade. | — |
| ~~P6~~ | ~~Ampliação da amostra (S2 / AIDev completo)~~ — **resolvida** em D19: não adotadas. | — |
| ~~P8~~ | ~~Incluir JavaScript/TypeScript~~ — **resolvida** em D18: incluído. | — |
| P7 | **Amostragem do HL** para reduzir custo da Fase 2: limitar a K PRs HL por repositório (ex.: 50, sorteadas no período), já que alguns têm > 1.000 (`marimo`, `azure-sdk-for-python`). | Antes da Fase 2 |
| P3 | Itens S1–S5 da sabatina ainda não decididos: covariáveis de oportunidade e análise em arquivos compartilhados (S2), RMST (S2), hipóteses e análise primária fixadas antes dos dados (S5) | Antes da Fase 2 |
| R6 | Efeito aleatório do solicitante | Opcional |
| R7 | Q5 exploratória sobre processo de revisão | Opcional (caro) |

---

## 10. Parâmetros com valor padrão (ajustáveis)
| Parâmetro | Padrão |
|---|---|
| N mínimo de unidades válidas por grupo e repositório | **5** (D17) |
| Janela W de Q4 | 90 dias (censura para unidades sem W completo) |
| Arquivos de teste | excluídos da análise principal |
| Agentes do FA principal | Copilot coding agent, Devin, Jules (D15) |
| Teto de repositórios | sem teto (amostra atual: até 24, §14) |
| Limites de tamanho | ≥ 3 LLOC; ≤ 500 LLOC ou p99 |
| Linguagens (D18) | Python; JavaScript + TypeScript |
| Proporção mínima de código-fonte da família (Tier B) | 60% |
| Critério de entrada na amostra (D17) | ≥ 5 PRs FA elegíveis (S1) e ≥ 5 PRs HL no período, por repositório |
| Janela de seleção do HL (D20) | concorrente: do 1º merge FA ao corte; ampliada (+180 dias antes) só na sensibilidade |

---

## 11. Implicações para a escrita do artigo
- **Posicionamento:** apresentar honestamente os trabalhos de 2026 (§1.6) e o diferencial deste estudo; se P1 for aprovada, abrir o artigo pela contradição sobre durabilidade do código de agentes.
- **Definição do FA:** um *sistema* que pode conter múltiplos agentes (autor + revisor); pedido de mudança não implica humano. Se D9 não for implementado, declarar isso como limitação e trabalho futuro.
- **Unidade PR:** justificar com os argumentos de D14.
- **Escopo do FA:** explicar por que só agentes com conta própria de bot (D15) e o que isso implica para a generalização.
- **Linguagem:** associativa, não causal — o desenho é observacional.
- **Transparência:** publicar o funil de seleção, o relatório do spike e as regras de classificação como material suplementar.

---

## 12. Roteiro de fases (menor trabalho possível)
| Fase | Entrega | Critério para avançar |
|---|---|---|
| **0 — Spike** ✅ | Concluída em 13/10/2026 (§13); amostra inicial em §14 | — |
| **1 — Piloto** | P1 completa + P2 núcleo rodando em ~6 repositórios da amostra (3 Python + 3 TS), variados em tamanho e modo de integração (sugestão — Python: `crewAIInc/crewAI`, `microsoft/lisa`, `gerlero/foamlib`; TypeScript: `theopenco/llmgateway`, `intellectronica/ruler`, `tokens-studio/figma-plugin`; evitar gigantes como `microsoft/vscode` no piloto) | Pipeline funciona ponta a ponta; quantas unidades sobrevivem a E3; resultados preliminares para decidir P1 (ênfase em Q4) |
| **2 — Estudo completo** | P2 em todos os repositórios selecionados + E6 | Resultados por QP |
| **3 — Refinamentos (opcional)** | D13 → D11 lite → D9 → D10 | Conforme o tempo |

---

## 13. Achados da Fase 0 (spike de 13/10/2026)
Detalhes, ressalvas e números completos em `docs/03-spike-factibilidade.md` §5. Revisão `7840b6e…`.

### 13.1 Funil do FA principal (Python, AIDev-pop)
| Etapa | PRs |
|---|---|
| PRs de Copilot, Devin e Jules no AIDev-pop | 30.155 |
| Em repositórios Python | 4.093 |
| Mergeadas até o corte | 2.011 |
| Puras (só commits do agente ou de bots neutros) | 1.292 (64%) |
| Tocam `.py` de produção (≥ 3 linhas) — **elegíveis** | **545** (Copilot 417, Devin 123, Jules 5) |

### 13.2 O que o spike confirmou ou mudou
- **D15 confirmada:** Copilot, Devin e Jules abrem 100% das PRs com conta de bot e commitam com ela. O Codex abre 0% com conta de bot e commita com a conta do humano (pureza inverificável); um único usuário concentra ~38% das PRs do Codex.
- **Cursor tem identidade de commit verificável** (`cursoragent`) em ~63% das PRs mergeadas → base para a ampliação S2 (P6).
- **Jules é irrelevante em Python** (5 PRs elegíveis).
- **O Copilot coding agent é recente:** a maior parte das PRs mergeadas é de jun–out/2025. Por isso D7 classifica até o corte (e não até corte − W): com o snapshot em 2026, a janela de Q4 já está garantida.
- **Corte real do AIDev:** 24/10/2025.
- **Distribuição muito concentrada:** a maioria dos repositórios tem 1–2 PRs FA; 3 repositórios (`mlflow`, `crewAI`, `reflex-web`) somam ~37% das PRs da amostra.
- **Repositórios dominados por agentes** (ex.: `SkBlaz/py3plex`: 51 PRs FA e 0 humanas) saem pelo critério de HL — não há comparação intra-repositório possível.

### 13.3 Cenários e poder estatístico
| Cenário | PRs elegíveis | repos ≥ 5 FA | ≥ 5 FA e ≥ 5 HL | ≥ 10 FA e ≥ 10 HL |
|---|---|---|---|---|
| **S1 — Copilot, Devin, Jules (escolhido, D17)** | 545 | 31 | **21 (+3 a confirmar)** | 4 |
| S2 — S1 + Cursor com identidade de commit | 660 | 39 | 28 | 5 |
| S3 — S2 + Codex etc. com pureza fraca | 4.096 | 110 | n/d | n/d |

**Poder:** com ~24 repositórios, o Wilcoxon pareado por repositório (α = 0,05, poder 80%) só detecta efeitos padronizados a partir de ~0,6 (médios/grandes). Os trabalhos anteriores acharam efeitos pequenos; por isso o **modelo misto no nível da unidade** (~200–260 PRs FA contra centenas de PRs HL) é a análise com mais poder, e o teste por repositório funciona como confirmação robusta. A meta de 100 repositórios não é atingível no AIDev-pop sem abandonar D15 (só S3 chega a ~110, com o Codex).

**Teto no AIDev completo** (`spike_teto.py`): fora do AIDev-pop há só ~16 repositórios Python com ≥ 10 estrelas e ≥ 5 PRs S1 esperadas, antes da checagem de HL. Os demais candidatos (483 com 0–4 estrelas) são projetos pessoais em que o agente faz quase todas as PRs, sem grupo humano. Ampliar a fonte renderia ~8–16 repositórios, exigindo coletar pureza e arquivos pela API do GitHub. **Conclusão:** com D15 e comparação intra-repositório, o máximo realista é ~30–40 repositórios (S1/S2 no AIDev-pop + ampliação); 100 só seria possível relaxando o construto (S3/Codex) ou aceitando repositórios sem grupo humano, o que inviabiliza D2.

### 13.4 Spike JavaScript/TypeScript (13/10/2026)
| Cenário | PRs elegíveis | repos N≥5 | N≥5 e HL≥5 | N≥10 e HL≥10 | N≥5 e HL ampliado≥5 |
|---|---|---|---|---|---|
| S1 — Copilot, Devin, Jules | 1.632 | 75 | **56** | 30 | 59 |
| S2 — S1 + Cursor com identidade de commit | 2.008 | 86 | 59 | 32 | 63 |

- Dos 56, **52 são TypeScript** e 4 JavaScript. Devin é muito mais presente em TS (787 PRs elegíveis) do que em Python (123).
- **Amostra combinada possível (S1, ≥ 5/≥ 5):** Python 24 + JS/TS 56 = **~80 repositórios e ~1.200 PRs FA**; no S2, ~90. Com ~80 repositórios, o teste pareado por repositório passa a detectar efeitos padronizados de ~0,3 (antes ~0,6).
- 4 candidatos JS/TS estão privados ou apagados (404 na API) e saem.
- Concentração: `liam-hq/liam` tem 161 PRs FA; se necessário, limitar as unidades FA por repositório (ex.: 50, sorteadas) para que um repositório não domine o modelo misto.
- Repositórios muito grandes entram na amostra (`microsoft/vscode`, `calcom/cal.com`): clonar com `--shallow-since` e processar em paralelo.

### 13.5 Janela de seleção do HL (P5)
Não confundir com a janela W de Q4 (90 dias após cada unidade, para observar retrabalho). A janela de seleção define **de que período vêm as PRs HL** de cada repositório.
- **Concorrente (padrão):** do 1º merge FA no repositório até o corte do AIDev. FA e HL vêm do mesmo momento do projeto. Problema: em repositórios que adotaram o agente perto do corte (ex.: `chaiNNer-org/chaiNNer`, 5 dias), sobram poucas PRs HL.
- **Ampliada:** começa 180 dias antes do 1º merge FA. Ganha ~3–5 repositórios e mais PRs HL por repositório, e o HL pré-adoção não convive com código de agente.
- **Riscos da ampliada:** (1) o projeto muda com o tempo (tamanho, complexidade, time, convenções, uso de IA pelos humanos); (2) em Q4, a chance de retrabalho depende do ritmo de atividade após o merge, que difere entre períodos, e código HL antigo pode ser retrabalhado pelos próprios agentes quando chegam; (3) antes da adoção, humanos faziam também as tarefas pequenas que depois foram para o agente — o mix de tarefas muda; (4) 180 dias é arbitrário (alternativa: janela simétrica ao período de atividade do FA).
- **Decisão (D20):** concorrente como regra principal; ampliada apenas como sensibilidade, com o mês do merge como covariável.

---

## 14. Amostra inicial (D17, D18, D19)
**Amostra consolidada: `docs/amostra.csv`** — 80 repositórios com status `incluido` ou `incluir_confirmar_hl` (24 Python, ~262 PRs FA; 56 JS/TS, ~954 PRs FA). Colunas adicionais: `familia` (`python`/`jsts`), `language`, `hl_prs_ampliado` (só JS/TS). Status possíveis: `incluido`, `incluir_confirmar_hl`, `incluir_se_hl_ampliado` (só se P5 adotar a janela ampliada), `excluido_hl_insuficiente`, `falha_api_404` (privado/apagado), `nao_adotado_s2`.

As subseções 14.1–14.4 listam a parte Python; a parte JS/TS está em 14.5.

Arquivo de origem (Python): `docs/amostra_s1.csv` (colunas `status`, `repo_id`, `full_name`, `stars`, `fa_prs_s1`, `fa_prs_s2`, `hl_prs_estimadas`, `primeiro_merge_fa`, `ultimo_merge_fa`). Contagens são **tetos** do spike; a Fase 1 aplica E3. "PRs HL estim." = PRs humanas mergeadas entre o 1º merge FA e o corte.

### 14.1 Incluídos (21)
| # | Repositório | Estrelas | PRs FA (S1) | PRs HL estim. | 1º → último merge FA |
|---|---|---|---|---|---|
| 1 | `crewAIInc/crewAI` | 39.711 | 29 | 629 | 2024-12-28 → 2025-08-20 |
| 2 | `reflex-dev/reflex-web` | 307 | 25 | 247 | 2025-04-29 → 2025-08-05 |
| 3 | `translate/translate` | 920 | 14 | 5 | 2025-10-17 → 2025-10-23 |
| 4 | `microsoft/lisa` | 313 | 13 | 178 | 2025-05-22 → 2025-10-21 |
| 5 | `jeroenterheerdt/HAsmartirrigation` | 457 | 13 | 13 | 2025-07-12 → 2025-08-12 |
| 6 | `Ljzd-PRO/KToolBox` | 461 | 10 | 7 | 2025-07-28 → 2025-08-08 |
| 7 | `NewFuture/DDNS` | 4.587 | 9 | 11 | 2025-07-02 → 2025-10-21 |
| 8 | `chaiNNer-org/chaiNNer` | 5.390 | 9 | 8 | 2025-10-19 → 2025-10-23 |
| 9 | `polarsource/polar` | 8.066 | 8 | 451 | 2025-09-05 → 2025-10-21 |
| 10 | `microsoft/fabric-cicd` | 181 | 8 | 64 | 2025-06-12 → 2025-10-13 |
| 11 | `AgentOps-AI/agentops` | 4.989 | 7 | 61 | 2025-06-15 → 2025-10-23 |
| 12 | `Azure/azure-sdk-for-python` | 5.372 | 7 | 1066 | 2025-06-10 → 2025-10-01 |
| 13 | `marimo-team/marimo` | 16.611 | 7 | 1911 | 2025-01-06 → 2025-09-10 |
| 14 | `microsoft/agent-framework` | 4.338 | 7 | 305 | 2025-09-19 → 2025-10-22 |
| 15 | `deepmodeling/deepmd-kit` | 1.776 | 6 | 18 | 2025-08-18 → 2025-09-19 |
| 16 | `mabel-dev/opteryx` | 109 | 6 | 25 | 2025-09-26 → 2025-10-11 |
| 17 | `xtekky/gpt4free` | 65.452 | 6 | 10 | 2025-08-21 → 2025-10-02 |
| 18 | `vlm-run/vlmrun-hub` | 537 | 6 | 53 | 2025-01-09 → 2025-03-02 |
| 19 | `QuantEcon/QuantEcon.py` | 2.218 | 5 | 8 | 2025-08-16 → 2025-09-15 |
| 20 | `NVIDIA/cuda-python` | 3.014 | 5 | 146 | 2025-08-21 → 2025-08-21 |
| 21 | `gerlero/foamlib` | 153 | 5 | 107 | 2025-08-30 → 2025-09-06 |

### 14.2 Incluir após confirmar HL — P4 (3)
Repositórios muito ativos cuja contagem de PRs humanas falhou ou saiu 0 por limite de páginas do script (já corrigido); certamente têm centenas de PRs humanas.

| # | Repositório | Estrelas | PRs FA (S1) | PRs HL estim. | 1º → último merge FA |
|---|---|---|---|---|---|
| 1 | `mlflow/mlflow` | 22.667 | 42 | — | 2025-05-27 → 2025-10-24 |
| 2 | `airbytehq/airbyte` | 19.888 | 10 | 0 | 2025-01-28 → 2025-09-29 |
| 3 | `BerriAI/litellm` | 30.336 | 5 | 0 | 2025-06-09 → 2025-10-12 |

### 14.3 Excluídos por HL insuficiente (7)
| # | Repositório | Estrelas | PRs FA (S1) | PRs HL estim. | 1º → último merge FA |
|---|---|---|---|---|---|
| 1 | `SkBlaz/py3plex` | 172 | 51 | 0 | 2025-08-05 → 2025-10-24 |
| 2 | `deepmodeling/dpgen` | 363 | 6 | 1 | 2025-09-03 → 2025-09-23 |
| 3 | `CravateRouge/bloodyAD` | 1.952 | 5 | 2 | 2025-10-08 → 2025-10-23 |
| 4 | `github/issue-metrics` | 503 | 5 | 4 | 2025-06-17 → 2025-09-29 |
| 5 | `disler/single-file-agents` | 409 | 5 | 0 | 2025-02-22 → 2025-03-18 |
| 6 | `Rudra-ravi/wikipedia-mcp` | 128 | 5 | 2 | 2025-07-22 → 2025-09-10 |
| 7 | `fqscfqj/Y2A-Auto` | 208 | 5 | 0 | 2025-08-22 → 2025-09-02 |

Alguns têm adoção tardia do FA (janela HL curta) e podem voltar se P5 adotar a janela HL ampliada.

### 14.4 Candidatos da ampliação S2 — opcional, P6 (8)
| # | Repositório | Estrelas | PRs FA (S1) | PRs HL estim. | 1º → último merge FA |
|---|---|---|---|---|---|
| 1 | `567-labs/instructor` | 11.704 | 3 | 71 | 2025-05-29 → 2025-10-01 |
| 2 | `jxxghp/MoviePilot` | 9.732 | 0 | 70 | 2025-07-05 → 2025-09-16 |
| 3 | `getsentry/sentry` | 42.304 | 0 | 0 | 2025-06-11 → 2025-10-16 |
| 4 | `mfat/sshpilot` | 595 | 0 | 34 | 2025-08-24 → 2025-10-11 |
| 5 | `browser-use/browser-use` | 71.814 | 0 | 621 | 2025-06-24 → 2025-10-24 |
| 6 | `openai/openai-agents-python` | 16.883 | 0 | 352 | 2025-05-21 → 2025-09-08 |
| 7 | `PrimeIntellect-ai/verifiers` | 3.384 | 0 | 121 | 2025-07-05 → 2025-10-18 |
| 8 | `OpenPipe/ART` | 7.697 | 0 | 188 | 2025-05-20 → 2025-06-26 |

### 14.5 JavaScript/TypeScript — incluídos (56)
| # | Repositório | Linguagem | Estrelas | PRs FA (S1) | PRs HL estim. |
|---|---|---|---|---|---|
| 1 | `liam-hq/liam` | TypeScript | 4.374 | 161 | 1247 |
| 2 | `theopenco/llmgateway` | TypeScript | 591 | 50 | 546 |
| 3 | `microsoft/genaiscript` | TypeScript | 2.825 | 40 | 7 |
| 4 | `intellectronica/ruler` | TypeScript | 1.935 | 38 | 53 |
| 5 | `firecrawl/firecrawl` | TypeScript | 64.982 | 37 | 406 |
| 6 | `calcom/cal.com` | TypeScript | 38.571 | 36 | 1569 |
| 7 | `microsoft/vscode` | TypeScript | 177.930 | 34 | 3343 |
| 8 | `dcSpark/shinkai-local-ai-agents` | TypeScript | 379 | 29 | 226 |
| 9 | `ioBroker/ioBroker.admin` | TypeScript | 276 | 29 | 50 |
| 10 | `epam/ketcher` | TypeScript | 664 | 27 | 41 |
| 11 | `streamich/memfs` | TypeScript | 1.967 | 25 | 14 |
| 12 | `manusa/electronim` | JavaScript | 239 | 23 | 40 |
| 13 | `antiwork/shortest` | TypeScript | 5.367 | 19 | 54 |
| 14 | `novuhq/novu` | TypeScript | 38.074 | 18 | 584 |
| 15 | `tokens-studio/figma-plugin` | TypeScript | 1.504 | 18 | 40 |
| 16 | `ryokun6/ryos` | TypeScript | 781 | 17 | 20 |
| 17 | `codeceptjs/CodeceptJS` | JavaScript | 4.191 | 17 | 55 |
| 18 | `reown-com/appkit` | TypeScript | 5.287 | 16 | 453 |
| 19 | `jina-ai/node-DeepResearch` | TypeScript | 4.952 | 16 | 21 |
| 20 | `pdfme/pdfme` | TypeScript | 3.713 | 15 | 39 |
| 21 | `different-ai/note-companion` | TypeScript | 736 | 15 | 15 |
| 22 | `lingodotdev/lingo.dev` | TypeScript | 3.495 | 14 | 147 |
| 23 | `pwa-builder/PWABuilder` | TypeScript | 3.313 | 13 | 15 |
| 24 | `microsoft/ApplicationInsights-JS` | TypeScript | 671 | 12 | 46 |
| 25 | `ohcnetwork/care_fe` | TypeScript | 566 | 12 | 271 |
| 26 | `NangoHQ/nango` | TypeScript | 5.991 | 12 | 1046 |
| 27 | `onlook-dev/onlook` | TypeScript | 23.002 | 11 | 992 |
| 28 | `neondatabase/website` | JavaScript | 274 | 11 | 711 |
| 29 | `digitaldemocracy2030/kouchou-ai` | TypeScript | 147 | 10 | 185 |
| 30 | `cloudflare/workers-sdk` | TypeScript | 3.530 | 10 | 374 |
| 31 | `yamadashy/repomix` | TypeScript | 19.921 | 10 | 162 |
| 32 | `promptfoo/promptfoo` | TypeScript | 8.825 | 9 | 2020 |
| 33 | `Voxelum/x-minecraft-launcher` | TypeScript | 1.176 | 9 | 6 |
| 34 | `microsoft/vscode-pull-request-github` | TypeScript | 2.481 | 9 | 442 |
| 35 | `primer/react` | TypeScript | 3.707 | 8 | 336 |
| 36 | `remotion-dev/remotion` | TypeScript | 24.341 | 8 | 257 |
| 37 | `team-mirai-volunteer/marumie` | TypeScript | 532 | 8 | 261 |
| 38 | `michaellatman/mcp-get` | TypeScript | 493 | 7 | 16 |
| 39 | `cybersemics/em` | TypeScript | 340 | 7 | 95 |
| 40 | `SwitchbackTech/compass` | TypeScript | 198 | 6 | 226 |
| 41 | `alchemy-run/alchemy` | TypeScript | 1.456 | 6 | 494 |
| 42 | `Azure/autorest.typescript` | TypeScript | 183 | 6 | 35 |
| 43 | `Azure/azure-sdk-for-js` | TypeScript | 2.242 | 6 | 730 |
| 44 | `zapier/zapier-platform` | JavaScript | 441 | 6 | 52 |
| 45 | `appsmithorg/appsmith` | TypeScript | 38.291 | 6 | 970 |
| 46 | `pyth-network/pyth-crosschain` | TypeScript | 216 | 6 | 574 |
| 47 | `haydenbleasel/ultracite` | TypeScript | 2.135 | 6 | 43 |
| 48 | `goat-sdk/goat` | TypeScript | 899 | 6 | 119 |
| 49 | `cornerstonejs/cornerstone3D` | TypeScript | 904 | 5 | 207 |
| 50 | `firebase/firebase-tools` | TypeScript | 4.251 | 5 | 217 |
| 51 | `browserless/browserless` | TypeScript | 11.666 | 5 | 45 |
| 52 | `vitejs/vite` | TypeScript | 76.185 | 5 | 147 |
| 53 | `bootstrap-vue-next/bootstrap-vue-next` | TypeScript | 1.239 | 5 | 17 |
| 54 | `fern-api/fern` | TypeScript | 3.377 | 5 | 138 |
| 55 | `samchon/typia` | TypeScript | 5.358 | 5 | 11 |
| 56 | `stack-auth/stack-auth` | TypeScript | 6.372 | 5 | 277 |

Demais candidatos JS/TS em `docs/amostra.csv`: excluido_hl_insuficiente: 12, nao_adotado_s2: 11, falha_api_404: 4, incluir_se_hl_ampliado: 3.
