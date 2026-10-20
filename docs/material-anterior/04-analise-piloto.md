# Análise do piloto (Fase 1) — pipeline Python

> **Data:** 14/10/2026 · **Base:** `tisl_pipeline/fa_hl_pipeline/fa_hl` (execução de 15/10/2026 01:52–02:01 UTC), metodologia v7.
> **Status:** v1.2 (18/10: revisão da v2 da pipeline em §7). **A execução completa da v2 nos repositórios Python está em `05-resultados-python.md`**; ela substitui os números do piloto v1 (§2) e fecha V2-2 e V2-5. Itens marcados **[a confirmar]** dependem do diagnóstico `diagnostico.bat` (exporta os `.parquet` para CSV e monta o destino de cada PR FA).
> **Para agentes de IA:** este documento avalia a viabilidade do plano com dados reais. As recomendações (R-P1…R-P8) **não** estão aprovadas; não altere a metodologia sem decisão do grupo.

## 1. O que foi executado
- P1 completa sobre os 24 repositórios Python da amostra (23 com ≥ 5 PRs FA elegíveis no AIDev; 257 PRs FA elegíveis).
- P2 + E6 em 3 repositórios do piloto: `crewAIInc/crewAI`, `microsoft/lisa`, `gerlero/foamlib`. Tempo total ~7 min.
- Implementação segue o núcleo (§4.1) com fidelidade: unidade = PR integrada, leitura por `git show` em SHAs fixos, Radon 6.0.1, blame `-w -M -C`, versões e parâmetros no manifesto, testes automatizados. Escolhas próprias documentadas no README (p99 `higher`, closures somadas à função externa, GEE e Cox robusto no lugar de modelos com frailty).

## 2. Resultados do piloto
| Repositório | Modo de integração | PRs FA classificadas | FA válidas | HL válidas | Incluído |
|---|---|---|---|---|---|
| crewAIInc/crewAI | squash | 33 | 9 | 220 | sim |
| microsoft/lisa | squash (+ ~69% dos eventos por rebase/direto) | 22 | 9 | 56 | sim |
| gerlero/foamlib | merge commit | 5 | 4 | 41 | não (FA < 5) |

Leitura preliminar (n = 18 FA, 2 repositórios — **não é resultado**, só sinal de que as medidas funcionam):
- **Q4:** sobrevivência sem retrabalho em 90 dias 0,61 (FA) × 0,34 (HL); Cox HR = 0,56 (IC 0,23–1,34) para retrabalho e 0,49 (IC 0,24–1,01) para *fix*. Mesma direção de Rahman & Shihab (código de agente sobrevive mais). Há eventos suficientes para Q4 (39% das FA e 66% das HL têm retrabalho em 90 dias).
- **Tamanho:** PRs FA são menores (mediana `size_churn` 25 × 45; 1 × 2 arquivos; LMM: −48 linhas, IC −89 a −6, p bruto = 0,02, **p de Holm = 0,40**). Indício, não resultado; reforça o risco de confusão por tipo/tamanho de tarefa.
- **Q1–Q3:** métricas brutas fortemente correlacionadas com o tamanho (`cc_delta_sum` ρ = 0,62; `lloc_delta` ρ = 0,63); as normalizadas por tamanho, quase não (`cc_delta_per_size` ρ = 0,09; `lloc_delta_per_size` ρ = 0,02).
- **Q2:** `mi_rank_drop` ≈ 0 em todos os grupos (0% FA, 0,7% HL) e `mi_worsened` ≈ 75% nos dois — pouco informativas.

## 3. Viabilidade: o que se sustenta
1. **A pipeline é viável e barata:** 1–5 min por repositório; a amostra completa (~80 repositórios) roda em poucas horas (exceto gigantes como `microsoft/vscode`).
2. **O construto FA funciona:** autoria por conta de bot e pureza pelo AIDev se confirmaram no git (99,6% das linhas retrabalhadas batem com linhas adicionadas pela PR de origem, no teste do autor da pipeline).
3. **Q4 é mensurável** e tem eventos suficientes; a medição de Q1–Q3 por estados B/A funciona como descrito em §E4.
4. **O HL é abundante** (centenas de PRs por repositório grande).

## 4. Viabilidade: o que não se sustenta como planejado
### 4.1 Perda de PRs FA entre o spike e as unidades válidas
De 47 PRs FA elegíveis no spike (crewAI 29, lisa 13, foamlib 5), restaram **22 unidades válidas (47%)**; no crewAI, 31%. Motivos no funil agregado (FA + HL): `inconsistente_com_pr_commit_details` 19 (só se aplica a FA), `fa_mista` 19 (já fora das elegíveis), `sem_arquivo_considerado` 257, `nenhuma_funcao_tocada` 74, `fa_nao_encontrada_no_historico` 5.

