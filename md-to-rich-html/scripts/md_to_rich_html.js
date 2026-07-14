#!/usr/bin/env node
/**
 * Markdown → 富表现单文件 HTML（md-to-rich-html skill 参考实现）
 * Usage: node .cursor/skills/md-to-rich-html/scripts/md_to_rich_html.js [--sidebar-toc] <input.md> [output.html]
 */
const fs = require('fs');
const path = require('path');

const CSS = `
    :root {
      --bg: #f4f6fa;
      --surface: #ffffff;
      --text: #1a2332;
      --muted: #5c6b7f;
      --accent: #0d6e6e;
      --accent-soft: rgba(13, 110, 110, 0.12);
      --accent-2: #c45c26;
      --border: #e2e8f0;
      --shadow: 0 8px 30px rgba(26, 35, 50, 0.08);
      --radius: 14px;
      --font: "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      --mono: ui-monospace, "Cascadia Code", "SF Mono", Consolas, monospace;
    }
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #12171f;
        --surface: #1c2430;
        --text: #e8edf4;
        --muted: #9aacbf;
        --accent: #3db8b8;
        --accent-soft: rgba(61, 184, 184, 0.15);
        --accent-2: #e88a52;
        --border: #2d3848;
        --shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
      }
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      font-family: var(--font);
      font-size: clamp(15px, 2.8vw, 17px);
      line-height: 1.65;
      color: var(--text);
      background: var(--bg);
      -webkit-font-smoothing: antialiased;
    }
    .wrap {
      max-width: 920px;
      margin: 0 auto;
      padding: clamp(16px, 4vw, 28px);
      padding-bottom: 48px;
    }
    header.hero {
      background: linear-gradient(135deg, var(--accent) 0%, #0a4d52 55%, #063842 100%);
      color: #fff;
      border-radius: var(--radius);
      padding: clamp(22px, 5vw, 40px);
      margin-bottom: 28px;
      box-shadow: var(--shadow);
      position: relative;
      overflow: hidden;
    }
    header.hero::after {
      content: "";
      position: absolute;
      right: -20%;
      top: -40%;
      width: 60%;
      height: 180%;
      background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
      pointer-events: none;
    }
    header.hero h1 {
      margin: 0 0 12px;
      font-size: clamp(1.35rem, 4.5vw, 1.85rem);
      font-weight: 700;
      letter-spacing: -0.02em;
      position: relative;
      z-index: 1;
    }
    header.hero .meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 8px 16px;
      margin-top: 12px;
      position: relative;
      z-index: 1;
    }
    header.hero .meta-item {
      font-size: 0.88rem;
      color: rgba(255, 255, 255, 0.94);
    }
    header.hero .meta-item strong { color: #fff; }
    header.hero .badge {
      display: inline-block;
      margin-top: 14px;
      padding: 6px 12px;
      background: rgba(255,255,255,0.18);
      border-radius: 999px;
      font-size: 0.82rem;
      position: relative;
      z-index: 1;
    }
    nav.toc {
      background: var(--surface);
      border-radius: var(--radius);
      padding: clamp(16px, 3vw, 22px);
      margin-bottom: 22px;
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
    }
    nav.toc h2 {
      margin: 0 0 12px;
      font-size: 0.95rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    nav.toc ol {
      margin: 0;
      padding-left: 1.25em;
      columns: 2;
      column-gap: 24px;
    }
    @media (max-width: 520px) { nav.toc ol { columns: 1; } }
    nav.toc a { color: var(--accent); text-decoration: none; font-size: 0.92rem; }
    nav.toc a:hover { text-decoration: underline; }
    section {
      background: var(--surface);
      border-radius: var(--radius);
      padding: clamp(18px, 4vw, 26px);
      margin-bottom: 22px;
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
    }
    section > h2 {
      margin: 0 0 16px;
      font-size: clamp(1.12rem, 3.2vw, 1.35rem);
      color: var(--accent);
      border-left: 4px solid var(--accent);
      padding-left: 12px;
    }
    section h3 {
      margin: 22px 0 10px;
      font-size: 1.05rem;
      color: var(--text);
    }
    section h3:first-of-type { margin-top: 0; }
    p { margin: 0 0 12px; color: var(--text); }
    p:last-child { margin-bottom: 0; }
    ul, ol {
      margin: 8px 0 12px;
      padding-left: 1.25em;
      color: var(--text);
    }
    li { margin-bottom: 8px; }
    li strong { color: var(--accent); }
    .table-wrap { overflow-x: auto; margin: 14px 0; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }
    th, td {
      padding: 10px 12px;
      border: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }
    th {
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 600;
    }
    tr:nth-child(even) td { background: var(--bg); }
    code {
      font-family: var(--mono);
      font-size: 0.88em;
      padding: 2px 7px;
      border-radius: 6px;
      background: var(--accent-soft);
      color: var(--accent);
    }
    pre {
      margin: 14px 0;
      padding: 14px 16px;
      border-radius: 10px;
      background: var(--bg);
      border: 1px dashed var(--border);
      overflow-x: auto;
      font-family: var(--mono);
      font-size: 0.82rem;
      line-height: 1.55;
      color: var(--text);
      white-space: pre-wrap;
    }
    .callout {
      margin: 14px 0;
      padding: 14px 16px;
      border-radius: 10px;
      background: var(--accent-soft);
      border-left: 4px solid var(--accent);
      font-size: 0.95rem;
    }
    .callout strong { color: var(--accent); }
    .cards-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin: 16px 0;
    }
    @media (max-width: 680px) { .cards-3 { grid-template-columns: 1fr; } }
    .mini-card {
      border-radius: 12px;
      padding: 16px;
      border: 1px solid var(--border);
      background: linear-gradient(160deg, var(--surface) 0%, var(--bg) 100%);
    }
    .mini-card h4 {
      margin: 0 0 8px;
      font-size: 0.95rem;
      color: var(--accent);
    }
    .mini-card p { margin: 0; font-size: 0.88rem; color: var(--muted); line-height: 1.5; }
    .figure {
      margin: 18px 0;
      padding: 16px;
      border-radius: 12px;
      background: var(--bg);
      border: 1px dashed var(--border);
      overflow-x: auto;
    }
    .figure-caption {
      font-size: 0.85rem;
      color: var(--muted);
      margin-top: 12px;
      text-align: center;
    }
    svg.diagram { display: block; max-width: 100%; height: auto; margin: 0 auto; }
    .case-card {
      border-radius: 12px;
      padding: 16px;
      border: 1px solid var(--border);
      margin-bottom: 14px;
      background: var(--bg);
    }
    .case-card:last-child { margin-bottom: 0; }
    .case-card h3 { margin-top: 0; color: var(--accent-2); }
    footer {
      text-align: center;
      color: var(--muted);
      font-size: 0.82rem;
      padding: 16px 8px 0;
    }

    /* ---------- 左侧悬浮章节目录 ---------- */
    .page-layout {
      display: grid;
      grid-template-columns: minmax(200px, 248px) minmax(0, 1fr);
      gap: clamp(16px, 3vw, 32px);
      max-width: 1280px;
      margin: 0 auto;
      padding: clamp(16px, 4vw, 28px);
      padding-bottom: 48px;
      align-items: start;
    }
    .page-layout .content { min-width: 0; }
    .page-layout .content .wrap {
      max-width: none;
      margin: 0;
      padding: 0;
    }
    aside.sidebar-toc {
      position: sticky;
      top: 16px;
      align-self: start;
      max-height: calc(100vh - 32px);
      overflow-y: auto;
      overscroll-behavior: contain;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 14px 12px 16px;
      z-index: 20;
    }
    aside.sidebar-toc .toc-title {
      margin: 0 0 10px;
      padding: 0 6px 8px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
    }
    aside.sidebar-toc nav ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    aside.sidebar-toc nav > ul > li { margin-bottom: 4px; }
    aside.sidebar-toc a {
      display: block;
      padding: 5px 8px;
      border-radius: 8px;
      color: var(--text);
      text-decoration: none;
      font-size: 0.84rem;
      line-height: 1.45;
      border-left: 3px solid transparent;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
    }
    aside.sidebar-toc a:hover {
      background: var(--accent-soft);
      color: var(--accent);
    }
    aside.sidebar-toc a.active {
      background: var(--accent-soft);
      color: var(--accent);
      border-left-color: var(--accent);
      font-weight: 600;
    }
    aside.sidebar-toc nav ul ul {
      margin: 2px 0 6px 10px;
      padding-left: 8px;
      border-left: 1px solid var(--border);
    }
    aside.sidebar-toc nav ul ul a {
      font-size: 0.78rem;
      color: var(--muted);
      padding: 3px 8px;
    }
    .toc-toggle {
      display: none;
      position: fixed;
      left: 12px;
      bottom: 16px;
      z-index: 30;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--surface);
      color: var(--accent);
      font-size: 0.85rem;
      font-weight: 600;
      box-shadow: var(--shadow);
      cursor: pointer;
      font-family: var(--font);
    }
    .toc-backdrop {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.35);
      z-index: 15;
    }
    @media (max-width: 960px) {
      .page-layout { grid-template-columns: 1fr; padding-top: 12px; }
      aside.sidebar-toc {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: min(288px, 86vw);
        max-height: none;
        border-radius: 0 var(--radius) var(--radius) 0;
        transform: translateX(-105%);
        transition: transform 0.25s ease;
      }
      aside.sidebar-toc.open { transform: translateX(0); }
      .toc-backdrop.open { display: block; }
      .toc-toggle { display: inline-flex; align-items: center; gap: 6px; }
    }
    header.hero .intro-lines {
      margin: 0;
      position: relative;
      z-index: 1;
    }
    header.hero .intro-lines p {
      margin: 0 0 8px;
      color: rgba(255, 255, 255, 0.96);
      font-size: 0.92rem;
      line-height: 1.55;
    }
    header.hero .intro-lines p:last-child { margin-bottom: 0; }
    /* Hero 内联 code/strong 需高对比，避免被全局 accent 盖暗 */
    header.hero code {
      background: rgba(255, 255, 255, 0.22);
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.35);
    }
    header.hero strong {
      color: #fff;
      font-weight: 700;
    }

    /* ---------- 题目卡片 ---------- */
    ol { counter-reset: none; }
    li.quiz-item {
      margin-bottom: 16px;
      padding-left: 4px;
    }
    li.quiz-item::marker { color: var(--accent); font-weight: 700; }
    li.quiz-item .q-stem {
      color: var(--text);
      line-height: 1.6;
      margin-bottom: 6px;
    }
    li.quiz-item .q-options {
      list-style: none;
      margin: 0 0 8px;
      padding: 0;
      display: flex;
      flex-wrap: wrap;
      gap: 3px 22px;
    }
    li.quiz-item .q-options li {
      margin: 0;
      flex: 1 1 240px;
      font-size: 0.92rem;
      color: var(--muted);
    }
    li.quiz-item .q-answer {
      display: inline-flex;
      align-items: center;
      padding: 2px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    li.quiz-item .q-answer-label {
      opacity: 0.7;
      margin-right: 5px;
      font-weight: 500;
    }
    li.quiz-item .q-explain {
      display: block;
      margin-top: 6px;
      font-size: 0.88rem;
      color: var(--muted);
      line-height: 1.55;
    }

    /* ---------- 答案速查表 ---------- */
    table.answer-key { font-size: 0.9rem; }
    table.answer-key th,
    table.answer-key td { text-align: center; padding: 6px 10px; }
    table.answer-key td:nth-child(odd) { color: var(--muted); }
    table.answer-key td:nth-child(even) { font-weight: 600; color: var(--accent); }
    table.answer-key tr:nth-child(even) td:nth-child(even) { color: var(--accent); }

    /* ---------- 填空题 / 判断题 / 补充题库 通用卡片 ---------- */
    ol.fill-list, ol.judge-list, ol.qbank-list {
      list-style: none;
      margin: 8px 0 12px;
      padding: 0;
      counter-reset: item;
    }
    li.fill-item, li.judge-item, li.qbank-item {
      position: relative;
      margin: 0 0 12px;
      padding: 12px 14px 12px 46px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: linear-gradient(160deg, var(--surface) 0%, var(--bg) 100%);
      counter-increment: item;
    }
    li.fill-item:last-child, li.judge-item:last-child, li.qbank-item:last-child { margin-bottom: 0; }
    li.fill-item::before, li.judge-item::before, li.qbank-item::before {
      content: counter(item);
      position: absolute;
      left: 12px;
      top: 11px;
      width: 26px;
      height: 26px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: var(--accent-soft);
      color: var(--accent);
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    li.fill-item .q-stem, li.judge-item .q-stem, li.qbank-item .q-stem {
      color: var(--text);
      line-height: 1.65;
    }
    .fill-answer {
      margin-top: 8px;
      padding: 6px 12px;
      border-radius: 8px;
      background: var(--accent-soft);
      border-left: 3px solid var(--accent);
      font-size: 0.92rem;
    }
    .fill-answer .q-answer-label {
      font-weight: 700;
      color: var(--accent);
      margin-right: 6px;
    }
    .fill-answer .fill-note { color: var(--muted); font-size: 0.85rem; }

    /* ---------- 判断题 √ / × ---------- */
    .judge-answer { margin-top: 8px; font-size: 0.9rem; display: flex; align-items: baseline; gap: 8px; }
    .judge-badge {
      flex: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      font-size: 0.9rem;
      font-weight: 700;
      line-height: 1;
      transform: translateY(3px);
    }
    .judge-badge.t { background: rgba(22, 163, 74, 0.15); color: #16a34a; }
    .judge-badge.f { background: rgba(220, 38, 38, 0.14); color: #dc2626; }
    .judge-answer .q-explain { color: var(--muted); line-height: 1.55; }
    .judge-answer .q-explain strong { color: var(--text); }

    /* ---------- 简答题 ---------- */
    .sa-item {
      margin: 0 0 14px;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
    }
    .sa-item:last-child { margin-bottom: 0; }
    .sa-q {
      display: flex;
      gap: 8px;
      padding: 10px 14px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 600;
      font-size: 0.98rem;
      line-height: 1.55;
    }
    .sa-q .sa-num { flex: none; font-weight: 700; opacity: 0.85; }
    .sa-a { padding: 10px 14px; color: var(--text); font-size: 0.92rem; line-height: 1.7; }

    /* ---------- 补充题库（无选项）---------- */
    li.qbank-item .q-stem { line-height: 1.7; }
    .qbank-answer {
      display: inline-flex;
      align-items: center;
      margin: 0 2px;
      padding: 1px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 600;
      font-size: 0.85rem;
      white-space: nowrap;
    }
    .qbank-answer::before { content: "✔"; margin-right: 5px; opacity: 0.7; font-size: 0.8em; }

    /* ---------- 答案速查 chips ---------- */
    .answer-key-panel { margin: 10px 0 4px; }
    .ak-group { margin-bottom: 18px; }
    .ak-group:last-child { margin-bottom: 0; }
    .ak-group h4 {
      margin: 0 0 10px;
      font-size: 0.9rem;
      color: var(--accent-2);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .ak-group h4::before {
      content: "";
      width: 4px;
      height: 14px;
      border-radius: 2px;
      background: var(--accent-2);
    }
    .ak-chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .ak-chip {
      display: inline-flex;
      align-items: baseline;
      gap: 6px;
      padding: 4px 11px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--surface);
      font-size: 0.85rem;
      font-variant-numeric: tabular-nums;
    }
    .ak-chip b { color: var(--muted); font-weight: 600; }
    .ak-chip .ak-val { color: var(--accent); font-weight: 700; }
    .ak-chip .ak-val.t { color: #16a34a; }
    .ak-chip .ak-val.f { color: #dc2626; }

    /* ---------- 历年真题 case cards ---------- */
    .exam-case {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 14px;
      background: var(--bg);
    }
    .exam-case:last-child { margin-bottom: 0; }
    .exam-case > .case-title {
      margin: 0 0 10px;
      font-size: 1rem;
      font-weight: 700;
      color: var(--accent-2);
      padding-bottom: 8px;
      border-bottom: 1px dashed var(--border);
    }
    .exam-case .case-note {
      margin: 0 0 10px;
      padding: 8px 12px;
      border-radius: 8px;
      background: var(--accent-soft);
      font-size: 0.86rem;
      color: var(--muted);
      border-left: 3px solid var(--accent-2);
      line-height: 1.6;
    }
    .exam-case ol.exam-q { margin: 0; padding-left: 0; list-style: none; }
    .exam-case ol.exam-q > li {
      margin-bottom: 8px;
      padding-left: 4px;
      line-height: 1.65;
    }
    .exam-case ol.exam-q > li:last-child { margin-bottom: 0; }
    .exam-case ol.exam-q > li strong { color: var(--accent); }
`;

