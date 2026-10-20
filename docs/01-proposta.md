# Nova proposta — Quem conserta o código dos agentes?

> **Data:** 19/10/2026 · **Status:** proposta v1, para discussão no grupo.
> **Base:** metodologia v7.1, docs 02–05 e o diagnóstico em `06-estado-e-proximos-passos.md`.
> **O que muda em relação ao trabalho anterior:** a pergunta central deixa de ser "o código de agente é diferente?" (quatro QPs paralelas) e passa a ser **a correção do código de agente: com que frequência acontece, quem a faz e em que PRs ela se concentra**. Complexidade e tamanho deixam de ser perguntas próprias e viram **fatores explicativos**. O construto, o dataset, a unidade e a maior parte da pipeline continuam.

---

## 1. Título de trabalho
**"Quem conserta o código dos agentes? Frequência, autoria e fatores da correção de código integrado por agentes autônomos de IA"**

Alternativa mais curta: *"O custo humano escondido do código gerado por agentes de IA"*.

O tema da disciplina, "Código gerado por agentes de IA: qualidade e taxa de correção", fica preservado: a taxa de correção vira o eixo, e a qualidade aparece como explicação.

---

## 2. Motivação (o argumento do artigo em cinco frases)
1. Agentes de IA já abrem e integram PRs sozinhos em repositórios reais (AIDev: ~2,74 M PRs de agentes, revisão de 24/10/2025).
2. A literatura discute se esse código **dura** mais ou menos (Rahman & Shihab: sobrevive mais; Popescu et al.: sobrevive menos), mas quase não pergunta **quem paga a conta** quando ele precisa ser corrigido.
3. Se a correção do código de agente recai sobre humanos, a "produtividade" do fluxo autônomo esconde um custo transferido para os mantenedores.
4. Nossos dados preliminares (12 repositórios Python) sugerem exatamente isso: **56% das linhas retrabalhadas de código de agente foram corrigidas por PRs humanas e só 6% pelo próprio fluxo autônomo**, e PRs pequenas de agente são retrabalhadas quase o dobro das humanas (0,36 × 0,19).
5. Medimos isso comparando, dentro do mesmo repositório, o código integrado pelo fluxo autônomo (FA) com o do fluxo com humano no loop (HL).

---

## 3. Objetivo (formato GQM)
**Analisar** o código integrado à branch principal por PRs de agentes autônomos de IA
**com o propósito de** caracterizar sua correção posterior
**com respeito a** frequência, autoria e fatores associados
**do ponto de vista de** mantenedores de projetos open source
**no contexto de** repositórios populares do GitHub (AIDev-pop) em que o fluxo autônomo convive com o fluxo humano.

---

## 4. Questões, hipóteses e métricas

### QP1 — Frequência: o código do fluxo autônomo é corrigido mais vezes?
*Com que frequência e em quanto tempo o código introduzido por PRs FA é corrigido, comparado ao código de PRs HL do mesmo repositório?*

| Métrica | Definição | Papel |
|---|---|---|
| `fix_rate_w` | linhas da PR alteradas ou removidas por eventos de **correção** em até W = 90 dias ÷ linhas adicionadas | **Primária** |
| `rework_rate_w` | o mesmo, para qualquer modificação (correção ou evolução) | Secundária |
| `has_fix` | 1 se ao menos uma linha foi corrigida em W | Secundária |
| Tempo até a 1ª correção | Kaplan-Meier, RMST até 90 dias, Cox | Estimativa complementar |

**H1:** a taxa de correção do código FA difere da do HL (bilateral; a literatura aponta nas duas direções).

### QP2 — Autoria: quem corrige o código do fluxo autônomo?
*Que fração das correções do código FA é feita por humanos, pelo próprio fluxo autônomo ou por outros agentes e bots, e isso difere do que acontece com o código HL?*

| Métrica | Definição | Papel |
|---|---|---|
| `human_fix_share` | das linhas corrigidas de uma PR, fração corrigida por PRs HL ou commits diretos | **Primária** |
| `self_fix_share` | fração corrigida pelo mesmo fluxo que a criou (FA corrigindo FA; HL corrigindo HL) | Secundária |
| `human_fix_excess` | `human_fix_share` observada − fração da atividade do repositório feita por humanos no mesmo período (linha de base) | Secundária: separa "humanos corrigem porque fazem quase tudo no repositório" de "humanos corrigem desproporcionalmente o código de agente" |
| Origem por categoria | HL · commit direto · FA · FA-provável · bot | Descritiva |

**H2:** a maior parte da correção do código FA é feita por humanos, acima do que a linha de base de atividade humana explica (`human_fix_excess` > 0).