**Confirmado no código:** a lista de arquivos da PR usada na consistência (`agent_pr_files`) só é montada para PRs FA **elegíveis**; logo, as **19 exclusões por Jaccard são todas de PRs elegíveis** — cerca de 40% das 47, a maior causa isolada de perda. Essa lista soma os arquivos de **todos** os commits da PR no `pr_commit_details`, inclusive commits de sincronização (`Merge branch 'main' into …`), que trazem para a lista arquivos alterados na `main` e não pela PR.

**Hipótese sobre o mecanismo [a confirmar com o diagnóstico]:** a verificação de consistência usa **Jaccard** entre os arquivos da unidade (diff líquido) e os arquivos tocados por *qualquer* commit da PR no AIDev. PRs de agentes mexem em arquivos e desfazem dentro da própria PR (planos, tentativas), então o conjunto do AIDev é maior que o diff líquido e o Jaccard cai abaixo de 0,5 mesmo quando a unidade é a PR certa. O teste correto é de **contenção**: os arquivos da unidade devem estar contidos nos arquivos da PR.

**Projeção para a amostra inteira** (aplicando a taxa de conversão às PRs elegíveis do spike, com mínimo de 5 FA válidas por repositório):

| Conversão FA | Repositórios Python | Repositórios JS/TS | PRs FA em repositórios incluídos |
|---|---|---|---|
| 31% (como no crewAI) | 3 | 17 | ~220 |
| **47% (piloto)** | **6** | **28** | **~430** |
| 65% (se a consistência for corrigida) | 12 | 37 | ~670 |
| 80% | 16 | 39 | ~860 |

A amostra de ~80 repositórios da metodologia **não se mantém**: a estimativa realista hoje é de **~35–50 repositórios**, quase todos TypeScript. Python sozinho fica pequeno demais para conclusões próprias.

### 4.2 Rebase invisível
Em `microsoft/lisa`, ~69% dos eventos de 1º pai não têm marcação de PR (rebase ou push direto). O núcleo os trata como "commit direto": o HL perde PRs humanas reais e a origem do retrabalho fica mal atribuída (afeta o "custo humano escondido", D13). Q4 em si (houve ou não retrabalho) não é afetada.

### 4.3 Especificação de E6
- **Q3 ajustado por tamanho:** o modelo inclui `log(size_churn)` como covariável também para `lloc_delta`, `n_files` e `n_funcs_*`, que são medidas de tamanho; isso ajusta o desfecho por ele mesmo. Q3 deve ser modelado sem essa covariável.
- **Métricas primárias:** as brutas de Q1/Q3 são quase só tamanho (ver §2).

## 5. Recomendações
| ID | Recomendação | Impacto | Custo |
|---|---|---|---|
| R-P1 | **Trocar Jaccard por contenção** na consistência FA: `|arquivos_unidade ∩ arquivos_PR| / |arquivos_unidade| ≥ 0,8`; montar `agent_pr_files` **sem** os commits de sincronização (mesmo filtro `SYNC_MERGE` já usado na pureza). | Pode recuperar boa parte das 19 FA perdidas (até ~87% de conversão se todas forem falsos negativos) | Baixo (2 linhas) |
| R-P2 | **Desacoplar o mínimo por repositório:** modelos por unidade (LMM/GEE/Cox) usam todo repositório com ≥ 1 FA e ≥ 5 HL válidas; o Wilcoxon por repositório usa só os com ≥ 5/≥ 5. Tornar o **modelo por unidade a análise principal** (já sugerido em §13.3). | Recupera FA de repositórios como `foamlib` (4 FA) | Baixo |
| R-P3 | **Rebase:** para repositórios com > 30% de eventos sem marcação, mapear commits → PRs pela API (`GET /repos/{o}/{r}/commits/{sha}/pulls`, 1 consulta por commit, com cache) — ou, no mínimo, registrar a proporção como covariável e excluir de D13. | HL e origem corretos em repositórios como `lisa` | Médio |
| R-P4 | **Q3 sem ajuste por tamanho** no modelo (manter para Q1, Q2 e Q4). | Corrige especificação | Baixo |
| R-P5 | **Métricas primárias (P3):** Q1 `cc_delta_per_size`; Q2 `mi_delta_mean` (manter, mas sem `mi_rank_drop`); Q3 `size_churn` e `lloc_delta` sem ajuste; Q4 `rework_rate_w` + Cox/RMST. | Evita "medir tamanho" | Nenhum |
| R-P6 | **Ativar D11-lite (tipo de tarefa)** pelo título da PR: as PRs FA são sistematicamente menores. | Controle do principal confundidor | Baixo |
| R-P7 | **Implementar JS/TS antes de rodar Python inteiro:** a amostra depende principalmente de TypeScript. | Viabiliza o N | Médio |
| R-P8 | **Reenquadrar a amostra:** "Python + TypeScript, com Python como subamostra" — evitar conclusões separadas por linguagem sem N suficiente. | Escrita do artigo | Nenhum |