function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function inlineFmt(s) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function slugifyHeading(text) {
  const s = text
    .replace(/[（）()\[\]【】「」『』、，。：:；;·\-–—\s]+/g, '')
    .replace(/[^\w\u4e00-\u9fff]/g, '');
  return s || 'section';
}

function createIdFactory() {
  const used = new Set();
  return function uniqueId(text) {
    let base = slugifyHeading(text);
    let id = base;
    let n = 2;
    while (used.has(id)) {
      id = `${base}-${n}`;
      n++;
    }
    used.add(id);
    return id;
  };
}

function parseTable(lines) {
  const rows = lines.filter(l => l.trim().startsWith('|'));
  if (rows.length < 2) return '';
  const parseRow = r => r.split('|').slice(1, -1).map(c => c.trim());
  const headers = parseRow(rows[0]);
  const body = rows.slice(2).map(parseRow);
  let html = '<div class="table-wrap"><table><thead><tr>';
  headers.forEach(h => { html += `<th>${inlineFmt(h)}</th>`; });
  html += '</tr></thead><tbody>';
  body.forEach(row => {
    html += '<tr>';
    row.forEach(c => { html += `<td>${inlineFmt(c)}</td>`; });
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  return html;
}

function painCardsFromTable(tableLines) {
  const rows = tableLines.filter(l => l.trim().startsWith('|')).slice(2);
  const cards = rows.map(r => {
    const cells = r.split('|').slice(1, -1).map(c => c.trim());
    return `<article class="mini-card"><h4>${inlineFmt(cells[0] || '')}</h4><p>${inlineFmt(cells[1] || '')}</p></article>`;
  }).join('\n');
  return `<div class="cards-3" aria-label="痛点概览">${cards}</div>`;
}

const DIAGRAMS = {
  proc_flow: `<div class="figure" role="img" aria-label="内部流程自动化主流程">
<svg class="diagram" viewBox="0 0 720 200" xmlns="http://www.w3.org/2000/svg">
  <title>内部流程自动化主流程</title>
  <desc>流程发起、前置核验、任务分配、步骤完成与结案归档</desc>
  <defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#0d6e6e"/></marker></defs>
  <rect x="10" y="70" width="100" height="44" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="60" y="97" text-anchor="middle" font-size="12" fill="#1a2332">流程发起</text>
  <line x1="110" y1="92" x2="130" y2="92" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="130" y="70" width="110" height="44" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="185" y="97" text-anchor="middle" font-size="12" fill="#1a2332">前置核验</text>
  <line x1="240" y1="92" x2="260" y2="92" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="260" y="70" width="110" height="44" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="315" y="97" text-anchor="middle" font-size="12" fill="#1a2332">邮件分配</text>
  <line x1="370" y1="92" x2="390" y2="92" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="390" y="70" width="110" height="44" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="445" y="97" text-anchor="middle" font-size="12" fill="#1a2332">步骤办理</text>
  <line x1="500" y1="92" x2="520" y2="92" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="520" y="70" width="90" height="44" rx="8" fill="rgba(196,92,38,0.15)" stroke="#c45c26" stroke-width="2"/>
  <text x="565" y="97" text-anchor="middle" font-size="12" fill="#1a2332">末步?</text>
  <line x1="610" y1="92" x2="630" y2="92" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr)"/>
  <rect x="630" y="70" width="80" height="44" rx="8" fill="rgba(13,110,110,0.25)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="670" y="97" text-anchor="middle" font-size="12" fill="#1a2332">归档</text>
  <path d="M565 114 L565 150 L315 150 L315 114" fill="none" stroke="#c45c26" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#arr)"/>
  <text x="440" y="168" text-anchor="middle" font-size="11" fill="#5c6b7f">否 → 流转至下一步</text>
</svg>
<p class="figure-caption">主流程：实例化 → 核验 → 分配 → 办理 → 流转/结案归档</p>
</div>`,

  task_flow: `<div class="figure" role="img" aria-label="任务分发与追溯主流程">
<svg class="diagram" viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <title>任务分发与追溯主流程</title>
  <desc>上级任务接入、拆解分发、执行产出与验收关闭</desc>
  <defs><marker id="arr2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#0d6e6e"/></marker></defs>
  <rect x="20" y="60" width="110" height="48" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="75" y="88" text-anchor="middle" font-size="11" fill="#1a2332">上级任务接入</text>
  <line x1="130" y1="84" x2="150" y2="84" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr2)"/>
  <rect x="150" y="60" width="110" height="48" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="205" y="88" text-anchor="middle" font-size="11" fill="#1a2332">登记拆解</text>
  <line x1="260" y1="84" x2="280" y2="84" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr2)"/>
  <rect x="280" y="60" width="110" height="48" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="335" y="88" text-anchor="middle" font-size="11" fill="#1a2332">子任务分发</text>
  <line x1="390" y1="84" x2="410" y2="84" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr2)"/>
  <rect x="410" y="60" width="100" height="48" rx="8" fill="rgba(13,110,110,0.15)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="460" y="88" text-anchor="middle" font-size="11" fill="#1a2332">执行产出</text>
  <line x1="510" y1="84" x2="530" y2="84" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr2)"/>
  <rect x="530" y="60" width="80" height="48" rx="8" fill="rgba(196,92,38,0.15)" stroke="#c45c26" stroke-width="2"/>
  <text x="570" y="88" text-anchor="middle" font-size="11" fill="#1a2332">验收</text>
  <line x1="610" y1="84" x2="630" y2="84" stroke="#0d6e6e" stroke-width="2" marker-end="url(#arr2)"/>
  <rect x="630" y="60" width="60" height="48" rx="8" fill="rgba(13,110,110,0.25)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="660" y="88" text-anchor="middle" font-size="11" fill="#1a2332">关闭</text>
  <path d="M570 108 L570 140 L460 140 L460 108" fill="none" stroke="#c45c26" stroke-width="1.5" stroke-dasharray="4 3"/>
  <text x="515" y="158" text-anchor="middle" font-size="10" fill="#5c6b7f">不通过 → 退回补充</text>
</svg>
<p class="figure-caption">主流程：接入 → 拆解 → 分发 → 执行 → 验收 → 关闭</p>
</div>`,

  kb_flow: `<div class="figure" role="img" aria-label="知识库三大流程">
<svg class="diagram" viewBox="0 0 720 260" xmlns="http://www.w3.org/2000/svg">
  <title>规范制度知识库三大流程</title>
  <desc>知识库建设、查询生成与核验流程</desc>
  <text x="360" y="24" text-anchor="middle" font-size="13" font-weight="600" fill="#0d6e6e">知识库建设</text>
  <rect x="40" y="36" width="640" height="36" rx="6" fill="rgba(13,110,110,0.1)" stroke="#0d6e6e" stroke-width="1.5"/>
  <text x="360" y="59" text-anchor="middle" font-size="11" fill="#1a2332">收集 → 分类 → 解析切片 → 向量化 → 审核发布 → 定期巡检</text>
  <text x="360" y="100" text-anchor="middle" font-size="13" font-weight="600" fill="#0d6e6e">查询与生成</text>
  <rect x="40" y="112" width="300" height="36" rx="6" fill="rgba(13,110,110,0.1)" stroke="#0d6e6e" stroke-width="1.5"/>
  <text x="190" y="135" text-anchor="middle" font-size="10" fill="#1a2332">NL 提问 → RAG → 答案+引用</text>
  <rect x="380" y="112" width="300" height="36" rx="6" fill="rgba(196,92,38,0.1)" stroke="#c45c26" stroke-width="1.5"/>
  <text x="530" y="135" text-anchor="middle" font-size="10" fill="#1a2332">选类型 → 检索范本 → LLM 初稿</text>
  <text x="360" y="180" text-anchor="middle" font-size="13" font-weight="600" fill="#0d6e6e">核验流程</text>
  <rect x="40" y="192" width="640" height="48" rx="6" fill="rgba(13,110,110,0.1)" stroke="#0d6e6e" stroke-width="1.5"/>
  <text x="360" y="212" text-anchor="middle" font-size="10" fill="#1a2332">上传文稿 → 形式/文字/版面/引用 并行核验</text>
  <text x="360" y="228" text-anchor="middle" font-size="10" fill="#5c6b7f">→ 问题清单 → 人工复核 → 通过/退回</text>
</svg>
<p class="figure-caption">三大流程：知识建设、查询生成、文稿核验</p>
</div>`,

  deploy_layers: `<div class="figure" role="img" aria-label="私有化部署分层">
<svg class="diagram" viewBox="0 0 400 220" xmlns="http://www.w3.org/2000/svg">
  <title>私有化部署分层架构</title>
  <desc>内网隔离环境下的应用、数据与模型层</desc>
  <rect x="40" y="10" width="320" height="50" rx="8" fill="rgba(13,110,110,0.2)" stroke="#0d6e6e" stroke-width="2"/>
  <text x="200" y="40" text-anchor="middle" font-size="12" fill="#1a2332">应用层 · Web / API / 流程引擎</text>
  <rect x="60" y="75" width="280" height="50" rx="8" fill="rgba(13,110,110,0.12)" stroke="#0d6e6e" stroke-width="1.5"/>
  <text x="200" y="105" text-anchor="middle" font-size="12" fill="#1a2332">数据层 · 数据库 / 对象存储 / 向量库</text>
  <rect x="80" y="140" width="240" height="50" rx="8" fill="rgba(196,92,38,0.12)" stroke="#c45c26" stroke-width="1.5"/>
  <text x="200" y="170" text-anchor="middle" font-size="12" fill="#1a2332">模型层 · 私有化 LLM / Embedding</text>
  <ellipse cx="200" cy="210" rx="180" ry="8" fill="none" stroke="#0d6e6e" stroke-width="1.5" stroke-dasharray="6 4"/>
  <text x="200" y="200" text-anchor="middle" font-size="10" fill="#5c6b7f">企业内网安全域 · 数据不出域</text>
</svg>
<p class="figure-caption">全栈私有化：应用 + 数据 + 模型均部署于内网</p>
</div>`
};

function parseMd(md, docKey) {
  const lines = md.replace(/\r\n/g, '\n').split('\n');
  let i = 0;
  let title = '';
  const meta = {};
  const intro = [];
  const sections = [];
  let currentSection = null;
  let buffer = [];
  const uniqueId = createIdFactory();

  function flushBuffer() {
    if (!currentSection || buffer.length === 0) return;
    currentSection.blocks.push(...buffer);
    buffer = [];
  }

  function startSection(h2) {
    if (h2 === '目录') {
      flushBuffer();
      if (currentSection) sections.push(currentSection);
      currentSection = null;
      return;
    }
    flushBuffer();
    if (currentSection) sections.push(currentSection);
    currentSection = { h2, id: uniqueId(h2), children: [], blocks: [] };
  }

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (i === 0 && trimmed.startsWith('# ')) {
      title = trimmed.slice(2).trim();
      i++; continue;
    }

    if (trimmed.startsWith('> **文档编号**')) {
      const blockquote = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        blockquote.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      blockquote.forEach(b => {
        const m = b.match(/\*\*(.+?)\*\*[：:]\s*(.+)/);
        if (m) meta[m[1]] = m[2];
      });
      continue;
    }

    if (!currentSection && trimmed.startsWith('> ')) {
      const blockquote = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        blockquote.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      intro.push(...blockquote);
      continue;
    }

    if (trimmed === '---') { i++; continue; }

    if (trimmed.startsWith('## ')) {
      const h2 = trimmed.slice(3).trim();
      if (h2 === '目录') {
        flushBuffer();
        if (currentSection) sections.push(currentSection);
        currentSection = null;
        i++;
        while (i < lines.length) {
          const t = lines[i].trim();
          if (t.startsWith('## ')) break;
          if (t === '---') { i++; break; }
          i++;
        }
        continue;
      }
      startSection(h2);
      i++; continue;
    }

    if (!currentSection) {
      i++; continue;
    }

    if (trimmed.startsWith('### ')) {
      flushBuffer();
      const h3Text = trimmed.slice(4).trim();
      const h3Id = uniqueId(h3Text);
      currentSection.children.push({ h3: h3Text, id: h3Id });
      currentSection.blocks.push({ type: 'h3', text: h3Text, id: h3Id });
      i++; continue;
    }

    const mcqStem = trimmed.match(/^\*\*(\d+(?:\/\d+)?)\.\*\*\s*(.*)$/);
    if (mcqStem) {
      flushBuffer();
      const numStr = mcqStem[1];
      const num = parseInt(numStr, 10);
      let stem = mcqStem[2].trim();
      if (numStr.indexOf('/') !== -1) stem = `（第 ${numStr} 题）${stem}`;
      const rawStem = trimmed;
      const contLines = [];
      i++;
      while (i < lines.length) {
        const t = lines[i].trim();
        if (t === '' || t === '---') break;
        if (/^\*\*\d+(?:\/\d+)?\.\*\*/.test(t)) break;
        if (t.startsWith('#')) break;
        contLines.push(t);
        i++;
      }
      const ansRe = /^\*\*【答案】\s*([\s\S]*?)\s*\*\*\s*([\s\S]*)$/;
      let answerCore = '', trailing = '', matchedAns = false;
      const optChunks = [];
      const stemExtra = [];
      for (const cl of contLines) {
        const am = cl.match(ansRe);
        if (am) { answerCore = am[1].trim(); trailing = (am[2] || '').trim(); matchedAns = true; continue; }
        if (/(^|[^A-Za-z0-9])[A-H][.．、]/.test(cl)) optChunks.push(cl);
        else stemExtra.push(cl);
      }
      if (matchedAns) {
        if (stemExtra.length) stem += ' ' + stemExtra.join(' ');
        const isChoice = /^[A-Ha-h]{1,8}$/.test(answerCore);
        const isJudge = /^(?:[√×对错]|正确|错误|[TF])$/.test(answerCore);
        const explanation = trailing.replace(/^[—–\-]\s*/, '').trim();
        const options = parseOptionsStr(optChunks.join(' '));
        if (isChoice && options.length >= 2) {
          currentSection.blocks.push({ type: 'mcq', num, stem, options, answer: answerCore.toUpperCase(), explanation });
        } else if (isJudge) {
          currentSection.blocks.push({ type: 'judge', num, stem, answer: answerCore, explanation });
        } else {
          currentSection.blocks.push({ type: 'fill', num, stem, answer: answerCore, note: trailing });
        }
      } else {
        currentSection.blocks.push({ type: 'p', text: rawStem });
        for (const cl of contLines) currentSection.blocks.push({ type: 'p', text: cl });
      }
      continue;
    }

    const saStem = trimmed.match(/^\*\*(\d+)[.、]\s*(.+?)\*\*\s*$/);
    if (saStem) {
      flushBuffer();
      const num = parseInt(saStem[1], 10);
      const q = saStem[2].trim();
      const ansLines = [];
      i++;
      while (i < lines.length) {
        const t = lines[i].trim();
        if (t === '' || t === '---') break;
        if (/^\*\*\d+[.、]/.test(t)) break;
        if (t.startsWith('#')) break;
        ansLines.push(t);
        i++;
      }
      currentSection.blocks.push({ type: 'short', num, q, a: ansLines.join(' ') });
      continue;
    }

    if (trimmed.startsWith('```')) {
      flushBuffer();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++;
      currentSection.blocks.push({ type: 'pre', text: codeLines.join('\n') });
      continue;
    }

    if (trimmed.startsWith('|')) {
      flushBuffer();
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) {
        tableLines.push(lines[i]);
        i++;
      }
      currentSection.blocks.push({ type: 'table', lines: tableLines });
      continue;
    }

    if (trimmed.startsWith('> ')) {
      flushBuffer();
      const bq = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        bq.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      currentSection.blocks.push({ type: 'callout', text: bq.join(' ') });
      continue;
    }

    if (/^[-*]\s/.test(trimmed)) {
      flushBuffer();
      const items = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s/, ''));
        i++;
      }
      currentSection.blocks.push({ type: 'ul', items });
      continue;
    }

    const OL_RE = /^(\d+)\.(?!\d)\s*(.*)$/;
    if (OL_RE.test(trimmed)) {
      flushBuffer();
      const items = [];
      while (i < lines.length) {
        const m = lines[i].trim().match(OL_RE);
        if (!m) break;
        items.push({ num: parseInt(m[1], 10), text: m[2] });
        i++;
      }
      currentSection.blocks.push({ type: 'ol', items });
      continue;
    }

    if (trimmed === '') { i++; continue; }

    buffer.push({ type: 'p', text: trimmed });
    i++;
  }
  flushBuffer();
  if (currentSection) sections.push(currentSection);

  return { title, meta, intro, sections, docKey };
}

