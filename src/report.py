"""通用报告：指标卡 + GMV 趋势图(标异动) + 异动下钻 + 建议。"""
import os
import json
import datetime

import requests
import markdown


def _money(v, cur):
    if v >= 1e6:
        return f"{cur}{v/1e6:,.2f}M"
    if v >= 1e3:
        return f"{cur}{v/1e3:,.1f}K"
    return f"{cur}{v:,.0f}"


def _fmt_anomaly(a, cur):
    if a["type"] == "GMV峰值":
        s = f"{a['month']} 峰值 {_money(a['gmv'], cur)}"
        if a.get("mom") is not None:
            s += f"（环比 {a['mom']*100:+.1f}%）"
        return s
    if a["type"] == "GMV下滑":
        return f"{a['month']} GMV 环比 {a['mom']*100:+.1f}%"
    if a["type"] == "GMV激增":
        return f"{a['month']} GMV 环比 {a['mom']*100:+.1f}%"
    return f"{a['month']} {a['type']}"


def build_prompt(summary, profile):
    m = summary["metrics"]
    cur = m["currency"]
    dims = {d["key"]: d["label"] for d in profile.get("dimensions", [])}
    order = [k for k in profile.get("drilldown", []) if k in dims]
    lines = []
    lines.append(f"你是资深电商数据分析师。基于「{profile['display_name']}」数据，"
                 "只输出两块：异动下钻、优化建议。语言极度精炼，不写空话，不重复正常趋势。")
    lines.append("")
    lines.append("【核心指标】")
    lines.append(f"GMV {_money(m['gmv'], cur)}；订单量 {m['orders']:,}；"
                 f"客单价 {_money(m['aov'], cur)}；复购率 {m['repeat_rate']*100:.1f}%。")
    lines.append("")
    lines.append("【已识别异动点】")
    for a in summary["anomalies"]:
        lines.append(f"- {_fmt_anomaly(a, cur)}")
    for key in order:
        lines.append("")
        lines.append(f"【分月×{dims[key]} GMV 下钻】")
        lines.append(json.dumps(summary["drill"][key], ensure_ascii=False))
    lines.append("")
    lines.append("【输出格式（Markdown）】")
    lines.append("### 异动下钻")
    drill_path = " → ".join(dims[k] for k in order) or "各维度"
    lines.append(f"针对每个异动点，按 {drill_path} 逐层下钻，只写影响最大的维度 + 量化贡献。")
    lines.append("### 优化建议")
    lines.append("2-4 条，每条对应影响最大的归因维度，格式=做什么+针对谁+预期效果。")
    lines.append("全文不超过 400 字，只使用提供的数据，不编造。")
    return "\n".join(lines)


def fallback_narrative(summary, profile):
    cur = summary["metrics"]["currency"]
    dims = {d["key"]: d["label"] for d in profile.get("dimensions", [])}
    lines = []
    lines.append("### 异动下钻")
    for a in summary["anomalies"]:
        lines.append(f"- {_fmt_anomaly(a, cur)}。")
    for key, label in dims.items():
        tv = summary["top_values"].get(key, [])
        if tv:
            lines.append(f"- {label}：" + "、".join(f"{r['value']}（{r['share']}）" for r in tv) + "。")
    lines.append("")
    lines.append("### 优化建议")
    for a in summary["anomalies"][:2]:
        lines.append(f"- 针对 {a['month']} 的 {a['type']}：结合主要维度做针对性运营。")
    return "\n".join(lines)


