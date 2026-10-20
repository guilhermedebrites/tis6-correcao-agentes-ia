# Estado da pesquisa, inconsistências e próximos passos

> **Data:** 19/10/2026 · **Base:** pasta `docs/` do zip (metodologia v7.1, análise do piloto v1.2, resultados Python v2), slides de setembro e de 15/10, visão geral da disciplina.
> **Caráter:** consolidação e proposta. Nada aqui altera a metodologia; os itens marcados **[decisão do grupo]** precisam de aprovação antes de entrar no doc 01.

---

## 1. Onde a pesquisa está (em uma tela)

| Fase | Situação | Evidência |
|---|---|---|
| Escopo (marco 1) | Apresentado em setembro, com o enquadramento antigo (commit, autoria IA × humano) | `apresentacao.pdf` |
| Planejamento (marco 2) | Metodologia v7.1: construto FA × HL (D0), unidade PR integrada (D14), FA = Copilot/Devin/Jules (D15), Python + JS/TS (D18) | doc 01 |
| Fase 0 — spike | Concluída em 13/10. NO-GO pelo critério original; amostra refeita com ≥ 5/≥ 5 (D17) | doc 03 |
| Fase 1 — piloto v1 | 3 repositórios, 18 FA válidas. Apresentado como resultados preliminares (marco 3) em 15/10 | doc 04 §1–6, `anexo.pdf` |
| Pipeline v2 | R-P1, R-P3, R-P4, R-P5, R-P6 implementadas; R-P2 parcialmente rejeitada (D17-bis); Holm em duas famílias (D21) | doc 04 §7 |
| **1ª expedição Python** | **12 repositórios, 138 FA × 2.500 HL**, executada em 18/10 | doc 05 |
| JS/TS | **Não implementado** (`lang/jsts.py`). É onde está a maior parte da amostra planejada (56 de 80 repositórios) | doc 05 §9 |
| **Próximo marco da disciplina** | **Entrega da 1ª versão do artigo final (15 pontos)** | visão geral TI6 |

### O que os dados dizem hoje (Python, 12 repositórios)
- **Q3:** PRs FA são menores (−30 linhas lógicas, p Holm 0,0017), robusto a tirar um repositório por vez. Crescem o código tanto quanto as HL (`lloc_delta` sem diferença), ou seja, **removem e reescrevem menos código existente**.
- **Q1, Q2:** sem diferença detectável nas primárias. Sinal exploratório em Halstead (FA maior), que pode ser ajuste incompleto por tamanho.
- **Q4:** **inconclusivo**. O HR do piloto (0,56, "agente sobrevive mais") virou 1,17 (IC 0,80–1,71) com 138 FA. Falta poder.
- **Exploratórios que valem hipótese:** código FA retrabalhado é corrigido quase sempre por humanos (56% por PRs HL, 6% pelo próprio agente); em PRs de até 10 linhas, o retrabalho FA é quase o dobro do HL (0,36 × 0,19).

---

## 2. Inconsistências entre os documentos

### 2.1 Versões
| # | Problema | Ação |
|---|---|---|
| I1 | Os arquivos `01-metodologia.md` e `04-analise-piloto.md` enviados soltos são **versões antigas** (v7 e v1). As atuais (v7.1 e v1.2) estão no zip. | Usar só o zip como fonte; descartar as cópias soltas |

### 2.2 A metodologia (doc 01) ficou atrás da pipeline
O doc 05 descreve o que a pipeline **realmente faz**; o doc 01 ainda descreve o plano anterior. Quem ler só o doc 01 (inclusive a banca, se ele virar a seção de método) vai encontrar um método diferente do executado.

