# md-to-agent-response-html — 参考扩充

> 主流程见 `SKILL.md`。本文件按需打开，避免占满上下文。

## 摘要卡片（summary.html）骨架模板

仅作参考；实际内容须从 MD 抽取，**不要在没有信息时填占位文字**。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="color-scheme" content="light dark" />
  <title>{{标题}} · 摘要</title>
  <style>
    :root {
      --bg: #f4f6fa;
      --surface: #ffffff;
      --text: #1a2332;
      --muted: #5c6b7f;
      --accent: #2b6cb0;
      --accent-soft: rgba(43,108,176,0.12);
      --border: #e2e8f0;
      --shadow: 0 12px 40px rgba(26,35,50,0.10);
      --radius: 20px;
      --font: "Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #11161e; --surface: #1c2330; --text: #e8edf4;
        --muted: #9aacbf; --accent: #5aa3e0;
        --accent-soft: rgba(90,163,224,0.18);
        --border: #2d3848; --shadow: 0 12px 40px rgba(0,0,0,0.4);
      }
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh;
      display: grid; place-items: center;
      background: var(--bg); color: var(--text);
      font-family: var(--font); padding: clamp(16px,4vw,32px);
    }
    .card-link {
      display: block; text-decoration: none; color: inherit;
      max-width: 720px; width: 100%;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: clamp(20px,4vw,32px);
      transition: transform .2s ease, box-shadow .2s ease;
    }
    .card-link:hover .card,
    .card-link:focus-visible .card {
      transform: translateY(-3px);
      box-shadow: 0 18px 50px rgba(26,35,50,0.16);
    }
    .eyebrow { color: var(--accent); font-size: .85rem; letter-spacing: .04em; }
    h1 { margin: 6px 0 12px; font-size: clamp(1.4rem,3.6vw,1.9rem); }
    .lede { color: var(--muted); margin: 0 0 20px; line-height: 1.6; }
    .kpis {
      display: grid; gap: 12px;
      grid-template-columns: repeat(auto-fit,minmax(140px,1fr));
      margin: 18px 0 22px;
    }
    .kpi { background: var(--accent-soft); border-radius: 12px; padding: 12px 14px; }
    .kpi .num { font-size: clamp(1.4rem,3.4vw,1.7rem); font-weight: 700; color: var(--accent); }
    .kpi .label { font-size: .8rem; color: var(--muted); }
    ul.points { margin: 0; padding-left: 1.1rem; }
    ul.points li { margin: 6px 0; }
    .cta {
      display: inline-flex; align-items: center; gap: 8px;
      margin-top: 18px; padding: 10px 16px; border-radius: 999px;
      background: var(--accent); color: #fff; font-weight: 600;
    }
  </style>
</head>
<body>
  <a class="card-link" href="{{name}}.detail.html" aria-label="查看完整版">
    <article class="card">
      <div class="eyebrow">智能体响应 · 摘要卡片</div>
      <h1>{{标题}}</h1>
      <p class="lede">{{一句话摘要}}</p>

      <!-- 仅当 MD 中有真实数据时才渲染 -->
      <div class="kpis">
        <div class="kpi"><div class="num">{{N}}</div><div class="label">{{口径}}</div></div>
      </div>

      <ul class="points">
        <li>{{关键结论 1}}</li>
        <li>{{关键结论 2}}</li>
      </ul>

      <span class="cta">查看完整版 →</span>
    </article>
  </a>
</body>
</html>
```

## 详情页（detail.html）返回按钮骨架

```html
<a class="back-btn" href="{{name}}.summary.html" aria-label="返回摘要卡片">← 返回</a>

<style>
  .back-btn {
    position: fixed;
    top: clamp(12px, 2vw, 20px);
    left: clamp(12px, 2vw, 20px);
    z-index: 50;
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 14px;
    border-radius: 999px;
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    font-size: .9rem;
    text-decoration: none;
    backdrop-filter: blur(6px);
    transition: transform .15s ease, box-shadow .15s ease;
  }
  .back-btn:hover,
  .back-btn:focus-visible {
    transform: translateX(-2px);
    box-shadow: 0 6px 18px rgba(0,0,0,.15);
  }
  /* 避免被 hero 遮挡 */
  header.hero { padding-top: clamp(56px, 8vw, 72px); }
  @media (max-width: 480px) {
    .back-btn { font-size: .82rem; padding: 6px 10px; }
  }
</style>
```

## 抽取摘要的启发式速查

| MD 信号 | 摘要位置 |
|--------|---------|
| `# / ## 摘要 / 总结 / TL;DR / 结论` 段下文字 | 一句话摘要 / 结论 bullet |
| `**加粗短句**` | 关键结论 bullet 候选 |
| `> 引用块` | 关键结论或一句话摘要候选 |
| 表格里的数字单元格 | 指标卡的数字 |
| 行内 `数字%`、`N 倍`、`N 小时`、`N 次` | 指标卡候选（确认有上下文口径再放） |
| 末尾 `行动 / Next Steps / TODO` 列表 | CTA 文案灵感（但 CTA 仍只跳详情） |

## 常见坑

- **绝对路径跳转**：开发机能跑、用户拷贝走就 404。一律相对路径。
- **summary 内嵌 `<a>` 套 `<a>`**：浏览器会拆开，键盘语义错乱。整卡跳转用最外层 `<a class="card-link">` 包裹。
- **返回按钮被 hero 渐变盖住**：把 `header.hero` 的 `padding-top` 加大，或给 `.back-btn` 更深底色 + 阴影。
- **深色模式下按钮看不见**：返回按钮和卡片都依赖 `var(--surface)` / `var(--border)`，确保深色变量已定义。
- **中文文件名编码**：`href` 直接写中文即可，让浏览器编码；手写 `%XX` 反而易错。
- **摘要卡灌水**：MD 里没有的数字 / 结论坚决不要造，宁可摘要卡更短。

## 与 md-to-rich-html 的复用建议

- detail.html 的版式、SVG 启发式、配色变量 **直接复用** `md-to-rich-html` 的规范（见其 `SKILL.md` 与 `reference.md`）。
- 只额外满足两点差异：左上角"返回"按钮、文件名以 `.detail.html` 结尾。
- 摘要卡片的变量名建议与 detail 完全一致（`--bg / --surface / --text / --muted / --accent / --border / --shadow / --radius`），方便后续整体换肤。