> A linha de base é o ponto que torna a QP2 defensável: em quase todo repositório os humanos fazem a maioria das PRs, então "56% corrigido por humanos" sozinho não prova nada.

### QP3 — Fatores: em que PRs a correção se concentra?
*Quais características da PR estão associadas à correção, e a diferença FA × HL muda com elas?*

| Fator | Medida | Origem |
|---|---|---|
| Tamanho | `log(size_churn)` | E3 atual |
| Complexidade introduzida | `cc_delta_per_size`, `cc_after_max` | E4 atual (Radon / Lizard) |
| Tipo de tarefa | `feat / fix / refactor / docs / test / chore / outro` (D11-lite, **validado**) | E3b atual |
| Novidade | fração das linhas em arquivos novos | E4 atual |
| Oportunidade de correção | churn do arquivo nos 90 dias **anteriores** à PR | **Novo** (sabatina S2) |

**H3:** a diferença de correção entre FA e HL é maior em PRs pequenas (interação `fluxo × log(size_churn)` com sinal negativo), o que é consistente com tarefas pequenas delegadas ao agente sendo menos bem especificadas.

---

## 5. Árvore GQM

```
G: Caracterizar a correção do código integrado por agentes autônomos
│
├── QP1 Frequência ── fix_rate_w (primária) · rework_rate_w · has_fix · tempo até 1ª correção
│
├── QP2 Autoria ───── human_fix_share (primária) · self_fix_share · human_fix_excess · origem
│
└── QP3 Fatores ───── tamanho · complexidade · tipo de tarefa · novidade · oportunidade
                      (e interação fluxo × fator)
```

---

## 6. O que se aproveita, o que muda, o que sai

### 6.1 Aproveitado sem mudança
| Item | Referência |
|---|---|
| Construto FA × HL (fluxo, não autoria) | D0 |
| FA = Copilot coding agent, Devin, Jules (conta de bot) | D15, D19 |
| AIDev-pop na revisão fixada `7840b6e…`, corte 24/10/2025 | D5, D6, D7 |
| Unidade = PR integrada (diff líquido) | D14 |
| Amostra ≥ 5 FA e ≥ 5 HL válidas por repositório; janela HL concorrente | D17, D17-bis, D20 |
| Python + JS/TS | D18 |
| Pipeline P1 → P2 (classificação, filtros E3, consistência por contenção, recuperação de rebase) | doc 04 §7, doc 05 §3 |
| Rastreamento por `git blame -w -M -C` com origem do retrabalho (E5) | doc 05 §3.7 |
| Modelos por unidade (LMM/GEE/Cox robusto) como análise principal; Wilcoxon por repositório como confirmação; Holm em duas famílias | D17-bis, D21 |
| Resultados Python de 18/10 como **estudo piloto** do novo desenho | doc 05 |

### 6.2 Muda
| Antes | Agora | Por quê |
|---|---|---|
| Quatro QPs paralelas (Q1–Q4) | Três QPs, todas sobre correção | Foco e contribuição mais clara frente aos trabalhos de 2026 |
| Q4 primária = `rework_rate_w` | QP1 primária = `fix_rate_w` | O título fala em **correção**, não em qualquer modificação; retrabalho inclui evolução legítima (doc 05 §8) |
| Classificação de *fix* por palavras-chave, sem validação | **Classificação validada**: palavras-chave + prefixo `fix:` + rótulo `bug` da PR corretora (API do GitHub), conferida à mão em ~200 eventos, com kappa entre dois avaliadores | Passa a ser a medida central; precisa de precisão reportada |
| Origem do retrabalho como refinamento opcional (D13) | Origem vira a **QP2**, com linha de base de atividade | É o achado mais original dos dados atuais |
| Q1–Q3 como perguntas | Complexidade e tamanho como **fatores** da QP3 | Os dados mostraram que Q1–Q3 quase não diferenciam os fluxos e que as métricas brutas são quase só tamanho (doc 04 §2) |
| Primárias fixadas depois de ver dados | **Pré-registro** desta proposta antes de rodar JS/TS | Resolve a ressalva da D21 e a sabatina S5 |

### 6.3 Sai
| Item | Motivo |
|---|---|
| Maintainability Index (Q2 antiga) | Sem diferença, `mi_rank_drop` ≈ 0, validade contestada (sabatina S1); só existe para Python |
| Halstead | Fica só como exploratório em apêndice, se couber |
| Métricas de documentação (`comment_delta`, `doc_ratio_*`) | Não respondem nenhuma QP nova |

---

## 7. Desenho de análise