| # | Doc 01 diz | O que foi executado (doc 05) | [decisão do grupo] |
|---|---|---|---|
| I2 | D2 e E6: **análise principal = Wilcoxon** por repositório; modelo misto é complemento | D17-bis e doc 05 §3.8: **principal = modelos por unidade**; Wilcoxon é confirmação | Reescrever D2 (contradição interna do §4.1) |
| I3 | E2: consistência FA = arquivos e linhas "batem com tolerância" | **Contenção ≥ 0,8** sobre arquivos considerados, sem merges de sincronização (R-P1) | Registrar como decisão (ex.: D22) |
| I4 | E2 e §7: PRs por **rebase são excluídas** no núcleo | Rebase **recuperado**: FA pelos commits do AIDev; HL pela API quando > 30% sem marcação (R-P3) | Registrar (D23) e atualizar a ameaça "Rebase" |
| I5 | §6.4.3: primárias = `cc_delta_sum`, `mi_delta_mean`, `lloc_delta` | Primárias = `cc_delta_per_size`, `mi_delta_mean`, `size_churn`, `lloc_delta`, `rework_rate_w` (R-P5, já citadas em D21) | Corrigir a coluna "Primária" da tabela |
| I6 | §6.4.3: `log(size_churn)` como covariável em **todas** as métricas | Q3 **sem** ajuste por tamanho (R-P4) | Registrar (D24) |
| I7 | D11 (tipo de tarefa) é **opcional** | D11-lite **já está nos modelos** como covariável (R-P6), sem validação | Registrar como núcleo (D25) + validar (V2-4) |
| I8 | E6: LMM + **logística mista** + **Cox com frailty** | **GEE** para binárias e **Cox com variância robusta** por repositório | Registrar a troca no doc 01 |
| I9 | §10: proporção mínima de código da família = 60% | Parâmetro existe mas **não é aplicado** (`mlflow` tem 44% e está na análise) | Aplicar (mlflow sai) ou remover o parâmetro |
| I10 | §1.5 "repositórios Python"; §7 "~21–24 repositórios"; §10 "teto: até 24"; §14 "80 repositórios" | Python válido: **12**; projeção JS/TS: 28–37 (doc 04 §4.1, conversão de 47–65%; com os 75% do doc 05 seria mais) | Atualizar números e §1.5 |
| I11 | Ferramenta: Python 3.13 (slides de 15/10) | Executado com **Python 3.14.3** | Só registrar |

### 2.3 Status das recomendações R-P
O cabeçalho do doc 04 ainda diz que R-P1…R-P8 **não estão aprovadas**, mas a §7 mostra cinco delas implementadas e usadas nos resultados do doc 05. Hoje só D17-bis e D21 estão registradas no doc 01. **A situação real é:**

| R-P | Situação real |
|---|---|
| R-P1 contenção | Implementada e usada (0 exclusões; rendimento FA 47% → 75%) — falta decisão registrada |
| R-P2 mínimos | Parte "≥ 1 FA" **rejeitada** (D17-bis); parte "modelo por unidade é o principal" **em uso** — falta corrigir D2 |
| R-P3 rebase | Implementada e usada — falta decisão registrada |
| R-P4 Q3 sem ajuste | Implementada e usada — falta decisão registrada |
| R-P5 primárias | Implementada; usada em D21 — falta corrigir §6.4.3 |
| R-P6 tipo de tarefa | Implementada como covariável — falta decisão e validação |
| R-P7 JS/TS primeiro | **Não feita** (Python rodou inteiro antes) |
| R-P8 reenquadrar amostra | Sem decisão; o doc 05 já trata Python como subamostra |

### 2.4 Os slides estão superados
| # | Problema | Consequência para o artigo |
|---|---|---|
| I12 | `apresentacao.pdf` (set.) fala em **commit a commit**, **autoria IA × humano**, repositórios **sem squash** e 932.791 PRs / 116.211 repositórios | Tudo isso foi substituído por D0, D1, D14 e pela revisão fixada do AIDev (~2,74 M PRs, ~327 mil repositórios). A introdução do artigo não pode reaproveitar esses slides |
| I13 | `anexo.pdf` (15/10) afirma "**o código de agente sobreviveu mais**" e usa `cc_delta_sum` como primária | Com 138 FA, Q4 é inconclusiva (HR 1,17). Essa frase **não pode ir para o artigo**; vale como exemplo de por que o piloto não era resultado |
| I14 | Os slides listam 15 artigos e nenhum dos trabalhos de 2026 sobre o AIDev (sabatina C1) | O trabalho relacionado precisa incluir Rahman & Shihab, Popescu et al., *More Code, Less Reuse*, Agarwal et al. e 2601.17581 |
| I15 | Citações a conferir (sabatina M3): "Li, Zhang & Hassan validaram o mesmo recorte", Akbar & Anderies (~40%), Ebiwonjumi et al. (6,1% / 20,8% ou ~21%) | Conferir na fonte antes de entrar no texto; os próprios docs divergem entre 20,8% e ~21% |

