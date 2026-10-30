"""通用 OLAP 立方体：把 canonical fact 聚合成 (月 × 维度) + 日序列。"""
import json

import pandas as pd


def _records(df):
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            df[c] = df[c].dt.strftime("%Y-%m-%d")
    return json.loads(df.to_json(orient="records", force_ascii=False))


def build_cube(fact, profile):
    f = fact.dropna(subset=["order_id", "customer_id", "timestamp", "amount"]).copy()
    f["month"] = f["timestamp"].dt.strftime("%Y-%m")
    f["date"] = f["timestamp"].dt.normalize()
    if "quantity" not in f.columns:
        f["quantity"] = 1.0

    # 日序列
    daily = (f.groupby("date", as_index=False)
             .agg(gmv=("amount", "sum"), orders=("order_id", "nunique"))
             .sort_values("date"))

    # 月度主表
    g = f.groupby("month", as_index=False).agg(
        gmv=("amount", "sum"), orders=("order_id", "nunique"), items=("quantity", "sum"))
    cust = f.groupby("month")["customer_id"].nunique().rename("customers").reset_index()
    first = f.groupby("customer_id")["month"].min()
    last = f.groupby("customer_id")["month"].max()
    newc = (f[f["month"] == f["customer_id"].map(first)]
            .groupby("month")["customer_id"].nunique().rename("new_customers").reset_index())
    churn = (f[f["month"] == f["customer_id"].map(last)]
             .groupby("month")["customer_id"].nunique().rename("churn_customers").reset_index())
    monthly = (g.merge(cust, on="month", how="left")
               .merge(newc, on="month", how="left")
               .merge(churn, on="month", how="left"))
    monthly[["new_customers", "churn_customers"]] = (
        monthly[["new_customers", "churn_customers"]].fillna(0))

    # 维度立方体
    dims = {}
    for d in profile.get("dimensions", []):
        col = d["column"]
        dd = (f.groupby(["month", col], as_index=False)
              .agg(gmv=("amount", "sum"), orders=("order_id", "nunique"))
              .rename(columns={col: "value"}))
        dims[d["key"]] = _records(dd)

    months = sorted(monthly["month"].tolist())
    order_per_cust = f.groupby("customer_id")["order_id"].nunique()
    repeat_rate = float((order_per_cust > 1).mean()) if len(order_per_cust) else 0.0

    return {
        "meta": {
            "title": profile.get("title", profile["display_name"]),
            "display_name": profile["display_name"],
            "currency": profile.get("currency", ""),
            "month_min": months[0],
            "month_max": months[-1],
            "n_orders": int(monthly["orders"].sum()),
            "n_customers": int(order_per_cust.shape[0]),
            "repeat_rate": round(repeat_rate, 4),
            "dimensions": [{"key": d["key"], "label": d["label"]}
                           for d in profile.get("dimensions", [])],
            "kpi_cards": profile.get("kpi_cards", ["gmv", "orders", "aov", "repeat_rate"]),
        },
        "months": months,
        "daily": _records(daily),
        "monthly": _records(monthly),
        "dims": dims,
    }
