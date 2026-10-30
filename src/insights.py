"""通用指标 + 规则化异动检测 + 下钻表。"""
import pandas as pd


def _money(v, cur):
    if v >= 1e6:
        return f"{cur}{v/1e6:,.2f}M"
    if v >= 1e3:
        return f"{cur}{v/1e3:,.1f}K"
    return f"{cur}{v:,.0f}"


def _df(rows):
    return pd.DataFrame(rows)


def compute_summary(cube, profile):
    cur = cube["meta"]["currency"]
    monthly = _df(cube["monthly"])
    meta = cube["meta"]

    tot = monthly[["gmv", "orders", "items"]].sum()
    gmv = float(tot["gmv"])
    orders = int(tot["orders"])
    items = float(tot["items"])
    aov = gmv / orders if orders else 0.0
    items_per = items / orders if orders else 0.0
    customers = meta["n_customers"]
    repeat_rate = meta["repeat_rate"]

    # 异动检测
    am = monthly.sort_values("month").reset_index(drop=True)
    am["mom"] = am["gmv"].pct_change()
    anomalies = []
    peak = am.loc[am["gmv"].idxmax()]
    anomalies.append({"month": str(peak["month"]), "type": "GMV峰值",
                      "gmv": float(peak["gmv"]),
                      "mom": float(peak["mom"]) if pd.notna(peak["mom"]) else None})
    meaningful = am[(am["orders"] >= 30) & am["mom"].notna()]
    if len(meaningful):
        drop = meaningful.loc[meaningful["mom"].idxmin()]
        if drop["mom"] < -0.10 and str(drop["month"]) != str(peak["month"]):
            anomalies.append({"month": str(drop["month"]), "type": "GMV下滑",
                              "gmv": float(drop["gmv"]), "mom": float(drop["mom"])})
        rise = meaningful.loc[meaningful["mom"].idxmax()]
        if rise["mom"] > 0.20 and str(rise["month"]) != str(peak["month"]):
            anomalies.append({"month": str(rise["month"]), "type": "GMV激增",
                              "gmv": float(rise["gmv"]), "mom": float(rise["mom"])})

    first6 = am.head(6)["gmv"].sum()
    last6 = am.tail(6)["gmv"].sum()
    growth = (last6 - first6) / first6 if first6 else 0.0

    # 下钻表（每个维度：Top4 + 其他，分月）
    all_months = sorted(monthly["month"].tolist())
    drill = {}
    top_values = {}
    for d in profile.get("dimensions", []):
        key = d["key"]
        dd = _df(cube["dims"][key])
        top = dd.groupby("value")["gmv"].sum().nlargest(4).index.tolist()
        pivot = dd.pivot_table(index="month", columns="value", values="gmv",
                               aggfunc="sum", fill_value=0.0).reindex(all_months)
        cols = [c for c in top if c in pivot.columns]
        sub = pivot[cols].copy()
        sub["其他"] = pivot.sum(axis=1) - sub.sum(axis=1)
        drill[key] = [
            {"月": m, **{c: _money(sub.loc[m, c], cur) for c in sub.columns}}
            for m in all_months
        ]
        total = dd.groupby("value")["gmv"].sum().sort_values(ascending=False)
        top_values[key] = [
            {"value": v, "gmv": _money(gv, cur), "share": f"{gv/total.sum()*100:.1f}%"}
            for v, gv in total.head(5).items()
        ]

    metrics = {
        "gmv": gmv, "orders": orders, "aov": aov, "items_per_order": items_per,
        "customers": customers, "repeat_rate": repeat_rate,
        "growth_first6_last6": growth,
        "peak_month": str(peak["month"]), "peak_month_gmv": float(peak["gmv"]),
        "month_min": meta["month_min"], "month_max": meta["month_max"],
        "currency": cur,
    }

    monthly_gmv = [{"month": r["month"], "gmv": float(r["gmv"])}
                   for _, r in monthly.sort_values("month").iterrows()]

    return {"metrics": metrics, "anomalies": anomalies, "monthly_gmv": monthly_gmv,
            "drill": drill, "top_values": top_values}