---

## 3. Lacunas de método que ainda importam

| # | Lacuna | Por que importa | Custo |
|---|---|---|---|
| L1 | **Q4 sem poder** com Python sozinho | É a pergunta central (e o enquadramento P1 de "reconciliar Rahman × Popescu" depende dela) | JS/TS (médio) |
| L2 | **Pré-registro**: as primárias foram fixadas depois do piloto (ressalva da D21) | O JS/TS é a chance de ter uma análise confirmatória limpa: basta fixar hipóteses e primárias **num documento datado antes de rodar** | Muito baixo |
| L3 | Tipo de tarefa não validado (V2-4) | É o principal confundidor do resultado de Q3 ("o agente recebe tarefas menores") | Baixo: rotular 50–100 títulos à mão, reportar kappa |
| L4 | Oportunidade de retrabalho (sabatina S2) não controlada | Código em arquivo pouco tocado "sobrevive" por falta de chance; é a explicação alternativa mais forte para qualquer resultado de Q4 | Baixo-médio: covariável de churn prévio do arquivo, ou análise só em arquivos tocados pelos dois fluxos |
| L5 | Deltas com excesso de zeros (sabatina S1) | LMM sobre `cc_delta_per_size` com muitos zeros viola pressupostos | Baixo: checar e, se preciso, reportar modelo de duas partes como sensibilidade |
| L6 | Concentração (3 repositórios = 50% das FA em Python; `liam-hq/liam` = 17% das FA de JS/TS) | Um projeto pode dominar o modelo | Baixo: limitar FA por repositório (P7) como sensibilidade |
| L7 | `ai_assist_declared` só 5,6% do HL | Puxa para "sem diferença"; deve aparecer como ameaça e como sensibilidade | Baixo |

---

## 4. Recomendação

**O tangível agora é a 1ª versão do artigo**, que é o próximo marco da disciplina (15 pontos) e já tem material suficiente: método executado, funil, resultados Python e uma narrativa honesta (PRs de agentes são menores e mexem menos no código existente; em qualidade e retrabalho, sem diferença detectável com o N atual). O JS/TS entra como "em andamento" e completa a versão final.

Ordem proposta:

| # | Passo | Quem decide / faz | Entrega |
|---|---|---|---|
| 1 | **Fechar a metodologia v7.2**: registrar R-P1, R-P3, R-P4, R-P6 como decisões, corrigir D2, §6.4.3, E2, E6, §7, §10 (itens I2–I10) | **[decisão do grupo]**; o texto pode ser preparado como proposta | doc 01 v7.2 coerente com o que foi executado (e que vira a seção de método do artigo) |
| 2 | **Pré-registro curto para JS/TS** (H1–H4 direcionais, primárias, modelo, população), datado, antes de rodar | Grupo aprova; texto em 1 página | Resolve a ressalva da D21 e a sabatina S5 |
| 3 | **Artigo v1** com a estrutura: introdução (contradição Rahman × Popescu), construto FA × HL, método, funil, resultados Python, ameaças, trabalho em andamento (JS/TS) | Rascunho pode começar já | 1ª versão do artigo |
| 4 | Implementar `lang/jsts.py` e rodar (R-P7, V2-6) | Quem mantém a pipeline | Resultados JS/TS para o artigo final |
| 5 | Rotular 50–100 títulos para validar o tipo de tarefa (V2-4) | Divisão entre os 6 membros (~15 títulos cada) | Kappa no artigo |
| 6 | Decidir P1 (ênfase em Q4) **depois** do JS/TS | Grupo | Enquadramento final |

**Por que essa ordem:** os passos 1–3 não dependem de código novo e garantem a nota do próximo marco; o passo 4 é o único que pode mudar a conclusão de Q4, mas é o mais caro e incerto, então não deve bloquear o artigo.