| QP | Modelo principal | Confirmação |
|---|---|---|
| QP1 | `fix_rate_w ~ fluxo + log(size_churn) + tipo_tarefa + oportunidade + modo + (1 \| repo)`; Cox robusto e RMST para o tempo | Wilcoxon pareado por repositório + Cliff's δ |
| QP2 | Proporções por fluxo com IC por bootstrap de repositórios; `human_fix_excess` testado contra 0 (modelo com efeito de repositório) | Teste por repositório do sinal de `human_fix_excess` |
| QP3 | Modelo da QP1 com interações `fluxo × fator`; foco pré-registrado em `fluxo × log(size_churn)` | — (exploratório, exceto H3) |

**Família confirmatória (Holm):** `fix_rate_w` (H1), `human_fix_excess` (H2), interação `fluxo × log(size_churn)` (H3). Todo o resto é exploratório.

**Sensibilidades:** só arquivos tocados pelos dois fluxos; janela W de 30 e 180 dias; sem os repositórios com > 30% de commits diretos (ex.: HAsmartirrigation, que concentra 425 das 461 linhas corrigidas por commit direto); limite de FA por repositório (concentração).

---

## 8. Contribuições esperadas
1. **Autoria da correção** do código de agentes, com linha de base de atividade, no lugar de só "sobrevive mais ou menos".
2. Comparação **dentro do mesmo repositório** e com o construto de **fluxo** (FA × HL), não autoria.
3. Classificação de correção **validada manualmente**, que os trabalhos comparáveis não reportam.
4. Controle de **oportunidade de correção** e de tipo de tarefa, apontado como lacuna nos estudos de 2026.

**A verificar antes de fechar o texto:** se algum trabalho de 2026 sobre o AIDev já mede quem corrige o código de agentes. Rahman & Shihab classificam a *intenção* da modificação, não a autoria; Popescu et al. medem churn. Isso precisa ser conferido na leitura.

---

## 9. Ameaças principais
- **Uso de IA no HL é invisível:** não dá para garantir que uma PR humana não usou IA (agente local, chat, autocompletar). Por isso o estudo compara **quem conduz** (D0), não "IA × humano": o HL inclui uso de IA por definição, e "corrigido por humanos" significa "corrigido em PRs conduzidas por humanos". Efeito esperado: aproxima os grupos e puxa para "sem diferença". Sensibilidade: HL sem as PRs com IA declarada (`ai_assist_declared`, 5,6% no Python).
- **Correção ≠ defeito:** mesmo validada, a classificação pelo título de PR erra; reportamos precisão e usamos `rework_rate_w` como sensibilidade.
- **Linha de base de atividade:** se humanos fazem 95% das PRs de um repositório, quase toda correção será humana por construção; por isso a primária da QP2 é o excesso sobre a linha de base.
- **Commits diretos:** atribuídos como "humanos" na QP2, mas podem incluir automações; checar autores e reportar à parte.
- **Seleção de tarefas:** agentes recebem tarefas diferentes; tipo de tarefa e tamanho são controlados, mas não eliminam a confusão. Linguagem associativa, não causal.
- **Herdadas do desenho anterior:** viés do merge, IA não declarada no HL (5,6% declaram), concentração em poucos repositórios, agentes recentes (jun–out/2025).

---

## 10. Plano de execução

| # | Etapa | Depende de | Entrega |
|---|---|---|---|
| 1 | Grupo discute e aprova esta proposta; congelar como **pré-registro** datado | — | Esta proposta v1.x, com data |
| 2 | Recalcular QP1 e QP2 com os dados Python **já existentes** (`out/diag`), incluindo a linha de base de atividade | 1 | Resultados piloto do novo desenho, sem rodar a pipeline de novo |
| 3 | Validação da correção: sortear ~200 eventos corretores, dois avaliadores por evento, kappa; ajustar a regra se a precisão for baixa | 1 | Tabela de precisão para o artigo |
| 4 | Adicionar à pipeline: rótulo `bug` via API (com cache), churn prévio do arquivo, linha de base de atividade | 3 | Pipeline v3 |
| 5 | Implementar JS/TS (`lang/jsts.py`, Lizard) e rodar P1 → P2 → E6 | 4 | Amostra completa (~40–50 repositórios esperados) |
| 6 | Artigo v1 com Python (etapas 2–3) e JS/TS como em andamento | 2, 3 | 1ª versão do artigo |
| 7 | Artigo final com a amostra completa | 5 | Artigo final |

Os passos 2, 3 e 6 não dependem de código novo pesado e cabem antes da entrega da 1ª versão do artigo. A divisão natural no grupo é: duas pessoas na pipeline (4–5), duas na validação manual (3) e duas no texto (6).

---

## 11. Decisões que o grupo precisa tomar
1. Aprovar o foco em correção e as três QPs.
2. Aprovar as três hipóteses e a família confirmatória (§7).
3. Definir quem faz a validação manual e quem implementa JS/TS.
4. Escolher o título.
