"""下载运行所需资源（不随仓库提交）：plotly.min.js + 示例数据集。

用法：python download_data.py
"""
import os
import shutil
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PLOTLY_URL = "https://cdn.plot.ly/plotly-2.35.2.min.js"


def download_plotly():
    dest = os.path.join(ROOT, "src", "assets", "plotly.min.js")
    if os.path.exists(dest):
        print("[跳过] plotly.min.js 已存在")
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("[下载] plotly.min.js ...")
    urllib.request.urlretrieve(PLOTLY_URL, dest)
    print(f"  -> {dest}")


def _copy_csvs(src_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for f in os.listdir(src_dir):
        if f.lower().endswith(".csv"):
            shutil.copy(os.path.join(src_dir, f), os.path.join(dest_dir, f))


def download_datasets():
    import kagglehub

    # Olist 巴西电商
    p = kagglehub.dataset_download("olistbr/brazilian-ecommerce")
    dest = os.path.join(ROOT, "datasets", "olist", "data")
    _copy_csvs(p, dest)
    print(f"[下载] Olist -> {dest}")

    # UK 线上零售
    p2 = kagglehub.dataset_download("carrie1/ecommerce-data")
    dest2 = os.path.join(ROOT, "datasets", "uk_retail", "data")
    os.makedirs(dest2, exist_ok=True)
    shutil.copy(os.path.join(p2, "data.csv"), os.path.join(dest2, "data.csv"))
    print(f"[下载] UK Retail -> {dest2}")


if __name__ == "__main__":
    download_plotly()
    download_datasets()
    print("完成。现在可运行：python run.py olist  或  python run.py uk_retail")
