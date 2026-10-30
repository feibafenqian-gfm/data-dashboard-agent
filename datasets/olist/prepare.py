"""Olist：把 9 张关系表关联成 canonical fact（行粒度，已交付订单）。"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import categories  # noqa: E402


def prepare(data_dir):
    def read(name):
        return pd.read_csv(os.path.join(data_dir, name), low_memory=False)

    orders = read("olist_orders_dataset.csv")
    items = read("olist_order_items_dataset.csv")
    payments = read("olist_order_payments_dataset.csv")
    customers = read("olist_customers_dataset.csv")
    products = read("olist_products_dataset.csv")
    translation = read("product_category_name_translation.csv")

    # 类目中文
    enmap = dict(zip(translation["product_category_name"],
                     translation["product_category_name_english"]))
    products["category"] = products["product_category_name"].map(
        lambda c: categories.to_zh(c, enmap.get(c, "") if isinstance(c, str) else ""))
    products["category"] = products["category"].fillna("其他")

    # 主支付方式（每单第一笔）→ 中文
    pay_primary = (payments.sort_values("payment_sequential")
                   .groupby("order_id")["payment_type"].first())
    pay_primary = pay_primary.map(categories.payment_zh).fillna("未定义")

    orders["timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
    orders = orders.merge(customers[["customer_id", "customer_unique_id", "customer_state"]],
                          on="customer_id", how="left")
    orders["state"] = orders["customer_state"].map(categories.state_zh)

    # 行粒度 fact：order_items 为骨架，挂订单/客户/商品/支付
    fact = items.merge(
        orders[["order_id", "customer_unique_id", "timestamp", "order_status", "state"]],
        on="order_id", how="left")
    fact = fact.merge(products[["product_id", "category"]], on="product_id", how="left")
    fact = fact.join(pay_primary, on="order_id")

    fact = fact[fact["order_status"] == "delivered"]
    fact["amount"] = fact["price"] + fact["freight_value"]
    fact["quantity"] = 1.0
    fact["customer_id"] = fact["customer_unique_id"].astype(str)
    fact["order_id"] = fact["order_id"].astype(str)

    cols = ["order_id", "customer_id", "timestamp", "amount", "quantity",
            "category", "state", "payment_type"]
    fact = fact[cols].dropna(subset=["order_id", "customer_id", "timestamp", "amount"])
    return fact.reset_index(drop=True)
