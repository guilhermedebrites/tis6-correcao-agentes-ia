# Sabatina crítica da pesquisa (revisão imparcial da metodologia v3)

> **Data:** 12/10/2026 · **Status:** decisões do grupo registradas ao final · **Escopo:** ideia, novidade, confiabilidade, metodologia e factibilidade da pesquisa descrita em `docs/01-metodologia.md` (v3).
> **Postura:** revisor externo cético. Inclui crítica a decisões propostas pelo próprio assistente (D9–D13).
> **Para agentes de IA:** este documento lista riscos e recomendações **ainda não aprovadas**. Não altere a metodologia com base nele sem decisão do grupo.

## Veredito resumido
A pergunta é relevante e o desenho intra-repositório é sólido, mas **a pesquisa, como está, corre risco real de ser redundante e de ter o construto central (Fluxo Autônomo) medido com baixa confiabilidade**. Há quatro problemas críticos (C1–C4) que devem ser resolvidos antes do plano de implementação. A pesquisa é viável se for **reposicionada** (reconciliar evidências conflitantes sobre retrabalho, com controles que os trabalhos anteriores não usam), se a **unidade de análise mudar para a mudança integrada (PR)** e se um **spike de factibilidade** confirmar amostra suficiente.

---

## Críticos

### C1 — Novidade: o núcleo da pesquisa já foi publicado em 2026
| Trabalho | O que fez | Sobreposição com a nossa pesquisa |
|---|---|---|
| Rahman & Shihab, *Will It Survive?* (EASE 2026) | AIDev; repositórios com PRs de agente **e** humanas (comparação intra-repo); sobrevivência por linha via `git blame`; Kaplan-Meier, log-rank, Cox; intenção da modificação (Swanson) por palavras-chave; 201 repos, 24% Python | **Praticamente a nossa Q4.** Achado: código de agente **sobrevive mais** (HR 0,842), mas tem mais modificações corretivas (26,3% vs 23,0%); variação entre agentes > diferença agente-humano |
| Popescu et al., GitHub/TU Delft (arXiv 2604.00917, 2026) | ~112k PRs; sobrevivência, churn e deleção de linhas em 3 dias / 1 / 3 semanas | Q4. Achado **oposto**: código de agente sobrevive **menos**, com mais churn (efeitos pequenos) |
| *More Code, Less Reuse* (arXiv 2601.21276) | AIDev, **Python, > 500 estrelas**, **Radon** antes/depois (CC, raw) | **Nossas Q1 e Q3 com a mesma ferramenta.** Achado: diferenças mínimas; ~85% dos pares de arquivo com CC zero; o que diferencia é redundância semântica (1,87×) |
| Agarwal, He & Vasilescu (MSR 2026 Mining Challenge) | AIDev; diferenças-em-diferenças escalonadas; warnings estáticos, complexidade cognitiva, duplicação | Q1/Q2 em nível de repositório: +18% warnings, +39% complexidade cognitiva após adoção de agentes |
| *How AI Coding Agents Modify Code* (arXiv 2601.17581) | Estrutura de PRs de agentes vs. humanas | Q3 (tamanho, arquivos tocados) |

O AIDev foi o dataset do **MSR 2026 Mining Challenge**, então há dezenas de trabalhos sobre ele. O mapa de 15 artigos da apresentação não inclui nenhum desses.

**Recomendação:** reposicionar a contribuição. Em vez de "medir pela primeira vez", **reconciliar a contradição Rahman & Shihab × Popescu et al. em Q4**, mostrando se ela desaparece ao controlar o que eles não controlam: tipo de tarefa, tamanho, localização/"calor" do arquivo, modo de acionamento e nível de autonomia. A distinção FA × HL e o papel dos revisores de IA são a parte genuinamente nova.

