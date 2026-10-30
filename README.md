# 通用数据看板 & 分析报告 Agent

一套「数据集配置驱动」的通用工作流：给任意交易型数据集写一份 profile，就能自动产出
**交互式看板** + **分析报告**。

- **看板**：单文件 HTML，时间筛选 / 粒度切换 / 播放动画 / 深浅色主题，双击即开
- **报告**：指标卡 → GMV 折线图标异动 → 异动下钻（量化归因）→ 优化建议，LLM 写叙述

## 特性

- **换数据集只写两个文件**（`prepare.py` + `profile.yaml`），引擎零改动
- 通用指标：GMV / 订单量 / 客单价 / 平均每单件数 / 唯一客户数 / 复购率
- 规则化异动检测（GMV 峰值 + 最大环比突变）+ 按维度下钻归因
- 已接入：Olist 巴西电商（9 表关系型）、UK 线上零售（单文件）

## 快速开始

```bash
# 1) 依赖
pip install -r requirements.txt

# 2) 下载资源（数据集 + plotly.js，不随仓库提交）
python download_data.py

# 3) 配置 LLM（用于报告叙述，可选）
cp config.example.yaml config.yaml
# 编辑 config.yaml 填入 api_key，或设置环境变量 DEEPSEEK_API_KEY（推荐）

# 4) 运行
python run.py olist       # Olist 巴西电商
python run.py uk_retail   # UK 线上零售
python run.py olist --no-llm   # 跳过 LLM，规则版报告
```

产出在 `datasets/<name>/output/`，转 PDF：`python export_pdf.py`（需本机 Edge/Chrome）。

## 目录结构

```
├── run.py                 # 入口：python run.py <数据集名>
├── download_data.py       # 下载数据集 + plotly.js
├── config.example.yaml    # 配置模板（复制为 config.yaml）
├── export_pdf.py          # HTML -> PDF
├── src/
│   ├── schema.py          # profile 加载 + canonical fact 约定
│   ├── cube.py            # 通用 OLAP 立方体（月 × 维度）
│   ├── insights.py        # 指标 + 异动检测 + 下钻表
│   ├── report.py          # 指标卡 + 折线图 + LLM 叙述
│   ├── dashboard.py       # 单 HTML 交互看板
│   └── assets/plotly.min.js   # 由 download_data.py 获取
└── datasets/
    ├── olist/
    │   ├── profile.yaml   # 维度/下钻顺序/币种/标题
    │   ├── prepare.py     # 原始数据 -> canonical fact
    │   └── data/          # 原始 CSV（不提交，下载获取）
    └── uk_retail/
        ├── profile.yaml
        ├── prepare.py
        └── data/
```

## 接入新数据集（三步）

1. 建目录 `datasets/<name>/`，放原始数据到 `data/`。
2. 写 `prepare.py`，产出 **canonical fact**（DataFrame，行粒度）：

   | 必需列 | 说明 |
   |---|---|
   | `order_id` | 交易/订单唯一键 |
   | `customer_id` | 复购实体键（用于算复购率） |
   | `timestamp` | 时间戳 |
   | `amount` | 金额（销售额） |
   | `quantity`(可选) | 数量，默认 1 |
   | 维度列 | 任意离散字符串列 |

3. 写 `profile.yaml`：

   ```yaml
   name: my_data
   display_name: 我的数据集
   title: 我的数据分析报告
   currency: "¥"
   dimensions:
     - {key: region, column: region, label: 地区}
     - {key: category, column: category, label: 类目}
   drilldown: [region, category]          # 下钻优先级
   kpi_cards: [gmv, orders, aov, repeat_rate]
   ```

然后 `python run.py my_data` 即可。

## 数据来源与许可

| 数据集 | 来源 | 许可 |
|---|---|---|
| Olist 巴西电商 | [Kaggle · olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | CC BY-NC-SA 4.0（非商用） |
| UK 线上零售 | [Kaggle · carrie1/ecommerce-data](https://www.kaggle.com/datasets/carrie1/ecommerce-data)（UCI Online Retail） | 研究用途 |

数据与 `plotly.min.js` **不随仓库提交**，用 `python download_data.py` 获取。

## 隐私说明

- `config.yaml`（含 API 密钥）已被 `.gitignore` 忽略，**不会上传**。切勿手动 `git add config.yaml`。
- 更安全：用环境变量 `DEEPSEEK_API_KEY` 提供密钥，不写入任何文件。

## License

[MIT](LICENSE)
