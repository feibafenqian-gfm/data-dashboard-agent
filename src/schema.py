"""数据集 profile 加载 + canonical fact 约定。

canonical fact（行粒度，一个数据集一份 prepare.py 产出）必需列：
  order_id(str) / customer_id(str, 复购实体) / timestamp(datetime) / amount(float)
可选列：
  quantity(float, 默认 1)
维度列：与 profile.dimensions[].column 对应，任意离散字符串列。
"""
import os
import importlib.util

import pandas as pd
import yaml

REQUIRED_FACT_COLUMNS = ["order_id", "customer_id", "timestamp", "amount"]


def load_dataset(root, name):
    """加载数据集 profile 并执行 prepare，返回 (profile, fact)。"""
    ddir = os.path.join(root, "datasets", name)
    with open(os.path.join(ddir, "profile.yaml"), encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    prep_path = os.path.join(ddir, "prepare.py")
    spec = importlib.util.spec_from_file_location(f"prepare_{name}", prep_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    data_dir = os.path.join(ddir, profile.get("data_dir", "data"))
    fact = mod.prepare(data_dir)
    _validate(fact, profile)
    return profile, fact


def _validate(fact, profile):
    missing = [c for c in REQUIRED_FACT_COLUMNS if c not in fact.columns]
    if missing:
        raise ValueError(f"canonical fact 缺少必需列：{missing}")
    for d in profile.get("dimensions", []):
        if d["column"] not in fact.columns:
            raise ValueError(f"维度 {d.get('key')} 的列 {d['column']} 不在 fact 中")