### C2 — O construto FA depende da classificação menos confiável do estudo
- **Modo de acionamento (D10) não é observável no dado.** É inferido por sinais (autor bot, prefixo de branch, marca d'água). Popescu et al. relatam que o **Codex frequentemente commita sob a conta do humano** e que marcas d'água do Claude Code podem ser removidas.
- **Pureza da PR (D1) também quebra no Codex:** se os commits do agente saem com a conta do humano, "todos os commits são do agente" não pode ser verificado por autor. Uma edição humana na PR fica indistinguível.
- **Tensão de amostra:** o Codex é, de longe, o maior volume do AIDev. Excluí-lo por ambiguidade derruba a amostra; incluí-lo enfraquece o construto. Copilot coding agent, Devin e Jules têm sinais limpos (conta bot), mas volume menor.
- **Paradoxo:** a parte mais original da pesquisa (FA × HL) é exatamente a medida com mais erro.

**Recomendação:** (a) definir o FA principal **só com agentes de sinal limpo** (autor bot: Copilot coding agent, Devin, Jules); (b) Codex, Cursor e Claude Code em estrato "FA-provável" com análise de sensibilidade; (c) validar manualmente uma amostra e reportar precisão; (d) aceitar que o N do FA principal pode ser pequeno — o spike (C4) decide.

### C3 — Unidade de análise assimétrica entre os grupos
Agentes e humanos commitam em granularidades muito diferentes: agentes geram commits de plano, WIP e iterações (o 2601.17581 mostra que contagem de commits é a maior diferença entre os grupos, δ = 0,54). Comparar **commit a commit** mede o hábito de commitar, não o código. Além disso, D1 já faz do squash uma unidade-PR para o FA, enquanto o HL em repositórios com merge commit fica em nível de commit.

**Recomendação:** mudar a unidade para **mudança integrada** = diff líquido que a PR trouxe à branch principal (squash: o commit; merge commit: `merge^1..merge`; rebase: agrupar os commits da PR). Isso vale igualmente para FA e HL, elimina o viés de granularidade e combina com D12. Revisa D1 e E2.

### C4 — Factibilidade amostral desconhecida
Os filtros se acumulam: AIDev-pop → Python → PRs mergeadas → puras → acionamento *fila* → que tocam funções `.py` não-teste com ≥ 3 LLOC → ≥ 10 por grupo por repositório → janela W completa antes do corte. Agentes produzem desproporcionalmente PRs de Markdown, testes e docs (Popescu et al.), que E3 descarta. Rahman & Shihab chegaram a 201 repositórios **multilinguagem** com critérios mais frouxos; só 24% eram Python.

Não foi possível rodar a contagem nesta sessão (o Hugging Face está bloqueado no ambiente do assistente e o shell remoto do computador está indisponível).

**Recomendação:** antes de qualquer outra implementação, rodar um **spike de P1 Tier A** (horas, não dias) que produza o funil real por agente. Critério de go/no-go sugerido: ≥ 30 repositórios com ≥ 10 unidades por grupo no FA principal. Se não atingir, relaxar para FA-provável ou baixar N (com custo em poder estatístico).

---

## Sérios

### S1 — Q1–Q3 provavelmente medem tamanho, ou dão nulo
- Efeito chão: ~85% dos pares de arquivo com variação de CC zero (2601.21276).
- Halstead e MI são fortemente correlacionados com LOC; o MI é uma fórmula dos anos 1990 com validade contestada. "Diferença em MI" tende a ser "diferença de tamanho".
- Deltas com excesso de zeros violam pressupostos de modelos lineares mistos.

**Recomendação:** tratar Q1–Q3 como **secundárias/explicativas** (mecanismos para Q4); reportar a correlação de cada métrica com o tamanho; usar modelos para dados com zeros (hurdle/duas partes, ou baseados em ranks); considerar **complexidade cognitiva** e **duplicação/redundância**, que diferenciaram os grupos em trabalhos anteriores.

### S2 — Retrabalho ≠ qualidade, e a sobrevivência é confundida pela localização
- Código em arquivos periféricos (novos, pouco tocados, docs/testes) sobrevive mais por falta de oportunidade, não por qualidade. Código morto/não usado sobrevive para sempre. Essa é uma explicação plausível para Rahman & Shihab acharem que o código de agente sobrevive mais.
- Rahman & Shihab encontraram **violação de riscos proporcionais** em todas as covariáveis do Cox.

**Recomendação:** covariáveis de oportunidade (churn prévio do arquivo, arquivo novo, idade do arquivo, atividade do repositório após o merge); **análise no subconjunto de arquivos tocados por ambos os fluxos**; usar **RMST** (tempo médio de sobrevivência restrito) como medida principal de tempo, com o Cox como complemento.

### S3 — Viés de sobrevivência do merge
Só PRs mergeadas entram. As PRs do FA que chegam à branch já passaram por um filtro humano; as taxas de rejeição diferem muito entre agentes e entre FA e HL. O estudo mede **a qualidade do que passa pelo portão**, não a qualidade do fluxo.

**Recomendação:** assumir isso explicitamente no construto e no artigo; reportar a taxa de merge por grupo/agente como contexto.

### S4 — Confusão por alocação dentro do repositório
O pareamento por repositório controla o projeto, mas não **onde** no projeto cada fluxo trabalha. Se agentes recebem módulos periféricos, a diferença é de módulo. D11 (tipo de tarefa) ajuda, mas não resolve. A análise de arquivos compartilhados (S2) é o controle mais direto.

### S5 — Sem hipóteses e com muitos caminhos de análise
As QPs não têm hipóteses direcionais nem tamanho de efeito mínimo de interesse. Com 4 QPs × ~15 métricas × vários estratos e sensibilidades, há risco alto de *garden of forking paths*.

**Recomendação:** escrever hipóteses H1–H4, fixar **uma análise primária por QP** (métrica, modelo, população) antes de ver os dados e rotular o resto como exploratório. Um pré-registro leve (documento datado no repositório) basta.

---

## Moderados

- **M1 — Escopo vs. prazo.** D9–D13 acrescentaram classificação de acionamento, gradiente de autonomia, curadoria de revisores de IA, classificador de tarefa por LLM e duas validações manuais (~200 itens cada). Para um trabalho de disciplina, isso é pesado. Sugestão de núcleo mínimo: Q4 + FA principal (agentes de sinal limpo) + unidade-PR + controle de tamanho, tarefa e arquivo. Gradiente de autonomia e revisores de IA ficam como extensão.
- **M2 — Infraestrutura.** Blame em escala é caro (por commit posterior × arquivo) e exige cache e processamento incremental. O ambiente Windows de pelo menos um membro já mostrou problemas: padronizar em Linux/WSL/Docker. API do GitHub com limite de 5.000 req/h por token. Custo e não-determinismo do classificador LLM (fixar modelo, temperatura 0, guardar respostas). Repositórios podem ser apagados ou ter histórico reescrito: arquivar snapshots.
- **M3 — Citações a verificar.** A apresentação afirma que Li, Zhang & Hassan (2026) "validaram o mesmo recorte" (sem squash, mínimo por grupo); isso parece não corresponder ao paper do AIDev. Os números de Akbar & Anderies (~40%) e Ebiwonjumi et al. (6,1% / ~21%) devem ser conferidos na fonte primária.
- **M4 — Linguagem causal.** O desenho é observacional e a atribuição de tarefas não é aleatória: usar "associado a", não "causa".
- **M5 — Agentes mudam rápido.** A janela do AIDev cobre várias versões dos agentes. Incluir o mês do merge como covariável e discutir a validade temporal.
- **M6 — PRs humanas no AIDev.** Trabalhos anteriores usam uma amostra de PRs humanas do próprio AIDev (sem dados de commit). Verificar se a v4 a mantém; isso pode baratear D12 e R7.

---

## O que se sustenta bem
- Comparação intra-repositório com pareamento por repositório.
- Versão do dataset fixada e correção do vazamento pós-corte (D7).
- Tratamento explícito de squash com verificação de consistência.
- Separação P1/P2 com funil documentado.
- Controle por tipo de tarefa (D11): nenhum dos trabalhos comparáveis faz isso de forma explícita.
- Enquadramento do FA como sistema (autor + revisores de IA) e o "custo humano escondido" (D13), que são contribuições novas.

---

## Reposicionamento sugerido
**Título de trabalho:** "Autonomia reduz durabilidade? Uma comparação intra-repositório, controlada por tarefa e localização, entre desenvolvimento autônomo por agentes e desenvolvimento com humano no loop."
- **Primária:** Q4 (retrabalho/correção), com a contradição Rahman & Shihab × Popescu et al. como motivação.
- **Secundárias:** Q1–Q3 como mecanismos explicativos.
- **Contribuições:** construto FA × HL com modo de acionamento; controles de tarefa e localização; custo humano escondido; revisores de IA.

## Decisões do grupo (12/10/2026)
| Item | Decisão | Onde está registrado |
|---|---|---|
| C1 — Novidade / reposicionamento | Fragilidade registrada na metodologia. As quatro QPs são mantidas; a ênfase em Q4 (reconciliar Rahman & Shihab × Popescu et al.) será decidida após o piloto com uma amostra de repositórios. | Metodologia §1.6 e pendência P1 |
| C3 — Unidade | **Aceito:** unidade = PR integrada, para FA e HL, com justificativa escrita. | D14 |
| C2 — FA principal | **Aceito:** só agentes com conta própria de bot (Copilot coding agent, Devin, Jules); Codex, Cursor e Claude Code como FA-provável. | D15 |
| C4 — Spike | **Aceito como Fase 0 obrigatória**, com script pronto que roda em Windows. | D16; `docs/03-spike-factibilidade.md` |
| M1 — Escopo | Prazo curto: D9–D13 viram **refinamentos opcionais**. D12 já é absorvido por D14; D13 custa quase zero; D11 na versão *lite* é fortemente recomendado. | Metodologia §4.2 e §12 |
| S1–S5 | Ainda não decididos. | Metodologia §9, pendência P3 |

Nota sobre M6: a revisão atual do AIDev **não** traz `human_pull_request` nem `pr_task_type`; revisões anteriores trazem (metodologia §6.0, pendência P2).

## Fontes
- [Rahman & Shihab — Will It Survive? (arXiv 2601.16809)](https://arxiv.org/html/2601.16809)
- [Popescu et al. — Investigating Autonomous Agent Contributions in the Wild (arXiv 2604.00917)](https://arxiv.org/html/2604.00917v1)
- [More Code, Less Reuse (arXiv 2601.21276)](https://arxiv.org/html/2601.21276)
- [Agarwal, He & Vasilescu — AI IDEs or Autonomous Agents? (MSR 2026 Mining Challenge)](https://2026.msrconf.org/details/msr-2026-mining-challenge/29/AI-IDEs-or-Autonomous-Agents-Measuring-the-Impact-of-Coding-Agents-on-Software-Devel)
- [How AI Coding Agents Modify Code (arXiv 2601.17581)](https://arxiv.org/html/2601.17581)
- [AIDev no Hugging Face](https://huggingface.co/datasets/hao-li/AIDev)
