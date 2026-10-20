# Fase 0 — Spike de factibilidade (P1 Tier A)

> **Objetivo:** descobrir, antes de construir a pipeline principal, se existem repositórios suficientes no AIDev para o estudo FA × HL (decisão D16 em `docs/01-metodologia.md`).
> **Esforço:** ~30–60 min, a maior parte esperando o download (~1,5 GB). Não exige Linux: roda em Windows, macOS ou Linux.
> **Arquivos:** `scripts/spike_aidev.py` e `scripts/requirements.txt` (no projeto e na pasta `tis/spike` do Pedro).

---

## 1. Por que isto é necessário

A metodologia empilha vários filtros (sabatina, item C4):

AIDev-pop → repositório Python → PR mergeada → antes do corte − 90 dias → agente do FA principal (Copilot, Devin, Jules) → PR pura → toca `.py` de produção → ≥ 10 PRs por repositório → ≥ 10 PRs humanas no mesmo período.

Agentes produzem muitas PRs só de docs, Markdown e testes, que o estudo descarta. Um trabalho comparável (Rahman & Shihab, 2026) chegou a 201 repositórios **em todas as linguagens** com filtros mais frouxos, e só 24% eram Python. **Não sabemos se sobram repositórios suficientes.** Se não sobrarem, é melhor descobrir agora, antes de implementar clone, Radon e `git blame`.

O spike também entrega dados úteis para o artigo: o **funil de seleção** e o **perfil empírico de cada agente** (quem aparece como autor das PRs e dos commits), que valida a decisão D15.

## 2. O que o script faz

`spike_aidev.py` usa **só os metadados do AIDev** (nenhum clone de repositório):

1. Baixa do Hugging Face, numa revisão fixa, 4 tabelas: `repository`, `pull_request`, `pr_commits`, `pr_commit_details`. Registra o SHA da revisão (D5).
2. Gera `schema.md`, com as colunas e exemplos de cada tabela.
3. Gera `perfil_agentes.md`: valores da coluna `agent` e, por agente, os autores mais frequentes das PRs e dos commits.
4. Aplica o funil de E1 Tier A, separado para **FA principal** (Copilot, Devin, Jules) e **FA-provável** (Codex, Cursor, Claude Code).
5. Conta quantos repositórios têm ≥ 5, 10 e 20 PRs elegíveis.
6. *(Opcional, com token do GitHub)* Estima quantas PRs humanas mergeadas cada repositório candidato teve no mesmo período (API de busca do GitHub), descontando bots comuns e as PRs de agentes.
7. Escreve `relatorio.md` com o veredito **GO / NO-GO**.

**Saídas** (pasta `out/`): `relatorio.md`, `funil.csv`, `repos_candidatos.csv`, `perfil_agentes.md`, `schema.md`, `run_info.json`.

## 3. Passo a passo

> **Atalho no Windows:** dê dois cliques em `rodar_spike.bat` (na pasta `tis\spike`). Ele faz os passos 3.2, 3.3 e 3.5 sozinho: acha o Python, cria o `.venv`, instala as dependências, pergunta o token do GitHub (opcional, não fica salvo), baixa os dados na primeira vez e roda. O log fica em `out\spike_log.txt`. Os passos manuais abaixo continuam valendo para macOS/Linux ou para depurar.

### 3.1 Pré-requisitos
- Python 3.10 ou superior (`python --version`).
- ~3 GB livres em disco e internet estável.
- *(Opcional, para a estimativa do HL)* um token do GitHub. Um *fine-grained token* sem nenhuma permissão extra basta, porque só lê dados públicos: GitHub → Settings → Developer settings → Personal access tokens.

