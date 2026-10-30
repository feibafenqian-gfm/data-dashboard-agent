"""一键入口：python run.py <数据集名>  生成交互看板 + 分析报告。

数据集放在 datasets/<name>/，含 profile.yaml + prepare.py + data/。
"""
import os
import sys
import argparse

import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src import schema, cube, insights, report, dashboard  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="通用数据看板 + 分析报告 Agent")
    ap.add_argument("dataset", help="datasets/ 下的数据集名（如 olist、uk_retail）")
    ap.add_argument("--no-llm", action="store_true", help="跳过 LLM，规则版报告")
    args = ap.parse_args()

    with open(os.path.join(ROOT, "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    profile, fact = schema.load_dataset(ROOT, args.dataset)
    output_dir = os.path.join(ROOT, "datasets", args.dataset, "output")

    print(f"[1/4] 数据集 {profile['display_name']}，fact 行数 = {len(fact):,}")
    c = cube.build_cube(fact, profile)
    print(f"[2/4] 立方体：订单 {c['meta']['n_orders']:,}，客户 {c['meta']['n_customers']:,}，"
          f"复购率 {c['meta']['repeat_rate']*100:.1f}%")

    print("[3/4] 生成交互看板 ...")
    dash_path = dashboard.generate_dashboard(c, profile, output_dir)
    print(f"      -> {dash_path}")

    print("[4/4] 生成分析报告 ...")
    summary = insights.compute_summary(c, profile)
    llm_cfg = dict(cfg.get("llm", {}))
    if args.no_llm:
        llm_cfg["api_key"] = None
    rep = report.generate_report(summary, profile, llm_cfg, output_dir)
    print(f"      -> {rep['html']}  (叙述来源: {'DeepSeek' if rep['llm_used'] else '规则模板'})")

    print("\n完成。看板 output/dashboard.html，报告 output/report.html")


if __name__ == "__main__":
    main()
