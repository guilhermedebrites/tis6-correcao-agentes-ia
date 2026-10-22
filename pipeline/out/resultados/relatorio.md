# Relatório — correção do código de agentes

Repositórios analisados: 13 · PRs FA: 150 · PRs HL: 2387

## QP1 — Frequência
- `fix_rate_w` (FA − HL): +0.0035 (IC -0.0162 a +0.0232; p 0.729; n 2537; lmm) · **Holm H1: 1**
- `rework_rate_w` (exploratório): +0.0064 (IC -0.0413 a +0.0540; p 0.794; n 2537; lmm)
- Wilcoxon por repositório (fix): {'n_repos': 13, 'mediana_dif': -0.0020110608345902466, 'p': 0.892578125, 'repos_fa_maior': 5}
- Cox (tempo até a 1ª correção): {'hr': 0.9830796016043577, 'ic_inf': 0.5930396532212662, 'ic_sup': 1.6296473563631955, 'p': 0.9472378812011584}
- Kaplan-Meier, sem correção em 90 dias: {'FA': 0.84, 'HL': 0.7943024717218268}
- Médias por fluxo: {'fix_rate_w': {'FA': 0.0341, 'HL': 0.0309}, 'rework_rate_w': {'FA': 0.2256, 'HL': 0.1709}, 'has_fix': {'FA': 0.16, 'HL': 0.2057}}

## QP2 — Autoria
- PRs com alguma correção: {'HL': 491, 'FA': 24}
- Linhas corrigidas por quem conduziu a correção: {'FA': {'fix_por_humano': 117, 'fix_por_agente_principal': 15, 'fix_por_outro_agente': 0, 'fix_por_bot': 0}, 'HL': {'fix_por_humano': 2531, 'fix_por_agente_principal': 110, 'fix_por_outro_agente': 0, 'fix_por_bot': 0}}
- Fração do código FA corrigida em PRs conduzidas por humanos: 0.81 (IC 0.67–0.98); linha de base humana nos mesmos repositórios: 0.97
- Excesso sobre a linha de base: -0.0500 (IC -0.2577 a +0.1577; p 0.637; n 24; lmm) · **Holm H2: 1**
- Autocorreção: FA 0.19 · HL 0.96

## QP3 — Fatores
- Interação fluxo × log(tamanho): -0.0137 (IC -0.0296 a +0.0023; p 0.0936; n 2537; lmm) · **Holm H3: 0.281**
- log_size (exploratório): -0.0082 (IC -0.0121 a -0.0044; p 2.32e-05; n 2537; lmm)
- log_churn_ant (exploratório): +0.0077 (IC +0.0024 a +0.0130; p 0.00406; n 2537; lmm)
- cc_delta (exploratório): +0.0001 (IC -0.0000 a +0.0003; p 0.0986; n 2537; lmm)

## Repositórios