def call_deepseek(prompt, cfg):
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}",
               "Content-Type": "application/json"}
    payload = {
        "model": cfg.get("model", "deepseek-chat"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": cfg.get("temperature", 0.6),
        "max_tokens": cfg.get("max_tokens", 4096),
        "stream": False,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _metric_cards(m, kpi_cards):
    cur = m["currency"]
    card_map = {
        "gmv": ("GMV", _money(m["gmv"], cur)),
        "orders": ("订单量", f"{m['orders']:,}"),
        "aov": ("客单价", _money(m["aov"], cur)),
        "repeat_rate": ("复购率", f"{m['repeat_rate']*100:.1f}%"),
    }
    items = "".join(
        f'<div class="kpi"><div class="kpi-label">{card_map[k][0]}</div>'
        f'<div class="kpi-value">{card_map[k][1]}</div></div>'
        for k in kpi_cards if k in card_map
    )
    return f'<div class="kpi-row">{items}</div>'


def _svg_gmv_chart(monthly_gmv, anomalies, cur):
    months = [r["month"] for r in monthly_gmv]
    gmv = [r["gmv"] for r in monthly_gmv]
    n = len(gmv)
    W, H = 820, 320
    ml, mr, mt, mb = 64, 20, 34, 44
    pw, ph = W - ml - mr, H - mt - mb
    ymax = max(gmv) * 1.12 if gmv else 1.0

    def x(i):
        return ml + pw * (i / (n - 1)) if n > 1 else ml

    def y(v):
        return mt + ph * (1 - v / ymax)

    anom = {a["month"]: a for a in anomalies}
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" '
             f'font-family="system-ui,-apple-system,Segoe UI,sans-serif">']
    for i in range(5):
        val = ymax * i / 4
        yy = y(val)
        parts.append(f'<line x1="{ml}" y1="{yy:.1f}" x2="{W-mr}" y2="{yy:.1f}" '
                     f'stroke="#e1e0d9" stroke-width="1"/>')
        parts.append(f'<text x="{ml-8}" y="{yy+4:.1f}" text-anchor="end" font-size="11" '
                     f'fill="#898781">{_money(val, cur)}</text>')
    step = max(1, n // 6)
    for i in range(0, n, step):
        parts.append(f'<text x="{x(i):.1f}" y="{H-mb+18}" text-anchor="middle" font-size="11" '
                     f'fill="#898781">{months[i]}</text>')
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(gmv))
    bottom = mt + ph
    parts.append(f'<polygon points="{x(0):.1f},{bottom:.1f} {pts} {x(n-1):.1f},{bottom:.1f}" '
                 f'fill="#2a78d6" opacity="0.08"/>')
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#2a78d6" stroke-width="2" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')
    for i, m in enumerate(months):
        if m in anom:
            yy = y(gmv[i])
            label = anom[m]["type"]
            parts.append(f'<circle cx="{x(i):.1f}" cy="{yy:.1f}" r="4.5" fill="#eb6834"/>')
            ty = yy - 10 if yy > mt + 20 else yy + 20
            parts.append(f'<text x="{x(i):.1f}" y="{ty:.1f}" text-anchor="middle" font-size="11" '
                         f'fill="#eb6834">{label}</text>')
    parts.append('</svg>')
    return "".join(parts)


def generate_report(summary, profile, cfg, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    prompt = build_prompt(summary, profile)
    narrative = None
    llm_used = False
    api_key = cfg.get("api_key") or os.environ.get("DEEPSEEK_API_KEY")
    if api_key:
        try:
            call_cfg = dict(cfg)
            call_cfg["api_key"] = api_key
            narrative = call_deepseek(prompt, call_cfg)
            llm_used = bool(narrative and narrative.strip())
        except Exception as e:  # noqa: BLE001
            print(f"[report] LLM 调用失败，回退到规则版：{e}")
    if not narrative:
        narrative = fallback_narrative(summary, profile)

    m = summary["metrics"]
    cur = m["currency"]
    anomalies = summary["anomalies"]
    meta = (f"数据范围 {m['month_min']} ~ {m['month_max']} · "
            f"生成 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            f"{' · DeepSeek' if llm_used else ' · 规则模板'}")

    trend_ok = (f"整体从冷启动快速爬坡（后6月较前6月 {m['growth_first6_last6']*100:+.1f}%），"
                f"{m['peak_month']} 达峰值后进入高位平台期。")
    trend_note = trend_ok + " 异动点：" + "；".join(_fmt_anomaly(a, cur) for a in anomalies)

    kpi_cards = profile.get("kpi_cards", ["gmv", "orders", "aov", "repeat_rate"])
    body = (
        f'<h1>{profile["title"]}</h1>'
        f'<p class="meta">{meta}</p>'
        f'<h2>核心指标</h2>{_metric_cards(m, kpi_cards)}'
        f'<h2>GMV 月度趋势</h2>'
        f'<div class="chart">{_svg_gmv_chart(summary["monthly_gmv"], anomalies, cur)}</div>'
        f'<p class="trend-note">{trend_note}</p>'
        f'<h2>异动下钻与建议</h2>'
        f'<div class="narrative">{markdown.markdown(narrative, extensions=["tables"])}</div>'
    )

    html = (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{profile['title']}</title>"
        "<style>"
        "body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;max-width:860px;"
        "margin:32px auto;padding:0 20px;color:#0b0b0b;line-height:1.7}"
        "h1{font-size:22px;border-bottom:1px solid #e1e0d9;padding-bottom:8px}"
        "h2{font-size:16px;margin:26px 0 12px}"
        ".meta{color:#898781;font-size:12px;margin:-8px 0 4px}"
        ".kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:8px 0}"
        ".kpi{background:#fcfcfb;border:1px solid rgba(11,11,11,0.10);border-radius:10px;padding:14px 16px}"
        ".kpi-label{font-size:12px;color:#898781}"
        ".kpi-value{font-size:26px;font-weight:600;margin-top:4px}"
        ".chart{margin:8px 0}"
        ".trend-note{color:#52514e;font-size:13px;margin:6px 0}"
        ".narrative h3{font-size:15px;margin:20px 0 6px}"
        ".narrative ul{padding-left:20px;margin:6px 0}"
        "@media(max-width:640px){.kpi-row{grid-template-columns:repeat(2,1fr)}}"
        "</style></head><body>" + body + "</body></html>"
    )
    html_path = os.path.join(output_dir, "report.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    md = (f"# {profile['title']}\n\n> {meta}\n\n"
          f"## 核心指标\n\n"
          f"GMV **{_money(m['gmv'], cur)}** · 订单量 **{m['orders']:,}** · "
          f"客单价 **{_money(m['aov'], cur)}** · 复购率 **{m['repeat_rate']*100:.1f}%**\n\n"
          f"## GMV 趋势与异动\n\n{trend_note}\n\n{narrative}\n")
    md_path = os.path.join(output_dir, "report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    return {"md": md_path, "html": html_path, "llm_used": llm_used}