## 6. Próximos passos
1. Rodar `diagnostico.bat` (em `fa_hl`) e confirmar a causa da perda de FA (§4.1).
2. Aplicar R-P1, R-P2 e R-P4 e reprocessar os 3 repositórios do piloto.
3. Implementar `lang/jsts.py` (R-P7) e rodar o piloto TypeScript (`theopenco/llmgateway`, `intellectronica/ruler`, `tokens-studio/figma-plugin`).
4. Com as duas famílias no piloto, recalcular a projeção da amostra e fixar as métricas primárias (P3).

## 7. Revisão da v2 da pipeline (18/10/2026)
Revisão do código de `fa_hl` alterado em 18/10. **Os resultados em `out/` ainda são da v1 (15/10)**: a v2 não foi executada, então os números deste documento continuam valendo até a nova rodada.

### 7.1 O que foi implementado
| Recomendação | Implementação | Avaliação |
|---|---|---|
| R-P1 contenção | Contenção ≥ 0,8 só sobre arquivos considerados; P1 tira merges de sincronização da lista de arquivos da PR | Correta. O autor confirmou no crewAI: 16 de 27 PRs FA caíam pelo Jaccard; com contenção, 22 FA válidas (antes 9) |
| R-P2 mínimos desacoplados | Modelos viram a análise principal. **A parte que aceitava ≥ 1 FA nos modelos foi rejeitada pelo grupo (D17-bis, 18/10):** o mínimo de ≥ 5 FA e ≥ 5 HL vale para tudo; `config.py` e testes ajustados (`min_fa_units_models = p1_min_fa_eligible = 5`). P1 pode selecionar todos os repositórios Python do AIDev-pop com ≥ 5 FA elegíveis (`--source aidev`) | Implementado conforme a decisão. A ampliação além dos 24 da §14 é decisão nova (ver 7.2) |
| R-P3 rebase | FA rebaseadas recuperadas pelos commits do AIDev (SHA ou mensagem, ±3 dias, bloco contíguo); HL rebaseadas pela API com cache, só com `GITHUB_TOKEN` e > 30% de eventos sem marcação; `unmarked_ratio` registrado | Correta e bem testada |
| R-P4 Q3 sem ajuste por tamanho | Implementado | Correto |
| R-P5 primárias | Q1 `cc_delta_per_size`; Q2 `mi_delta_mean`; Q3 `size_churn` + `lloc_delta`; Q4 `rework_rate_w` + Cox + RMST até 90 dias; `mi_rank_drop` fora | Correto |
| R-P6 tipo de tarefa | D11-lite pelo título, covariável nos modelos e no Cox | Correto; heurística ainda não validada |
| Bônus | Diagnóstico das causas da perda: P1 contava linhas de merges de sincronização e inflava as "elegíveis" | Achado importante: parte da "perda" era inflação na contagem do spike |

### 7.2 Pontos ainda a ajustar
| ID | Ponto | Recomendação | Custo |
|---|---|---|---|
| V2-1 | **[implementado em 18/10 — D21]** **Holm ainda corrige sobre todas as métricas da QP** (17 na Q3), inclusive as exploratórias. Com primárias definidas (R-P5), a família confirmatória é só a das primárias. | Holm sobre as 5 primárias (família confirmatória); secundárias com Holm separado, rotuladas como exploratórias. Resolve o "p 0,02 → 0,40" do tamanho. | Baixo |
| V2-2 | **Contenção é uma checagem mais frouxa de identidade.** Um commit `(#N)` que não seja a PR #N passaria se tocar arquivos em comum. | Exigir também `|data do commit A − merged_at do AIDev| ≤ 3 dias` para FA por squash/merge (a mesma regra já usada no rebase). | Baixo |
| V2-3 | **Ampliação da amostra (`--source aidev`)** não está registrada como decisão. Com D17-bis, ela inclui os repositórios Python do AIDev-pop com ≥ 5 FA elegíveis, além dos 24 da §14 (a contagem de elegíveis mudou após tirar os merges de sincronização). | Registrar como decisão (D22) e rodar P2 em todos; custo estimado de horas (clones). | Nenhum |
| V2-4 | **Tipo de tarefa sem validação.** Agora é covariável nos modelos. | Rotular manualmente ~50–100 títulos (FA e HL) e reportar a concordância. | Baixo (manual) |
| V2-5 | **HL rebaseado depende de `GITHUB_TOKEN`.** Sem token, `microsoft/lisa` e similares continuam com HL subcontado. | Rodar a Fase 2 com token. | Nenhum |
| V2-6 | **JS/TS (R-P7)** continua pendente e é a maior alavanca de N. | Implementar `lang/jsts.py` antes da Fase 2 completa. | Médio |

### 7.3 Próximo passo
Rodar a v2 no piloto (`python -m pipeline piloto --workers 3`, com `GITHUB_TOKEN`) e depois `python -m pipeline e6`, para confirmar o ganho de FA válidas e reavaliar a projeção da amostra (§4.1).