```
                             repo familia                                 snapshot fonte_fa            inicio_periodo  frac_sem_marcacao  api_consultas  fa_validas  hl_validas  incluido  n_eventos                                    erro
             AgentOps-AI/agentops  python f8e907b92dabe47232978023fdcb01e2a7d4b752    aidev 2025-05-10T13:33:17-07:00              0.012            0.0         7.0        36.0      True       25.0                                     NaN
       Azure/azure-sdk-for-python  python                                      NaN      NaN                       NaN                NaN            NaN         NaN         NaN     False        NaN BrokenPipeError: [Errno 32] Broken pipe
                  BerriAI/litellm  python c8ed5ccca8500ccc0c8a3b499790c07e7e57a763    aidev 2025-09-24T11:54:06-07:00              0.216            0.0         5.0       204.0      True      232.0                                     NaN
                Ljzd-PRO/KToolBox  python e17249be548e9b52e1a46ddaf82b6676c17c2c60    aidev 2025-07-29T22:59:04+08:00              0.935          261.0         0.0         1.0     False        0.0                                     NaN
               NVIDIA/cuda-python  python 585038dfa23437c17bb60b210a3db25464e32171    aidev 2025-08-20T21:45:48-04:00              0.002            0.0         3.0        30.0     False        0.0                                     NaN
                   NewFuture/DDNS  python 9f6cee7a5e0eb4f6bd91bb8c76783ef002d72059    aidev 2025-07-02T12:38:01+00:00              0.175            0.0         8.0         7.0      True       13.0                                     NaN
           QuantEcon/QuantEcon.py  python 8c85f1b2bdb8410b50093cc9ed0bc2c2155334e9    aidev 2025-08-12T15:25:35+10:00              0.021            0.0         5.0         3.0     False        0.0                                     NaN
                airbytehq/airbyte  python db79d7aa355fd30cdc07ec13b7cf6c8b4e6b4ede    aidev 2025-01-24T15:09:46-08:00              0.001            0.0         3.0       240.0     False        0.0                                     NaN
            chaiNNer-org/chaiNNer  python ad1ccb0bd97b05ecd8ed174a4fce7ae222b2bca3    aidev 2025-10-19T00:00:46-05:00              0.065            0.0         7.0         4.0     False        0.0                                     NaN
                 crewAIInc/crewAI  python a8877f0cdfbca4fc4b95e3ce54aaa69aafca7688    aidev 2024-12-27T18:16:02-03:00              0.282            0.0        23.0       234.0      True      185.0                                     NaN
          deepmodeling/deepmd-kit  python d07c097bbea1aede457af09f20ffbaf42a177c7c    aidev 2025-08-25T09:23:39+00:00              0.005            0.0         3.0         6.0     False        0.0                                     NaN
                  gerlero/foamlib  python d045a87714cc12ebd8fd35c3daf1dc61e7ad2293    aidev 2025-08-27T17:08:59-03:00              0.118            0.0         4.0        55.0     False        0.0                                     NaN
jeroenterheerdt/HAsmartirrigation  python a77c99442bf8b62896d70743dedb7a506c0b87a0    aidev 2025-07-12T11:29:39-07:00              0.799          304.0        12.0         7.0      True       32.0                                     NaN
                mabel-dev/opteryx  python f6aa6e1d33a5e6cd2670e12300b5b2f7f4f9c3b0    aidev 2025-09-26T20:30:41+01:00              0.000            0.0         3.0        20.0     False        0.0                                     NaN
               marimo-team/marimo  python ca983d9b4e86c6a3868f09d32018e6a1f17bc065    aidev 2025-01-03T10:06:33-05:00              0.039            0.0         7.0       860.0      True      478.0                                     NaN
        microsoft/agent-framework  python 08851e69d722b0e0961c08eecf8575db995f0172    aidev 2025-09-19T05:56:49+00:00              0.002            0.0         3.0        61.0     False        0.0                                     NaN
            microsoft/fabric-cicd  python 5ca096c00a9a878c646c59fe537b883eba951329    aidev 2025-06-12T07:03:51-07:00              0.000            0.0         7.0        30.0      True       23.0                                     NaN
                   microsoft/lisa  python e0540ba8e224fdc7dcff7679af41f23f0f87d8ee    aidev 2025-05-22T13:15:16+08:00              0.626            0.0        12.0       142.0      True       59.0                                     NaN
                    mlflow/mlflow  python fd71b4bb5b5888f92def27f3e03204b1e5d6e96d    aidev 2025-05-23T05:27:57+00:00              0.002            0.0        33.0       504.0      True      318.0                                     NaN
                polarsource/polar  python f6036d7d7e83093fa86ac3dd8a504cbbfbc2d065    aidev 2025-08-27T13:23:32+02:00              0.383            0.0         7.0       207.0      True      162.0                                     NaN
            reflex-dev/reflex-web  python 21ef786c4454f2e4f0fa7e974b68b1279c642f37    aidev 2025-04-27T19:08:55-07:00              0.000            0.0        17.0       117.0      True      110.0                                     NaN
              translate/translate  python 51c5e35df32290d10f301d45cb8d9e267e3227c1    aidev 2025-10-17T12:24:40+00:00              0.438          366.0        13.0         4.0     False        0.0                                     NaN
               vlm-run/vlmrun-hub  python 55b534d87980aaca55fba28a4a6062a58f8f01ab    aidev 2025-01-04T13:10:00-08:00              0.184            0.0         6.0        34.0      True       25.0                                     NaN
                  xtekky/gpt4free  python 1dbac2541335a2312f53002dfa9d14119af53099    aidev 2025-08-21T08:52:11+02:00              0.873          745.0         6.0         5.0      True       13.0                                     NaN
```