function parseOptionsStr(optStr) {
  const options = [];
  const re = /([A-H])[.．、]\s*([\s\S]*?)(?=\s+[A-H][.．、]|$)/g;
  let m;
  while ((m = re.exec(optStr)) !== null) {
    options.push({ key: m[1], text: m[2].trim() });
  }
  return options;
}

function renderQuizParts(text) {
  const ansRe = /\**\s*[【\[]\s*(?:答案|答)?\s*([A-Da-d√×对错TF]{1,4})\s*[】\]]\s*\**\s*$/;
  const am = text.match(ansRe);
  if (!am) return null;
  const answer = am[1].toUpperCase();
  const rest = text.slice(0, am.index).trim();
  const optRe = /(^|[^A-Za-z0-9])([A-H])[.．、]/;
  const om = rest.match(optRe);
  let stem = rest;
  let options = [];
  if (om) {
    const aPos = om.index + om[1].length;
    stem = rest.slice(0, aPos).trim();
    options = parseOptionsStr(rest.slice(aPos).trim());
    if (options.length < 2) { options = []; stem = rest; }
  }
  return { stem, options, answer };
}

function renderMcqList(items) {
  const lis = items.map(it => {
    const optsHtml = it.options.length
      ? `<ul class="q-options">${it.options.map(o =>
          `<li>${inlineFmt(o.key + '. ' + o.text)}</li>`).join('')}</ul>`
      : '';
    const expl = it.explanation
      ? `<span class="q-explain">${inlineFmt(it.explanation)}</span>`
      : '';
    return `<li value="${it.num}" class="quiz-item">` +
      `<div class="q-stem">${inlineFmt(it.stem)}</div>` +
      optsHtml +
      `<span class="q-answer"><span class="q-answer-label">答案</span>${esc(it.answer)}</span>` +
      expl +
      `</li>`;
  }).join('');
  return `<ol>${lis}</ol>`;
}

