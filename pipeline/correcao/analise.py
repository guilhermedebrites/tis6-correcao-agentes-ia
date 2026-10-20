"""E6: junta as saídas por repositório, calcula os desfechos por PR de origem e responde QP1–QP3.

Família confirmatória (Holm): H1 `fix_rate_w` (FA × HL), H2 `human_fix_excess` > 0 no código FA,
H3 interação fluxo × log(size_churn). Todo o resto é exploratório.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from .config import CFG

warnings.filterwarnings("ignore")


def carregar(out: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unidades, eventos, status = [], [], []
    for pasta in sorted((out / "repos").glob("*")):
        st = pasta / "status.json"
        if not st.exists():
            continue
        s = json.loads(st.read_text(encoding="utf-8"))
        status.append(s)
        if not s.get("incluido"):
            continue
        u = pd.read_csv(pasta / "unidades.csv")
        u["familia"] = s["familia"]
        unidades.append(u[u["valida"]])
        if (pasta / "eventos.csv").stat().st_size > 1:
            eventos.append(pd.read_csv(pasta / "eventos.csv"))
    U = pd.concat(unidades, ignore_index=True) if unidades else pd.DataFrame()
    E = pd.concat(eventos, ignore_index=True) if eventos else pd.DataFrame()
    return U, E, pd.DataFrame(status)


def desfechos(U: pd.DataFrame, E: pd.DataFrame, rotulos: pd.DataFrame, status: pd.DataFrame) -> pd.DataFrame:
    U = U.copy()
    W = CFG.janela_dias
    if len(E):
        E = E.merge(rotulos[["evento", "correcao"]], on="evento", how="left")
        E["correcao"] = E["correcao"].fillna(False).astype(bool)
        tot = E.groupby("origem")["linhas"].sum()
        fix = E[E["correcao"]].groupby("origem")["linhas"].sum()
        fix_quem = E[E["correcao"]].pivot_table(index="origem", columns="evento_quem", values="linhas",
                                               aggfunc="sum", fill_value=0)
        primeiro_fix = E[E["correcao"]].groupby("origem")["dias"].min()
        primeiro_ret = E.groupby("origem")["dias"].min()
    else:
        tot = fix = primeiro_fix = primeiro_ret = pd.Series(dtype=float)
        fix_quem = pd.DataFrame()
    U["linhas_retrabalho"] = U["unit_id"].map(tot).fillna(0)
    U["linhas_fix"] = U["unit_id"].map(fix).fillna(0)
    U["rework_rate_w"] = (U["linhas_retrabalho"] / U["adicionadas"]).clip(upper=1)
    U["fix_rate_w"] = (U["linhas_fix"] / U["adicionadas"]).clip(upper=1)
    U["has_fix"] = (U["linhas_fix"] > 0).astype(int)
    U["dias_ate_fix"] = U["unit_id"].map(primeiro_fix).fillna(W)
    U["evento_fix"] = U["unit_id"].isin(primeiro_fix.index).astype(int)
    U["dias_ate_retrabalho"] = U["unit_id"].map(primeiro_ret).fillna(W)
    for quem in ("humano", "agente_principal", "outro_agente", "bot"):
        col = fix_quem[quem] if quem in fix_quem else pd.Series(dtype=float)
        U[f"fix_por_{quem}"] = U["unit_id"].map(col).fillna(0)
    U["human_fix_share"] = np.where(U["linhas_fix"] > 0, U["fix_por_humano"] / U["linhas_fix"].replace(0, np.nan), np.nan)
    U["self_fix_share"] = np.where(
        U["linhas_fix"] > 0,
        np.where(U["fluxo"] == "FA", U["fix_por_agente_principal"], U["fix_por_humano"]) / U["linhas_fix"].replace(0, np.nan),
        np.nan)
    base = {}
    for s in status.to_dict(orient="records"):
        at = s.get("atividade_linhas") or {}
        total = sum(at.values()) if isinstance(at, dict) else 0
        base[s["repo"]] = (at.get("humano", 0) / total) if total else np.nan
    U["base_humana_repo"] = U["repo"].map(base)
    U["human_fix_excess"] = U["human_fix_share"] - U["base_humana_repo"]
    U["fa"] = (U["fluxo"] == "FA").astype(int)
    U["log_size"] = np.log(U["size_churn"])
    U["log_churn_ant"] = np.log1p(U.get("churn_anterior", pd.Series(0, index=U.index)).fillna(0))
    return U


def _holm(ps: dict) -> dict:
    itens = sorted((p, k) for k, p in ps.items() if p == p)
    m, ajust, ant = len(itens), {}, 0.0
    for i, (p, k) in enumerate(itens):
        ant = max(ant, min(1.0, p * (m - i)))
        ajust[k] = ant
    return ajust


def _lmm(formula: str, df: pd.DataFrame, termo: str) -> dict:
    """LMM com intercepto aleatório por repositório. Com poucos repositórios o LMM pode ficar
    singular; nesse caso cai para OLS com erro-padrão agrupado por repositório (registrado em `modelo`)."""
    import statsmodels.formula.api as smf
    try:
        r = smf.mixedlm(formula, df, groups=df["repo"]).fit(reml=True, method="lbfgs")
        ic = r.conf_int().loc[termo]
        if r.converged and np.isfinite(r.bse[termo]) and (ic[1] - ic[0]) < 1e3 * max(abs(r.params[termo]), 1):
            return {"efeito": r.params[termo], "ic_inf": ic[0], "ic_sup": ic[1], "p": r.pvalues[termo],
                    "n": len(df), "modelo": "lmm"}
    except Exception:  # noqa: BLE001
        pass
    try:
        r = smf.ols(formula, df).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df["repo"])[0]})
        ic = r.conf_int().loc[termo]
        return {"efeito": r.params[termo], "ic_inf": ic[0], "ic_sup": ic[1], "p": r.pvalues[termo],
                "n": len(df), "modelo": "ols_cluster"}
    except Exception as e:  # noqa: BLE001
        return {"erro": str(e)[:200], "n": len(df)}


def _wilcoxon_repo(df: pd.DataFrame, col: str) -> dict:
    from scipy.stats import wilcoxon
    g = df.groupby(["repo", "fluxo"])[col].mean().unstack()
    g = g.dropna(subset=["FA", "HL"]) if {"FA", "HL"} <= set(g.columns) else pd.DataFrame()
    if len(g) < 3:
        return {"n_repos": len(g)}
    dif = g["FA"] - g["HL"]
    try:
        p = wilcoxon(dif).pvalue
    except ValueError:
        p = np.nan
    return {"n_repos": len(g), "mediana_dif": float(dif.median()), "p": float(p),
            "repos_fa_maior": int((dif > 0).sum())}


def _cox(df: pd.DataFrame, tempo: str, evento: str) -> dict:
    import statsmodels.api as sm
    try:
        X = df[["fa", "log_size"]].astype(float)
        r = sm.PHReg(df[tempo].astype(float), X, status=df[evento].astype(int)).fit(groups=df["repo"])
        i = list(X.columns).index("fa")
        ic = np.exp(r.conf_int()[i])
        return {"hr": float(np.exp(r.params[i])), "ic_inf": float(ic[0]), "ic_sup": float(ic[1]),
                "p": float(r.pvalues[i])}
    except Exception as e:  # noqa: BLE001
        return {"erro": str(e)[:200]}


def _km(df: pd.DataFrame, tempo: str, evento: str) -> dict:
    from statsmodels.duration.survfunc import SurvfuncRight
    res = {}
    for fl, g in df.groupby("fluxo"):
        sf = SurvfuncRight(g[tempo].astype(float), g[evento].astype(int))
        res[fl] = float(sf.surv_prob[sf.surv_times <= CFG.janela_dias][-1]) if len(sf.surv_times) else 1.0
    return res


def _boot_repo(df: pd.DataFrame, col: str, n: int = 2000) -> tuple[float, float, float]:
    rng = np.random.default_rng(CFG.semente)
    repos = df["repo"].unique()
    est = df[col].mean()
    amostras = []
    for _ in range(n):
        esc = rng.choice(repos, len(repos), replace=True)
        amostras.append(pd.concat([df[df["repo"] == r] for r in esc])[col].mean())
    return est, float(np.nanpercentile(amostras, 2.5)), float(np.nanpercentile(amostras, 97.5))


def analisar(out: Path, rotulos: pd.DataFrame) -> dict:
    U, E, status = carregar(out)
    res_dir = out / "resultados"
    res_dir.mkdir(parents=True, exist_ok=True)
    if U.empty:
        (res_dir / "relatorio.md").write_text("Nenhum repositório passou no mínimo de 5 FA + 5 HL válidas.\n")
        return {}
    U = desfechos(U, E, rotulos, status)
    U.to_csv(res_dir / "unidades_desfechos.csv", index=False)

    cov = "log_size + log_churn_ant + C(tipo_tarefa)" + (" + C(modo)" if U["modo"].nunique() > 1 else "")
    R: dict = {"n_repos": int(U["repo"].nunique()), "n_fa": int(U["fa"].sum()), "n_hl": int((1 - U["fa"]).sum())}

    # QP1 — frequência
    R["qp1_fix_rate"] = _lmm(f"fix_rate_w ~ fa + {cov}", U, "fa")
    R["qp1_rework_rate"] = _lmm(f"rework_rate_w ~ fa + {cov}", U, "fa")
    R["qp1_wilcoxon_fix"] = _wilcoxon_repo(U, "fix_rate_w")
    R["qp1_cox_fix"] = _cox(U, "dias_ate_fix", "evento_fix")
    R["qp1_km_sem_fix"] = _km(U, "dias_ate_fix", "evento_fix")
    R["qp1_medias"] = U.groupby("fluxo")[["fix_rate_w", "rework_rate_w", "has_fix"]].mean().round(4).to_dict()

    # QP2 — autoria
    corr = U[U["linhas_fix"] > 0]
    R["qp2_n_corrigidas"] = corr["fluxo"].value_counts().to_dict()
    R["qp2_linhas_fix_por_quem"] = (corr.groupby("fluxo")[[c for c in U.columns if c.startswith("fix_por_")]]
                                    .sum().astype(int).to_dict(orient="index"))
    fa_corr = corr[corr["fluxo"] == "FA"].dropna(subset=["human_fix_excess"])
    if len(fa_corr) >= 3:
        R["qp2_human_fix_share_fa"] = _boot_repo(fa_corr, "human_fix_share")
        R["qp2_base_humana_media"] = float(fa_corr["base_humana_repo"].mean())
        R["qp2_excess"] = _lmm("human_fix_excess ~ 1", fa_corr, "Intercept")
    hl_corr = corr[corr["fluxo"] == "HL"]
    if len(hl_corr) >= 3:
        R["qp2_self_fix_hl"] = float(hl_corr["self_fix_share"].mean())
    if len(fa_corr) >= 3:
        R["qp2_self_fix_fa"] = float(fa_corr["self_fix_share"].mean())

    # QP3 — fatores
    R["qp3_interacao_tamanho"] = _lmm(f"fix_rate_w ~ fa * log_size + log_churn_ant + C(tipo_tarefa)", U, "fa:log_size")
    R["qp3_fatores"] = {t: _lmm(f"fix_rate_w ~ fa + {cov} + cc_delta", U, t)
                        for t in ("log_size", "log_churn_ant", "cc_delta")}

    # Holm na família confirmatória (H2 é unilateral: excesso > 0)
    ps = {"H1": R["qp1_fix_rate"].get("p", np.nan), "H3": R["qp3_interacao_tamanho"].get("p", np.nan)}
    if "qp2_excess" in R and "p" in R["qp2_excess"]:
        e = R["qp2_excess"]
        ps["H2"] = e["p"] / 2 if e["efeito"] > 0 else 1 - e["p"] / 2
    R["holm"] = _holm(ps)
    R["p_bruto"] = ps

    (res_dir / "resultados.json").write_text(json.dumps(R, indent=2, ensure_ascii=False, default=float),
                                             encoding="utf-8")
    status.to_csv(res_dir / "status_repos.csv", index=False)
    (res_dir / "relatorio.md").write_text(_relatorio(R, status), encoding="utf-8")
    return R


def _fmt(d: dict, chave="efeito") -> str:
    if not d or "erro" in d:
        return f"(não estimado: {d.get('erro', 'dados insuficientes') if d else 'dados insuficientes'})"
    return (f"{d[chave]:+.4f} (IC {d['ic_inf']:+.4f} a {d['ic_sup']:+.4f}; p {d['p']:.3g}; "
            f"n {d.get('n', '')}; {d.get('modelo', '')})")


def _relatorio(R: dict, status: pd.DataFrame) -> str:
    h = R.get("holm", {})
    l = ["# Relatório — correção do código de agentes", "",
         f"Repositórios analisados: {R['n_repos']} · PRs FA: {R['n_fa']} · PRs HL: {R['n_hl']}", "",
         "## QP1 — Frequência",
         f"- `fix_rate_w` (FA − HL): {_fmt(R['qp1_fix_rate'])} · **Holm H1: {h.get('H1', float('nan')):.3g}**",
         f"- `rework_rate_w` (exploratório): {_fmt(R['qp1_rework_rate'])}",
         f"- Wilcoxon por repositório (fix): {R['qp1_wilcoxon_fix']}",
         f"- Cox (tempo até a 1ª correção): {R['qp1_cox_fix']}",
         f"- Kaplan-Meier, sem correção em {CFG.janela_dias} dias: {R['qp1_km_sem_fix']}",
         f"- Médias por fluxo: {R['qp1_medias']}", "",
         "## QP2 — Autoria",
         f"- PRs com alguma correção: {R['qp2_n_corrigidas']}",
         f"- Linhas corrigidas por quem conduziu a correção: {R['qp2_linhas_fix_por_quem']}"]
    if "qp2_excess" in R:
        est, lo, hi = R["qp2_human_fix_share_fa"]
        l += [f"- Fração do código FA corrigida em PRs conduzidas por humanos: {est:.2f} (IC {lo:.2f}–{hi:.2f}); "
              f"linha de base humana nos mesmos repositórios: {R['qp2_base_humana_media']:.2f}",
              f"- Excesso sobre a linha de base: {_fmt(R['qp2_excess'])} · **Holm H2: {h.get('H2', float('nan')):.3g}**"]
    l += [f"- Autocorreção: FA {R.get('qp2_self_fix_fa', float('nan')):.2f} · HL {R.get('qp2_self_fix_hl', float('nan')):.2f}", "",
          "## QP3 — Fatores",
          f"- Interação fluxo × log(tamanho): {_fmt(R['qp3_interacao_tamanho'])} · **Holm H3: {h.get('H3', float('nan')):.3g}**"]
    for t, d in R["qp3_fatores"].items():
        l.append(f"- {t} (exploratório): {_fmt(d)}")
    tab = status.drop(columns=[c for c in ("traceback", "funil", "atividade_linhas", "fluxos") if c in status])
    try:
        tab_txt = tab.to_markdown(index=False)
    except ImportError:
        tab_txt = "```\n" + tab.to_string(index=False) + "\n```"
    l += ["", "## Repositórios", "", tab_txt]
    return "\n".join(l) + "\n"
