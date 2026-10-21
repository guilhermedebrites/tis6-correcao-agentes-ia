# Classificador de correção (etapa E5b)

> **Data:** 19/10/2026 · **Status:** proposta v1, vale para a pipeline adaptada ou refeita.
> **Para que serve:** decidir se cada PR posterior que alterou linhas de uma PR de origem é uma **correção de defeito**. É a medida central da QP1 (`fix_rate_w`) e da QP2 (proposta `07-nova-proposta-correcao.md`).

---

## 1. Entrada e saída

**Unidade classificada:** o *evento* = uma PR posterior P (ou commit direto) que alterou ou removeu linhas de uma PR de origem C dentro da janela W. Uma PR P é classificada **uma vez**, mesmo que atinja várias PRs de origem (cache por `repo + P`).

**O que o modelo recebe:**
| Campo | Origem | Limite |
|---|---|---|
| Título de P | histórico git / API | — |
| Descrição de P | API do GitHub (`GET /repos/{o}/{r}/pulls/{n}`), com cache | 1.500 caracteres |
| Rótulos de P (ex.: `bug`) | API, mesma consulta | — |
| Mensagens dos commits de P | git | 10 primeiras, 200 caracteres cada |
| Trecho do diff de P **nas linhas atribuídas a C** | `git diff -U3` filtrado pelos hunks do blame | 120 linhas |

**O que o modelo NÃO recebe:** quem é o autor de C nem de P, o fluxo (FA/HL), o nome do agente, o nome da branch. Isso mantém o classificador **cego ao fluxo**, para que ele não enviese a QP1 (ex.: "é de bot, deve ser bug").

**Saída (JSON):**
```json
{
  "categoria": "corrige_defeito | evolucao | refatoracao | outro",
  "confianca": "alta | media | baixa",
  "justificativa": "uma frase"
}
```
`fix = (categoria == "corrige_defeito")`. A heurística antiga por palavras-chave continua calculada ao lado, como sensibilidade.

---

## 2. Categorias (definições que vão no prompt e no guia de rotulação manual)
| Categoria | Definição | Exemplos |
|---|---|---|
| `corrige_defeito` | Muda o comportamento para consertar algo que estava **errado**: exceção, resultado incorreto, caso de borda não tratado, regressão, falha de segurança, erro de tipo | "Fix crash when config is empty"; diff troca `>` por `>=` em validação |
| `evolucao` | Acrescenta ou altera comportamento **desejado** que antes não existia: nova funcionalidade, nova opção, mudança de requisito, ajuste de API | "Add retry option to client"; "Support Python 3.13" |
| `refatoracao` | Muda a estrutura **sem** mudar o comportamento: renomear, extrair função, mover código, tipagem, limpeza, formatação | "Refactor parser into module"; "Rename X to Y" |
| `outro` | Reverts, atualização de dependência, mudança só de log/mensagem/documentação em código, ou informação insuficiente para decidir | "Revert #123"; "Bump version" |

**Regra de desempate:** se a PR mistura correção e evolução, vale o **propósito declarado** no título/descrição; se não há propósito claro, o que o diff nas linhas de C faz.

---

## 3. Prompt (rascunho)
```
Você classifica mudanças de código em repositórios open source.
Recebe uma pull request posterior (título, descrição, rótulos, mensagens de commit)
e o trecho do diff em que ela altera linhas escritas anteriormente.
Classifique o PROPÓSITO dessa mudança nas linhas mostradas, em exatamente uma categoria:
- corrige_defeito: conserta comportamento errado (bug, exceção, resultado incorreto, caso de borda, regressão, segurança).
- evolucao: adiciona ou altera comportamento desejado (funcionalidade, opção, requisito, API).
- refatoracao: muda estrutura sem mudar comportamento (renomear, extrair, mover, tipar, limpar, formatar).
- outro: revert, dependência, só log/mensagem/documentação, ou informação insuficiente.
Se houver mistura, use o propósito declarado no título/descrição; sem propósito claro, use o que o diff faz.
Responda só com JSON: {"categoria": ..., "confianca": "alta|media|baixa", "justificativa": "<uma frase>"}.
```

---

## 4. Reprodutibilidade
- **Modelo com versão fixa** (`claude-haiku-5-5`, registrado em cada resposta do cache).
- **Meio de chamada:** por padrão, o Claude Code logado no plano do usuário (`claude -p`, sem ferramentas, sem MCP, sem sessão salva); opcionalmente a API (`--meio api`, temperatura 0). O Claude Code não permite fixar a temperatura, então a reprodutibilidade vem do **cache**: cada evento é classificado uma única vez e o rótulo fica guardado; quem rodar de novo com o mesmo cache obtém exatamente os mesmos rótulos. O cache deve ser versionado junto com os resultados.
- Prompt versionado no repositório (`prompts/classificador_v1.txt`); mudar o prompt = nova versão e reclassificação completa.
- **Cache** de todas as respostas em disco (`data/llm_cache/<hash da entrada>.json`): rodar de novo não muda rótulos nem custa nada.
- Respostas inválidas (JSON quebrado) → nova tentativa uma vez; depois, `outro` com `confianca = baixa` e registro no funil.
- Chaves e logins só no computador de quem roda, nunca em arquivo do projeto.

---

## 5. Validação (o mínimo que sustenta a medida)
| Passo | Como | Esforço |
|---|---|---|
| Amostra | Sortear **80 eventos**, estratificados: 40 que o modelo marcou `corrige_defeito` e 40 que não marcou; metade com origem FA, metade HL | Script |
| Rotulação | Dois membros rotulam cada evento **sem ver** o rótulo do modelo nem um do outro, com as definições da §2 | 160 rótulos ÷ 6 pessoas ≈ 27 cada (~40 min) |
| Medidas | Kappa entre os dois humanos (qualidade das definições); precisão e revocação do modelo contra o rótulo de consenso, **separadas por FA e HL** | Script |
| Critério | Kappa humano ≥ 0,6 e precisão do modelo ≥ 0,8. Se o modelo errar mais em um dos fluxos, isso vira ameaça explícita e sensibilidade | — |

A separação por fluxo é o ponto que a banca vai perguntar: o classificador precisa errar **igual** no código de agente e no humano, senão a comparação da QP1 fica enviesada.

---

## 6. Custo esperado
O número de eventos só é conhecido depois do blame. Para dimensionar, nos 12 repositórios Python houve ~22,7 mil linhas retrabalhadas (doc 05 §6.4). Agrupadas por PR corretora, isso deve dar **na ordem de mil a poucos milhares de PRs** a classificar. Com ~1–2 mil tokens de entrada por evento e um modelo pequeno, o custo total fica baixo; a estimativa exata sai na primeira rodada.