### 3.2 Preparar o ambiente
**Windows (PowerShell)**, dentro da pasta onde estão `spike_aidev.py` e `requirements.txt`:
```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass   # só se a ativação abaixo for bloqueada
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
**macOS/Linux:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 3.3 Primeira execução (baixa e roda)
```powershell
python spike_aidev.py --download
```
- Baixa ~1,5 GB para `data/aidev/` (o `pr_commit_details` sozinho tem ~1,3 GB). Isso só acontece na primeira vez.
- Para reproduzir exatamente uma execução anterior, use `--revision <SHA>` com o SHA registrado em `out/run_info.json`.

### 3.4 Validar o perfil dos agentes (não pule)
Abra `out/perfil_agentes.md` e confira:
- **Valores da coluna `agent`.** Se algum agente aparecer com um nome que as expressões regulares de `CLEAN_AGENTS` ou `PROBABLE_AGENTS` (no topo do script) não reconhecem, ajuste-as.
- **Autores de commit do FA principal.** Para Copilot, Devin e Jules, os autores mais frequentes devem ser contas do próprio agente (algo como `copilot-swe-agent[bot]`, `devin-ai-integration[bot]`, `google-labs-jules[bot]`). Se o nome real for outro, ajuste `AGENT_COMMIT_AUTHOR`; caso contrário, PRs puras serão contadas como mistas.
- **Confirmação de D15.** Se o autor da PR de Codex/Claude Code for majoritariamente uma conta humana, a decisão D15 se confirma.

Depois de ajustar, rode de novo **sem** baixar:
```powershell
python spike_aidev.py
```

### 3.5 (Recomendado) Estimar o grupo HL
```powershell
python spike_aidev.py --github-token SEU_TOKEN
```
Consulta até 80 repositórios candidatos, com cerca de 2 s de pausa entre consultas para respeitar o limite da API de busca (~3 min). Isso adiciona a coluna `hl_prs_estimadas` em `repos_candidatos.csv` e aplica o critério completo de go/no-go. **Não salve o token em arquivos do projeto.**

### 3.6 Interpretar o resultado
`out/relatorio.md` traz:
- o funil por grupo e por agente (quantas PRs sobram em cada etapa);
- quantos repositórios têm ≥ 5, 10 e 20 PRs do FA elegíveis;
- o veredito, com critério padrão **≥ 30 repositórios com ≥ 10 PRs do FA principal e ≥ 10 PRs humanas estimadas**.

**Leia os números como teto.** O spike não aplica os filtros finos de E3 (função tocada, reformatação, limite de 500 LLOC, AST), e soma as linhas adicionadas de todos os commits da PR, não o diff líquido. Na Fase 1, o número de unidades válidas será **menor**.

### 3.7 Se der NO-GO
Opções, em ordem de preferência (cada uma tem custo metodológico; registrar a escolha em §4 da metodologia):
1. Baixar N para 5 por grupo (perde poder estatístico; compensa com mais repositórios).
2. Incluir o FA-provável na análise principal (enfraquece o construto; ver sabatina C2).
3. Testar uma revisão anterior do AIDev (pode ter mais PRs no subconjunto popular e traz `pr_task_type`; ver §6.0 da metodologia).
4. Relaxar o filtro de `.py` (≥ 1 linha) — último recurso.

### 3.8 Registrar o resultado
1. Coloque `relatorio.md`, `funil.csv` e `repos_candidatos.csv` no projeto (pasta `resultados/spike/`).
2. Preencha a seção 5 deste documento com os números principais.
3. Atualize a metodologia: D16 (go/no-go), P2 (revisão do AIDev) e §10, se algum parâmetro mudou.

## 4. Problemas comuns
| Sintoma | Causa provável | Solução |
|---|---|---|
| `401` / `GatedRepoError` no download | O dataset pede aceite de termos | Abra a página do dataset no Hugging Face logado, aceite os termos e rode `huggingface-cli login` |
| Download interrompido | Rede instável | Rode `--download` de novo; o `huggingface_hub` retoma |
| `MemoryError` | Pouca RAM ao ler `pr_commit_details` | Feche outros programas; o script só lê 3 colunas, mas precisa de ~2–4 GB |
| 0 PRs puras no FA principal | Nome do autor de commit diferente do esperado | Ajuste `AGENT_COMMIT_AUTHOR` com base em `perfil_agentes.md` |
| `hl_prs_estimadas` vazio | Token inválido ou limite da API | Confira o token; aguarde 1 min e rode de novo |
| Ativação do venv bloqueada no Windows | Política de execução | `Set-ExecutionPolicy -Scope Process Bypass` |

## 5. Resultados

### Rodada de 13/10/2026 (Pedro) — revisão `7840b6e61a5828461cd96806c52c20194ef57979`
Corte real do AIDev: **24/10/2025** (não novembro). Observação mínima para Q4 até hoje: 353 dias (> W = 90).

**Funil do FA principal (Python, AIDev-pop, mergeadas até o corte):** 2.011 PRs → 1.292 puras (64%) → **545 elegíveis** (tocam `.py` de produção). Copilot 417, Devin 123, Jules 5.
**Perfil dos agentes:** Copilot, Devin e Jules abrem 100% das PRs com conta de bot (confirma D15). Codex tem 0% e commita com a conta do humano. Cursor commita como `cursoragent` (identidade verificável em 63% das PRs mergeadas). Um único usuário responde por ~38% das PRs do Codex.

| Cenário | PRs elegíveis | repos N≥5 | repos N≥10 | N≥5 e HL≥5 (estim.) | N≥10 e HL≥10 (estim.) |
|---|---|---|---|---|---|
| S1 — Copilot, Devin, Jules | 545 | 31 | 9 | 21 | 4 |
| S2 — S1 + commits com identidade do agente (Cursor) | 660 | 39 | 10 | 28 | 5 |
| S3 — S2 + pureza fraca (Codex etc.) | 4.096 | 110 | 53 | n/d¹ | n/d¹ |

¹ HL só foi consultado para os 39 candidatos de S2.

**Ressalvas desta rodada:** (a) as estimativas de HL de repositórios muito ativos (`airbyte`, `litellm`, `sentry`) saíram 0 por um limite de páginas do script — corrigido depois; esses repositórios têm centenas de PRs humanas; `mlflow` falhou por rede. (b) Vários repositórios têm HL baixo porque o 1º merge do FA é próximo do corte (janela HL curta); a versão corrigida também mede uma janela HL **ampliada** (180 dias antes do 1º merge do FA). (c) Os números são teto: a Fase 1 aplica os filtros finos de E3.

**Veredito:** NO-GO pelo critério original (≥ 30 repositórios com ≥ 10 PRs). Meta de 100 repositórios **não é atingível no AIDev-pop** mantendo o construto S1/S2. Próximo passo: medir o teto no AIDev completo (`spike_teto.py`).


### Teto do AIDev completo (`spike_teto.py`, 13/10/2026)
Repositórios Python (sem fork) com ≥ 1 PR mergeada de agente: 42.928 (690 no AIDev-pop). Estimativa de PRs FA elegíveis aplicando as taxas do AIDev-pop (Copilot 0,28; Devin 0,25; Jules 0,17; Cursor 0,32):

| Estrelas ≥ | S1 N≥5 | S1 N≥10 | S2 N≥5 | S2 N≥10 |
|---|---|---|---|---|
| 100 | 17 | 5 | 25 | 7 |
| 20 | 24 | 6 | 33 | 8 |
| 10 | 33 | 8 | 44 | 10 |
| 0 | 529 | 226 | 735 | 321 |

**Leitura:** fora do AIDev-pop há só **~16 repositórios com ≥ 10 estrelas** e ≥ 5 PRs S1 esperadas (ex.: `vellum-ai/vellum-python-sdks`, `airbytehq/airbyte-python-cdk`, `Clarifai/clarifai-python`, `ROCm/iris`, `microsoft/simplechat`), antes de qualquer checagem de HL. A explosão para 529 vem de repositórios com **0–4 estrelas** (483 deles): projetos pessoais em que o agente faz praticamente todas as PRs (ex.: 577 de 577), sem grupo humano para comparar. **Conclusão:** o AIDev completo acrescentaria ~8–16 repositórios úteis, ao custo de coletar pureza e arquivos pela API do GitHub; a meta de 100 repositórios não é atingível mantendo D15 e a comparação intra-repositório.


### Rodada JavaScript/TypeScript (`rodar_spike_js.bat`, 13/10/2026)
Mesma revisão e regras; arquivos `.js/.jsx/.mjs/.cjs/.ts/.tsx/.mts/.cts`, excluindo testes, `node_modules`, `dist`/`build`, `.min.js`, `.d.ts` e configs. Saída em `spike/out_js/`.

Funil do FA principal: 4.851 PRs mergeadas → 2.982 puras (61%) → **1.632 elegíveis** (Copilot 829, Devin 787, Jules 16).

| Cenário | PRs elegíveis | repos N≥5 | N≥5 e HL≥5 | N≥10 e HL≥10 | N≥5 e HL ampliado≥5 |
|---|---|---|---|---|---|
| S1 | 1.632 | 75 | **56** | 30 | 59 |
| S2 | 2.008 | 86 | 59 | 32 | 63 |

Por linguagem (S1, N≥5 e HL≥5): **TypeScript 52, JavaScript 4**. Quatro candidatos deram 404 na API (repositórios privados ou apagados: `antiwork/gumboard`, `antiwork/helper`, `antiwork/iffy`, `faros-ai/airbyte-connectors`) e não podem ser clonados. Concentração: `liam-hq/liam` tem 161 PRs FA (17% do total JS/TS). Lista com status em `docs/amostra_jsts.csv`.

**Leitura:** JS/TS (na prática, TypeScript) **mais que dobra** a amostra mantendo D15: Python 24 + JS/TS 56 = **~80 repositórios** no S1 com ≥ 5/≥ 5, e ~90 no S2.

## 6. Notas para agentes de IA que executarem ou alterarem o spike
- O spike é **descartável e só de leitura**: não clona repositórios e não escreve fora de `data/` e `out/`.
- Não altere os critérios de go/no-go sem registrar a mudança na metodologia (D16).
- A pureza das PRs do FA principal exige que **todo** commit, exceto merges de sincronização (`Merge branch …`), tenha como autor o agente. No FA-provável aceita-se também o autor da PR, porque esses agentes commitam com a conta do humano; essa pureza é mais fraca (sabatina C2).
- O script aceita `--format csv` (oculto) para testes com dados sintéticos.
