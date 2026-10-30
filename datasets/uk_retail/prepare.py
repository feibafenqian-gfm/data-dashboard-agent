"""UK Online Retail：单文件行数据 -> canonical fact。

清洗：去空客户、去退货（Quantity<=0）、去无效单价（UnitPrice<=0）。
金额 = Quantity × UnitPrice。
"""
import os

import pandas as pd

COUNTRY_ZH = {
    "United Kingdom": "英国", "Germany": "德国", "France": "法国", "EIRE": "爱尔兰",
    "Spain": "西班牙", "Netherlands": "荷兰", "Belgium": "比利时",
    "Switzerland": "瑞士", "Portugal": "葡萄牙", "Australia": "澳大利亚",
    "Norway": "挪威", "Italy": "意大利", "Austria": "奥地利", "Sweden": "瑞典",
    "Poland": "波兰", "Denmark": "丹麦", "Finland": "芬兰", "Japan": "日本",
    "USA": "美国", "Iceland": "冰岛", "Canada": "加拿大", "Israel": "以色列",
    "Cyprus": "塞浦路斯", "Greece": "希腊", "Malta": "马耳他", "Singapore": "新加坡",
    "Hong Kong": "香港", "Lebanon": "黎巴嫩", "Lithuania": "立陶宛",
    "Czech Republic": "捷克", "Bahrain": "巴林", "Saudi Arabia": "沙特",
    "United Arab Emirates": "阿联酋", "European Community": "欧盟",
    "Channel Islands": "海峡群岛", "RSA": "南非", "Brazil": "巴西",
    "Unspecified": "未指定",
}


def prepare(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "data.csv"), encoding="latin-1", low_memory=False)
    df = df.dropna(subset=["CustomerID"])
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    df["timestamp"] = pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M", errors="coerce")
    df = df.dropna(subset=["timestamp"])

    df["order_id"] = df["InvoiceNo"].astype(str)
    df["customer_id"] = df["CustomerID"].astype("Int64").astype(str)
    df["amount"] = df["Quantity"] * df["UnitPrice"]
    df["quantity"] = df["Quantity"]
    df["country"] = df["Country"].map(COUNTRY_ZH).fillna(df["Country"])

    cols = ["order_id", "customer_id", "timestamp", "amount", "quantity", "country"]
    return df[cols].reset_index(drop=True)