function judgeBadge(answer) {
  const isTrue = /^(?:[√对]|正确|T)$/.test(answer);
  return `<span class="judge-badge ${isTrue ? 't' : 'f'}">${isTrue ? '✓' : '✕'}</span>`;
}

function renderFillList(items) {
  const lis = items.map(it => {
    const note = it.note ? ` <span class="fill-note">${inlineFmt(it.note)}</span>` : '';
    return `<li class="fill-item">` +
      `<div class="q-stem">${inlineFmt(it.stem)}</div>` +
      `<div class="fill-answer"><span class="q-answer-label">答案</span>${inlineFmt(it.answer)}${note}</div>` +
      `</li>`;
  }).join('');
  return `<ol class="fill-list">${lis}</ol>`;
}

function renderJudgeList(items) {
  const lis = items.map(it => {
    const expl = it.explanation
      ? `<span class="q-explain">${inlineFmt(it.explanation)}</span>`
      : '';
    return `<li class="judge-item">` +
      `<div class="q-stem">${inlineFmt(it.stem)}</div>` +
      `<div class="judge-answer">${judgeBadge(it.answer)}${expl}</div>` +
      `</li>`;
  }).join('');
  return `<ol class="judge-list">${lis}</ol>`;
}

// 补充题库：无选项、答案在 →（…） 中的题；或 判断题答案在（**√/×**…）中
const ARROW_ANS_TEST = /→\s*[（(]/;
const JUDGE_PAREN_RE = /^([\s\S]*?)[（(]\s*\*\*\s*([√×对错])\s*\*\*\s*[，,]?\s*([\s\S]*?)\s*[)）]\s*$/;

function classifyOl(items) {
  let arrow = 0, judge = 0;
  for (const it of items) {
    if (ARROW_ANS_TEST.test(it.text)) arrow++;
    else if (JUDGE_PAREN_RE.test(it.text)) judge++;
  }
  const n = items.length || 1;
  if (arrow >= Math.ceil(n * 0.6)) return 'qbank';
  if (judge >= Math.ceil(n * 0.6)) return 'judge';
  return 'default';
}

function renderQbankItem(text) {
  return inlineFmt(text)
    .replace(/→\s*[（(]\s*([^（）()]+?)\s*[)）]/g, ' <span class="qbank-answer">$1</span>');
}

function renderOrderedList(items) {
  const mode = classifyOl(items);
  if (mode === 'qbank') {
    const lis = items.map(it =>
      `<li class="qbank-item"><span class="q-stem">${renderQbankItem(it.text)}</span></li>`
    ).join('');
    return `<ol class="qbank-list">${lis}</ol>`;
  }
  if (mode === 'judge') {
    const lis = items.map(it => {
      const m = it.text.match(JUDGE_PAREN_RE);
      if (!m) return `<li class="judge-item"><div class="q-stem">${inlineFmt(it.text)}</div></li>`;
      const expl = (m[3] || '').trim();
      return `<li class="judge-item">` +
        `<div class="q-stem">${inlineFmt(m[1].trim())}</div>` +
        `<div class="judge-answer">${judgeBadge(m[2])}${expl ? `<span class="q-explain">${inlineFmt(expl)}</span>` : ''}</div>` +
        `</li>`;
    }).join('');
    return `<ol class="judge-list">${lis}</ol>`;
  }
  const lis = items.map(it => {
    const num = it.num;
    const quiz = renderQuizParts(it.text);
    if (quiz) {
      const optsHtml = quiz.options.length
        ? `<ul class="q-options">${quiz.options.map(o =>
            `<li>${inlineFmt(o.key + '. ' + o.text)}</li>`).join('')}</ul>`
        : '';
      return `<li value="${num}" class="quiz-item">` +
        `<div class="q-stem">${inlineFmt(quiz.stem)}</div>` +
        optsHtml +
        `<span class="q-answer"><span class="q-answer-label">答案</span>${esc(quiz.answer)}</span>` +
        `</li>`;
    }
    return `<li value="${num}">${inlineFmt(it.text)}</li>`;
  }).join('');
  return `<ol>${lis}</ol>`;
}

function tryAnswerKeyTable(text) {
  const t = text.trim();
  const tokenRe = /(\d+)\s*([A-D√×对错TF]{1,3})/g;
  const tokens = [];
  let m;
  while ((m = tokenRe.exec(t)) !== null) tokens.push({ q: m[1], a: m[2] });
  if (tokens.length < 12) return null;
  const stripped = t.replace(/(\d+)\s*([A-D√×对错TF]{1,3})/g, '').replace(/\s+/g, '');
  if (stripped.length > 4) return null;

  const perRow = 10;
  let html = '<div class="table-wrap"><table class="answer-key"><thead><tr>';
  for (let c = 0; c < perRow; c++) html += '<th>题</th><th>答</th>';
  html += '</tr></thead><tbody>';
  for (let r = 0; r < tokens.length; r += perRow) {
    html += '<tr>';
    for (let c = 0; c < perRow; c++) {
      const tk = tokens[r + c];
      if (tk) html += `<td>${esc(tk.q)}</td><td>${esc(tk.a)}</td>`;
      else html += '<td></td><td></td>';
    }
    html += '</tr>';
  }
  html += '</tbody></table></div>';
  return html;
}

function tryAnswerKeyList(items) {
  const tokenRe = /(\d+)\s*([A-H]+|[√×对错]|正确|错误)/g;
  const groups = [];
  for (const raw of items) {
    const lm = raw.match(/^(.+?)[:：]\s*([\s\S]+)$/);
    if (!lm) return null;
    const label = lm[1].trim();
    const body = lm[2].trim();
    const tokens = [];
    let m;
    tokenRe.lastIndex = 0;
    while ((m = tokenRe.exec(body)) !== null) tokens.push({ q: m[1], a: m[2] });
    const stripped = body.replace(/(\d+)\s*([A-H]+|[√×对错]|正确|错误)/g, '').replace(/\s+/g, '');
    if (tokens.length < 8 || stripped.length > 4) return null;
    groups.push({ label, tokens });
  }
  if (!groups.length) return null;
  let html = '<div class="answer-key-panel">';
  for (const g of groups) {
    html += `<div class="ak-group"><h4>${inlineFmt(g.label)}</h4><div class="ak-chips">`;
    for (const tk of g.tokens) {
      const cls = /^(?:[√对]|正确)$/.test(tk.a) ? ' t' : /^(?:[×错]|错误)$/.test(tk.a) ? ' f' : '';
      html += `<span class="ak-chip"><b>${esc(tk.q)}</b><span class="ak-val${cls}">${esc(tk.a)}</span></span>`;
    }
    html += '</div></div>';
  }
  html += '</div>';
  return html;
}

function renderBlock(block, sectionId, docKey) {
  switch (block.type) {
    case 'h3': return `<h3 id="${block.id}">${inlineFmt(block.text)}</h3>`;
    case 'p': {
      const keyTable = tryAnswerKeyTable(block.text);
      return keyTable || `<p>${inlineFmt(block.text)}</p>`;
    }
    case 'short':
      return `<div class="sa-item">` +
        `<div class="sa-q"><span class="sa-num">${esc(String(block.num))}.</span><span>${inlineFmt(block.q)}</span></div>` +
        `<div class="sa-a">${inlineFmt(block.a)}</div>` +
        `</div>`;
    case 'fill': return renderFillList([block]);
    case 'judge': return renderJudgeList([block]);
    case 'pre': return `<pre>${esc(block.text)}</pre>`;
    case 'callout': return `<div class="callout">${inlineFmt(block.text)}</div>`;
    case 'ul': return tryAnswerKeyList(block.items) || `<ul>${block.items.map(it => `<li>${inlineFmt(it)}</li>`).join('')}</ul>`;
    case 'ol': return renderOrderedList(block.items);
    case 'table':
      if (sectionId === 's2') return painCardsFromTable(block.lines);
      return parseTable(block.lines);
    default: return '';
  }
}

function renderSection(sec, docKey) {
  let extra = '';
  if (sec.id === 's5' && sec.h2.includes('业务流程')) {
    if (docKey === 'proc') extra = DIAGRAMS.proc_flow;
    else if (docKey === 'task') extra = DIAGRAMS.task_flow;
    else if (docKey === 'kb') extra = DIAGRAMS.kb_flow;
  }
  if (sec.id === 's7') extra = DIAGRAMS.deploy_layers + extra;

  let body = '';
  let inCase = false;
  let inExam = false;
  let run = [], runType = null;
  const flushRun = () => {
    if (!run.length) return;
    if (runType === 'mcq') body += renderMcqList(run);
    else if (runType === 'fill') body += renderFillList(run);
    else if (runType === 'judge') body += renderJudgeList(run);
    run = []; runType = null;
  };
  const closeExam = () => { if (inExam) { body += '</div>'; inExam = false; } };
  const closeCase = () => { if (inCase) { body += '</div>'; inCase = false; } };

  for (const block of sec.blocks) {
    if (block.type === 'mcq' || block.type === 'fill' || block.type === 'judge') {
      if (runType && runType !== block.type) flushRun();
      runType = block.type;
      run.push(block);
      continue;
    }
    flushRun();

    // 历年真题：**试题…** 开启一个 case 卡片
    const examTitle = block.type === 'p' && /^\*\*试题[\s\S]+\*\*$/.test(block.text.trim());
    if (examTitle) {
      closeCase();
      closeExam();
      const t = block.text.trim().replace(/^\*\*/, '').replace(/\*\*$/, '');
      body += `<div class="exam-case"><div class="case-title">${inlineFmt(t)}</div>`;
      inExam = true;
      continue;
    }
    if (inExam) {
      if (block.type === 'callout' && /^【/.test(block.text.trim())) {
        body += `<div class="case-note">${inlineFmt(block.text)}</div>`;
        continue;
      }
      if (block.type === 'ul') {
        body += `<ol class="exam-q">${block.items.map(it => `<li>${inlineFmt(it)}</li>`).join('')}</ol>`;
        continue;
      }
      closeExam();
    }

    if (block.type === 'h3' && block.text.startsWith('案例')) {
      closeCase();
      body += `<div class="case-card"><h3>${inlineFmt(block.text)}</h3>`;
      inCase = true;
    } else {
      body += renderBlock(block, sec.id, docKey);
    }
  }
  flushRun();
  closeExam();
  closeCase();

  return `<section id="${sec.id}">
      <h2>${inlineFmt(sec.h2)}</h2>
      ${extra}
      ${body}
    </section>`;
}

function detectDocKey(filename) {
  if (filename.includes('01-') || filename.includes('流程自动化')) return 'proc';
  if (filename.includes('02-') || filename.includes('任务分发')) return 'task';
  if (filename.includes('03-') || filename.includes('知识库')) return 'kb';
  return 'proc';
}

function renderSidebarToc(sections) {
  const items = sections.map(sec => {
    const childLinks = sec.children.map(ch =>
      `<li><a href="#${ch.id}">${inlineFmt(ch.h3)}</a></li>`
    ).join('');
    const nested = childLinks ? `<ul>${childLinks}</ul>` : '';
    return `<li><a href="#${sec.id}">${inlineFmt(sec.h2)}</a>${nested}</li>`;
  }).join('\n');
  return `<aside class="sidebar-toc" id="doc-toc" aria-label="章节目录">
      <h2 class="toc-title">章节目录</h2>
      <nav><ul>${items}</ul></nav>
    </aside>`;
}

function renderHero(title, meta, intro, badge) {
  const metaGrid = Object.entries(meta).map(([k, v]) =>
    `<div class="meta-item"><strong>${esc(k)}</strong>：${esc(v)}</div>`
  ).join('\n');
  const introHtml = intro.length
    ? `<div class="intro-lines">${intro.map(p => `<p>${inlineFmt(p)}</p>`).join('')}</div>`
    : '';
  const badgeHtml = badge ? `<span class="badge">${esc(badge)}</span>` : '';
  return `<header class="hero">
      <h1>${esc(title)}</h1>
      ${introHtml}
      ${metaGrid ? `<div class="meta-grid">${metaGrid}</div>` : ''}
      ${badgeHtml}
    </header>`;
}

const SIDEBAR_SCRIPT = `
<script>
(function () {
  var toc = document.getElementById('doc-toc');
  if (!toc) return;
  var toggle = document.getElementById('toc-toggle');
  var backdrop = document.getElementById('toc-backdrop');
  function closeToc() {
    toc.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = toc.classList.toggle('open');
      if (backdrop) backdrop.classList.toggle('open', open);
    });
  }
  if (backdrop) backdrop.addEventListener('click', closeToc);
  toc.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function () {
      if (window.matchMedia('(max-width: 960px)').matches) closeToc();
    });
  });
  var links = Array.from(toc.querySelectorAll('a[href^="#"]'));
  var headings = links.map(function (a) {
    var id = a.getAttribute('href').slice(1);
    return document.getElementById(id);
  }).filter(Boolean);
  if (!headings.length) return;
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var id = entry.target.id;
      links.forEach(function (link) {
        link.classList.toggle('active', link.getAttribute('href') === '#' + id);
      });
    });
  }, { rootMargin: '-20% 0px -70% 0px', threshold: 0 });
  headings.forEach(function (h) { observer.observe(h); });
})();
</script>`;

function convert(mdPath, outPath, options = {}) {
  const sidebarToc = options.sidebarToc !== false && options.sidebarToc;
  const md = fs.readFileSync(mdPath, 'utf8');
  const docKey = detectDocKey(path.basename(mdPath));
  const { title, meta, intro, sections } = parseMd(md, docKey);

  const toc = sections.map(s =>
    `<li><a href="#${s.id}">${inlineFmt(s.h2)}</a></li>`
  ).join('\n');

  const badge = meta['文档编号'] ? '人力资源部 AI 服务 · 私有化部署方案' : '';
  const hero = renderHero(title, meta, intro, badge);

  const bodySections = sections.map(s => renderSection(s, docKey)).join('\n\n    ');

  const footerMeta = meta['编制日期'] || meta['文档编号']
    ? `<footer>编制日期 ${esc(meta['编制日期'] || '')}${meta['文档编号'] ? ` · ${esc(meta['文档编号'])}` : ''}</footer>`
    : '';

  const mainContent = `
    ${hero}

    ${sidebarToc ? '' : `<nav class="toc" aria-label="目录">
      <h2>目录</h2>
      <ol>${toc}</ol>
    </nav>`}

    ${bodySections}

    ${footerMeta}`;

  const pageBody = sidebarToc
    ? `<div class="page-layout">
    ${renderSidebarToc(sections)}
    <div class="content">
      <div class="wrap">${mainContent}</div>
    </div>
  </div>
  <button type="button" class="toc-toggle" id="toc-toggle" aria-controls="doc-toc" aria-expanded="false">目录</button>
  <div class="toc-backdrop" id="toc-backdrop" hidden></div>
  ${SIDEBAR_SCRIPT}`
    : `<div class="wrap">${mainContent}</div>`;

  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="color-scheme" content="light dark" />
  <title>${esc(title)}</title>
  <style>${CSS}
  </style>
</head>
<body>
  ${pageBody}
</body>
</html>`;

  fs.writeFileSync(outPath, html, 'utf8');
  console.log(`✓ ${outPath}`);
}

const rawArgs = process.argv.slice(2);
if (rawArgs.length === 0) {
  console.error('Usage: node md_to_rich_html.js [--sidebar-toc] <input.md> [output.html]');
  process.exit(1);
}

const sidebarToc = rawArgs.includes('--sidebar-toc');
const args = rawArgs.filter(a => a !== '--sidebar-toc');

const input = path.resolve(args[0]);
const output = args[1]
  ? path.resolve(args[1])
  : input.replace(/\.md$/i, '.html');

convert(input, output, { sidebarToc });
