"""通用交互看板：单 HTML，Plotly 前端重算，维度图表由 profile 驱动。"""
import os
import json

_PLOTLY_JS = os.path.join(os.path.dirname(__file__), "assets", "plotly.min.js")

_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; }
  .viz-root {
    color-scheme: light;
    --page: #f9f9f7; --surface: #fcfcfb;
    --ink: #0b0b0b; --secondary: #52514e; --muted: #898781;
    --grid: #e1e0d9; --baseline: #c3c2b7; --border: rgba(11,11,11,0.10);
    --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;
    --s5: #e87ba4; --s6: #008300; --s7: #6250d6; --s8: #e34948;
    background: var(--page); min-height: 100vh; color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  .viz-root[data-theme="dark"] {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19;
    --ink: #f0efec; --secondary: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --baseline: #383835; --border: rgba(255,255,255,0.10);
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
    --s5: #d55181; --s6: #008300; --s7: #9085e9; --s8: #e66767;
  }
  .topbar { display:flex; justify-content:space-between; align-items:flex-start; padding:24px 20px 0; gap:16px; }
  .topbar h1 { font-size:22px; margin:0; }
  .subtitle { color:var(--secondary); font-size:13px; margin-top:6px; }
  .filters { display:flex; flex-wrap:wrap; align-items:center; gap:10px; padding:16px 20px 0; }
  .filters .lbl { color:var(--muted); font-size:13px; }
  select, button { background:var(--surface); color:var(--ink); border:1px solid var(--border);
    border-radius:6px; padding:6px 10px; font:inherit; font-size:13px; cursor:pointer; }
  button.preset.active { border-color:var(--s1); color:var(--s1); }
  button.play { background:var(--s1); color:#fff; border:none; }
  button.play.on { background:var(--s4); color:#0b0b0b; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; padding:16px 20px 0; }
  .tile { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:14px 16px; }
  .tile-label { font-size:12px; color:var(--muted); }
  .tile-value { font-size:24px; font-weight:600; margin-top:4px; }
  .grid { display:grid; grid-template-columns:repeat(2,1fr); gap:16px; padding:16px 20px 0; }
  .card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:12px 14px; }
  .card.wide { grid-column:1 / -1; }
  .plot { width:100%; height:340px; }
  .table-section { padding:20px; }
  .table-section h2 { font-size:15px; }
  table { border-collapse:collapse; width:100%; font-size:13px; background:var(--surface); }
  th, td { border:1px solid var(--border); padding:6px 10px; text-align:right; font-variant-numeric:tabular-nums; }
  th { background:var(--grid); color:var(--secondary); font-weight:600; }
  th:first-child, td:first-child { text-align:left; }
  footer { padding:8px 20px 24px; color:var(--muted); font-size:12px; }
  @media (max-width:900px){ .grid { grid-template-columns:1fr; } }
  @page { size: A4; margin: 12mm; }
  @media print {
    .filters, .topbar button { display:none; }
    .grid { grid-template-columns:1fr; }
    .card, .tile { break-inside:avoid; page-break-inside:avoid; }
    .plot { height:300px; }
    footer { display:none; }
  }
</style>
</head>
<body>
<div class="viz-root" id="root">
  <header class="topbar">
    <div>
      <h1>__TITLE__</h1>
      <div class="subtitle" id="subtitle"></div>
    </div>
    <button id="themeBtn">&#127769; 深浅色</button>
  </header>

  <div class="filters">
    <span class="lbl">时间范围</span>
    <button class="preset active" data-preset="all">全部</button>
    <button class="preset" data-preset="12">近12月</button>
    <button class="preset" data-preset="6">近6月</button>
    <button class="preset" data-preset="3">近3月</button>
    <label class="lbl">起 <select id="startSel"></select></label>
    <label class="lbl">止 <select id="endSel"></select></label>
    <span class="lbl">粒度</span>
    <select id="granSel">
      <option value="day">日</option>
      <option value="week">周</option>
      <option value="month" selected>月</option>
    </select>
    <button id="playBtn" class="play">&#9654; 播放</button>
  </div>

  <section class="kpis" id="kpis"></section>

  <div class="grid">
    <div class="card wide"><div class="plot" id="chart-gmv"></div></div>
    <div class="card"><div class="plot" id="chart-orders"></div></div>
    __DIM_DIVS__
  </div>

  <section class="table-section">
    <h2>月度明细表</h2>
    <div id="tableWrap"></div>
  </section>

  <footer>数据源：__DISPLAY_NAME__ · GMV = 销售额（__CURRENCY__）</footer>
</div>
<script>__PLOTLY_JS__</script>
<script>
'use strict';
const CUBE = __CUBE_JSON__;
const META = CUBE.meta;
const months = CUBE.months;

const THEMES = {
  light: { surface:'#fcfcfb', ink:'#0b0b0b', secondary:'#52514e', muted:'#898781',
    grid:'#e1e0d9', baseline:'#c3c2b7',
    series:['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300','#6250d6','#e34948'] },
  dark:  { surface:'#1a1a19', ink:'#f0efec', secondary:'#c3c2b7', muted:'#898781',
    grid:'#2c2c2a', baseline:'#383835',
    series:['#3987e5','#d95926','#199e70','#c98500','#d55181','#008300','#9085e9','#e66767'] }
};

let T = THEMES.light;
let startIdx = 0, endIdx = months.length - 1;
let gran = 'month';
let playing = false, playTimer = null;
const root = document.getElementById('root');

function fmtMoney(v){
  v = v || 0;
  const c = META.currency || '';
  if (Math.abs(v) >= 1e6) return c + (v/1e6).toFixed(2) + 'M';
  if (Math.abs(v) >= 1e3) return c + (v/1e3).toFixed(1) + 'K';
  return c + Math.round(v).toLocaleString('en-US');
}
function fmtNum(v){
  v = v || 0;
  if (Math.abs(v) >= 1e6) return (v/1e6).toFixed(1)+'M';
  if (Math.abs(v) >= 1e3) return (v/1e3).toFixed(1)+'K';
  return Math.round(v).toLocaleString('en-US');
}
function hexToRgba(hex, a){
  const h = hex.replace('#','');
  return 'rgba('+parseInt(h.slice(0,2),16)+','+parseInt(h.slice(2,4),16)+','+parseInt(h.slice(4,6),16)+','+a+')';
}
function inRange(m){ return m >= months[startIdx] && m <= months[endIdx]; }
function weekKey(d){
  const dt = new Date(d + 'T00:00:00Z');
  const day = (dt.getUTCDay()+6)%7;
  const s = new Date(dt); s.setUTCDate(dt.getUTCDate()-day);
  return s.toISOString().slice(0,10);
}
function monthlyAcc(){
  const a = {gmv:0, orders:0, items:0};
  for (const r of CUBE.monthly){ if (inRange(r.month)){ a.gmv+=r.gmv; a.orders+=r.orders; a.items+=(r.items||0); } }
  return a;
}
function dailySeries(){
  const g = {}, order = [];
  for (const r of CUBE.daily){
    const m = r.date.slice(0,7);
    if (!inRange(m)) continue;
    let k = m;
    if (gran==='day') k = r.date;
    else if (gran==='week') k = weekKey(r.date);
    if (!g[k]){ g[k] = {gmv:0, orders:0}; order.push(k); }
    g[k].gmv += r.gmv; g[k].orders += r.orders;
  }
  return order.map(k => ({x:k, gmv:g[k].gmv, orders:g[k].orders}));
}
function aggDim(key){
  const map = {};
  for (const r of CUBE.dims[key]){
    if (!inRange(r.month)) continue;
    if (!map[r.value]) map[r.value] = {value:r.value, gmv:0, orders:0};
    map[r.value].gmv += r.gmv; map[r.value].orders += r.orders;
  }
  return Object.values(map);
}
function baseLayout(title){
  return {
    title:{text:title, font:{size:14, color:T.ink}, x:0, xanchor:'left'},
    paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
    font:{family:'system-ui, -apple-system, "Segoe UI", sans-serif', size:12, color:T.secondary},
    margin:{l:54, r:16, t:44, b:44},
    xaxis:{gridcolor:T.grid, zeroline:false, linecolor:T.baseline, tickfont:{color:T.muted}, fixedrange:true, automargin:true},
    yaxis:{gridcolor:T.grid, zeroline:false, linecolor:T.baseline, tickfont:{color:T.muted}, fixedrange:true},
    showlegend:false, autosize:true, bargap:0.25
  };
}
const plotOpts = {responsive:true, displayModeBar:false};

function renderSubtitle(){
  document.getElementById('subtitle').textContent =
    '数据范围 ' + META.month_min + ' ~ ' + META.month_max +
    ' · 订单量 ' + fmtNum(META.n_orders) + ' · 复购率 ' + (META.repeat_rate*100).toFixed(1) + '%';
}
function renderKpis(){
  const a = monthlyAcc();
  const aov = a.orders ? a.gmv/a.orders : 0;
  const cards = META.kpi_cards || ['gmv','orders','aov','repeat_rate'];
  const el = document.getElementById('kpis');
  el.innerHTML = '';
  for (const k of cards){
    let label, value;
    if (k === 'gmv'){ label = 'GMV'; value = fmtMoney(a.gmv); }
    else if (k === 'orders'){ label = '订单量'; value = fmtNum(a.orders); }
    else if (k === 'aov'){ label = '客单价'; value = fmtMoney(aov); }
    else if (k === 'repeat_rate'){ label = '复购率(全期)'; value = (META.repeat_rate*100).toFixed(1)+'%'; }
    else continue;
    const div = document.createElement('div'); div.className = 'tile';
    const lab = document.createElement('div'); lab.className = 'tile-label'; lab.textContent = label;
    const val = document.createElement('div'); val.className = 'tile-value'; val.textContent = value;
    div.appendChild(lab); div.appendChild(val);
    el.appendChild(div);
  }
}
function renderGmv(){
  const d = dailySeries();
  const trace = {type:'scatter', mode:'lines', x:d.map(r=>r.x), y:d.map(r=>r.gmv),
    line:{color:T.series[0], width:2}, fill:'tozeroy', fillcolor:hexToRgba(T.series[0], 0.10),
    hovertemplate:'%{x}<br>GMV：%{y:,.0f}<extra></extra>'};
  const layout = baseLayout('GMV 趋势');
  layout.hovermode = 'x unified';
  layout.yaxis.tickformat = '~s'; layout.yaxis.tickprefix = META.currency || '';
  Plotly.react('chart-gmv', [trace], layout, plotOpts);
}
function renderOrders(){
  const d = dailySeries();
  const trace = {type:'bar', x:d.map(r=>r.x), y:d.map(r=>r.orders),
    marker:{color:T.series[0]},
    hovertemplate:'%{x}<br>订单量：%{y:,}<extra></extra>'};
  const layout = baseLayout('订单量趋势');
  layout.yaxis.tickformat = '~s';
  Plotly.react('chart-orders', [trace], layout, plotOpts);
}
function renderDims(){
  for (const d of META.dimensions){
    const rows = aggDim(d.key).sort((a,b)=>b.gmv-a.gmv).slice(0,10);
    const trace = {type:'bar', orientation:'h', y:rows.map(r=>r.value), x:rows.map(r=>r.gmv),
      marker:{color:T.series[0]},
      text:rows.map(r=>fmtMoney(r.gmv)), textposition:'outside', cliponaxis:false,
      customdata:rows.map(r=>r.orders),
      hovertemplate:'%{y}<br>GMV：%{x:,.0f}<br>订单：%{customdata:,}<extra></extra>'};
    const layout = baseLayout(d.label + ' Top10');
    layout.yaxis.autorange = 'reversed';
    layout.xaxis.tickformat = '~s'; layout.xaxis.tickprefix = META.currency || '';
    layout.margin.r = 74;
    Plotly.react('dim-' + d.key, [trace], layout, plotOpts);
  }
}
function renderTable(){
  const ms = CUBE.monthly.filter(r=>inRange(r.month));
  const wrap = document.getElementById('tableWrap');
  wrap.innerHTML = '';
  const table = document.createElement('table');
  const heads = ['月份','GMV','订单量','客单价'];
  const hr = document.createElement('tr');
  heads.forEach(h=>{ const th = document.createElement('th'); th.textContent = h; hr.appendChild(th); });
  table.appendChild(hr);
  for (const r of ms){
    const aov = r.orders ? r.gmv/r.orders : 0;
    const cells = [r.month, fmtMoney(r.gmv), fmtNum(r.orders), fmtMoney(aov)];
    const tr = document.createElement('tr');
    cells.forEach(c=>{ const td = document.createElement('td'); td.textContent = c; tr.appendChild(td); });
    table.appendChild(tr);
  }
  wrap.appendChild(table);
}
function renderAll(){
  renderSubtitle(); renderKpis();
  renderGmv(); renderOrders(); renderDims(); renderTable();
}
function syncSelects(){
  document.getElementById('startSel').value = startIdx;
  document.getElementById('endSel').value = endIdx;
  document.querySelectorAll('.preset').forEach(b=>{
    const n = b.dataset.preset;
    const isAll = n==='all' && startIdx===0 && endIdx===months.length-1;
    const isN = n!=='all' && startIdx===months.length-(+n) && endIdx===months.length-1;
    b.classList.toggle('active', isAll || isN);
  });
}
function populateSelects(){
  const ss = document.getElementById('startSel'), es = document.getElementById('endSel');
  months.forEach((m,i)=>{
    const o1 = document.createElement('option'); o1.value = i; o1.textContent = m; ss.appendChild(o1);
    const o2 = document.createElement('option'); o2.value = i; o2.textContent = m; es.appendChild(o2);
  });
}
function togglePlay(){
  const btn = document.getElementById('playBtn');
  if (playing){ clearInterval(playTimer); playing=false; btn.classList.remove('on'); btn.textContent='▶ 播放'; return; }
  playing = true; btn.classList.add('on'); btn.textContent='⏸ 暂停';
  startIdx = 0; endIdx = 0; renderAll(); syncSelects();
  playTimer = setInterval(()=>{
    if (endIdx < months.length-1){ endIdx++; renderAll(); syncSelects(); }
    else { clearInterval(playTimer); playing=false; btn.classList.remove('on'); btn.textContent='▶ 播放'; }
  }, 500);
}
function applyTheme(mode){
  root.setAttribute('data-theme', mode);
  T = THEMES[mode];
  renderAll();
}

populateSelects();
document.getElementById('startSel').addEventListener('change', e=>{ startIdx = Math.min(+e.target.value, endIdx); renderAll(); syncSelects(); });
document.getElementById('endSel').addEventListener('change', e=>{ endIdx = Math.max(+e.target.value, startIdx); renderAll(); syncSelects(); });
document.getElementById('granSel').addEventListener('change', e=>{ gran = e.target.value; renderGmv(); renderOrders(); });
document.querySelectorAll('.preset').forEach(b=>b.addEventListener('click', ()=>{
  const n = b.dataset.preset;
  if (n==='all'){ startIdx=0; endIdx=months.length-1; }
  else { endIdx = months.length-1; startIdx = Math.max(0, months.length-(+n)); }
  renderAll(); syncSelects();
}));
document.getElementById('playBtn').addEventListener('click', togglePlay);
document.getElementById('themeBtn').addEventListener('click', ()=>{
  const cur = root.getAttribute('data-theme')==='dark' ? 'dark' : 'light';
  applyTheme(cur==='light' ? 'dark' : 'light');
});
const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
applyTheme(prefersDark ? 'dark' : 'light');
</script>
</body>
</html>
"""


def generate_dashboard(cube, profile, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    cube_json = json.dumps(cube, ensure_ascii=False).replace("</", "<\\/")
    dim_divs = "".join(
        f'<div class="card"><div class="plot" id="dim-{d["key"]}"></div></div>'
        for d in profile.get("dimensions", [])
    )
    with open(_PLOTLY_JS, encoding="utf-8") as f:
        plotly_js = f.read()

    html = (_TEMPLATE
            .replace("__TITLE__", profile.get("title", profile["display_name"]))
            .replace("__DISPLAY_NAME__", profile["display_name"])
            .replace("__CURRENCY__", profile.get("currency", ""))
            .replace("__DIM_DIVS__", dim_divs)
            .replace("__PLOTLY_JS__", plotly_js)
            .replace("__CUBE_JSON__", cube_json))

    path = os.path.join(output_dir, "dashboard.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
