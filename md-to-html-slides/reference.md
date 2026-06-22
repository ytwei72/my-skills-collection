# md-to-html-slides — 参考实现

> SKILL.md 是规范与决策；本文件是**可复用代码骨架**。生成 HTML 时按此处的 CSS/JS 拷贝改写即可，不必重新设计交互逻辑。

---

## 1. 完整最小可运行骨架（直接拷走改）

下面是**一份完整的 16:9 翻页演示稿模板**，包含 1 张封面 + 1 张内容 + 1 张结束，覆盖了「骨架契约 5 条」全部要点。生成时按此扩展每页 `<section>` 即可。

```html
<!doctype html>
<html lang="zh-CN" data-theme="aqua">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{DECK_TITLE}}</title>
<style>
:root{
  --slide-w: 1920px; --slide-h: 1080px;          /* 16:9 高清；4:3 改 1440×1080 */
  /* 默认主题 = 青蓝 aqua（清新浅色），其余两套见 [data-theme] */
  --bg:#F1FAF8; --surface:#FFFFFF; --surface-2:#E4F4F0;
  --text:#1E2A33; --muted:#5F7682; --border:#D8E8E4;
  --primary:#0E9488; --primary-dark:#0B6E66; --accent:#F5A524; --accent-2:#16B6A6;
  --good:#10B981; --bad:#EF6C5A;
  --shadow: 0 12px 34px -10px rgba(20,40,50,.18);
}
[data-theme="aqua"]{ --bg:#F1FAF8; --surface:#FFFFFF; --surface-2:#E4F4F0;
  --text:#1E2A33; --muted:#5F7682; --border:#D8E8E4;
  --primary:#0E9488; --primary-dark:#0B6E66; --accent:#F5A524; --accent-2:#16B6A6; --good:#10B981; --bad:#EF6C5A; }
[data-theme="azure"]{ --bg:#F3F7FF; --surface:#FFFFFF; --surface-2:#E5EDFF;
  --text:#1B2740; --muted:#637089; --border:#DAE4F6;
  --primary:#2563EB; --primary-dark:#1E40AF; --accent:#06B6D4; --accent-2:#3B82F6; --good:#10B981; --bad:#EF6C5A; }
[data-theme="violet"]{ --bg:#FAF6FF; --surface:#FFFFFF; --surface-2:#F2E9FE;
  --text:#281F3D; --muted:#6C6385; --border:#E7DBF8;
  --primary:#7C3AED; --primary-dark:#5B21B6; --accent:#EC4899; --accent-2:#9461F0; --good:#10B981; --bad:#EF6C5A; }
/* 兜底深色：用户系统深色且未点主题时；多主题切换优先级更高 */
@media (prefers-color-scheme: dark){
  :root:not([data-theme]){ --bg:#0a0e1a; --surface:#111827; --surface-2:#1f2937;
    --text:#f1f5f9; --muted:#94a3b8; --border:#334155;
    --primary:#16B6A6; --primary-dark:#0E9488; --accent:#F5A524; --accent-2:#0EA5E9;
    --shadow:0 20px 60px -10px rgba(0,0,0,.6); }
}
*,*::before,*::after{ box-sizing:border-box }
html,body{ margin:0; height:100%; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI",system-ui,sans-serif;
  overflow:hidden;
}
body{ display:grid; place-items:center }

/* deck = 演示舞台；通过 transform: scale 适配窗口 */
.stage{ width:100vw; height:100vh; display:grid; place-items:center; overflow:hidden }
.deck{
  width:var(--slide-w); height:var(--slide-h);
  position:relative; background:var(--surface); border-radius:14px;
  box-shadow:var(--shadow); transform-origin:center;
}

/* 每页绝对定位，叠加，仅 .active 可见
   注意 padding-bottom 预留 ≥110px「底部安全区」，避免 nav.ctrl 遮挡内容；
   flex 纵向 + center → 内容垂直居中、占满版心，杜绝头重脚轻 */
section.slide{
  position:absolute; inset:0; padding:84px 112px 116px;
  display:flex; flex-direction:column; justify-content:center; gap:30px;
  opacity:0; transform:translateX(20px);
  transition: opacity .35s ease, transform .35s ease;
  pointer-events:none;
}
section.slide.active{ opacity:1; transform:none; pointer-events:auto }
section.slide aside.notes{ display:none }   /* 默认不显示备注 */

/* —— 各 layout —— */
section.slide[data-layout="cover"]{
  text-align:center; align-items:center; justify-content:center;
  background: linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%);
}
section.slide[data-layout="cover"] h1{ font-size: clamp(64px,5.2vw,92px); margin:0 0 .35em; letter-spacing:.02em; color:var(--primary-dark) }
section.slide[data-layout="cover"] .sub{ color:var(--muted); font-size:clamp(26px,2.4vw,34px) }
section.slide[data-layout="cover"] .meta{ margin-top:1.6em; font-size:20px; color:var(--muted) }

section.slide[data-layout="section"]{
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color:#fff; align-items:flex-start; padding-left:140px; justify-content:center;
}
section.slide[data-layout="section"] .num{ font-size:160px; font-weight:800; opacity:.25; line-height:1 }
section.slide[data-layout="section"] h2{ font-size:72px; margin:0 }

section.slide[data-layout="content"] h2{ font-size:50px; margin:0; color:var(--primary-dark);
  padding-bottom:14px; border-bottom:4px solid var(--accent); align-self:flex-start }
section.slide[data-layout="content"] ul{ font-size:28px; line-height:1.75; padding-left:1.2em }
section.slide[data-layout="content"] li{ margin:.45em 0 }
section.slide[data-layout="content"] li::marker{ color:var(--accent) }

section.slide[data-layout="two-col"] .grid{ display:grid; grid-template-columns:1fr 1fr; gap:48px; flex:1; align-content:center }
section.slide[data-layout="two-col"] .col{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:32px 36px; border-left:6px solid var(--primary); box-shadow:var(--shadow) }
section.slide[data-layout="two-col"] .col h3{ margin:0 0 16px; color:var(--primary-dark); font-size:26px }
section.slide[data-layout="two-col"] .col li{ font-size:22px; line-height:1.65 }

section.slide[data-layout="image"]{ padding:0; align-items:stretch; justify-content:stretch }
section.slide[data-layout="image"] img{ width:100%; height:100%; object-fit:cover; border-radius:14px }

section.slide[data-layout="image-text"] .grid{ display:grid; grid-template-columns:1.1fr 1fr; gap:40px; flex:1; align-items:center }
section.slide[data-layout="image-text"] img{ width:100%; height:100%; object-fit:cover; border-radius:12px; max-height:500px }

section.slide[data-layout="quote"]{ text-align:center; align-items:center; justify-content:center }
section.slide[data-layout="quote"] blockquote{ font-size:clamp(36px,3.4vw,56px); line-height:1.5; margin:0; max-width:80%;
  border-left:8px solid var(--accent); padding-left:32px; text-align:left; font-weight:500; color:var(--primary-dark) }
section.slide[data-layout="quote"] .cite{ margin-top:28px; color:var(--muted); font-size:24px }

section.slide[data-layout="table"] table{ width:100%; border-collapse:collapse; font-size:24px; box-shadow:var(--shadow); border-radius:14px; overflow:hidden }
section.slide[data-layout="table"] th{ background:var(--primary-dark); color:#fff; padding:18px 24px; text-align:left }
section.slide[data-layout="table"] td{ padding:16px 24px; border-bottom:1px solid var(--border) }
section.slide[data-layout="table"] tr:nth-child(even) td{ background:var(--surface-2) }

section.slide[data-layout="code"] pre{ background:var(--surface-2); padding:30px; border-radius:12px;
  font-family:"SF Mono","Cascadia Code",Consolas,Menlo,monospace; font-size:24px; line-height:1.55;
  overflow:auto; max-height:820px }

section.slide[data-layout="ending"]{ text-align:center; align-items:center; justify-content:center;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); color:#fff }
section.slide[data-layout="ending"] h1{ font-size:120px; margin:0 0 .2em }
section.slide[data-layout="ending"] .sub{ color:rgba(255,255,255,.85); font-size:30px }

/* —— 控制条 —— */
nav.ctrl{
  position:fixed; bottom:16px; right:16px; z-index:100;
  background:var(--surface); color:var(--text); border:1px solid var(--border);
  border-radius:999px; padding:6px 10px; display:flex; gap:6px; align-items:center;
  font-size:13px; box-shadow:var(--shadow); user-select:none;
}
nav.ctrl button{ background:transparent; color:inherit; border:0; cursor:pointer; padding:6px 10px; border-radius:999px; font-size:14px }
nav.ctrl button:hover{ background:var(--surface-2) }
nav.ctrl .pos{ color:var(--muted); padding:0 8px; font-variant-numeric:tabular-nums }

/* 概览模式 */
body.overview .stage{ padding:24px; align-items:start }
body.overview .deck{ display:grid !important; grid-template-columns:repeat(4,1fr); gap:16px;
  width:min(100vw - 48px, 1600px); height:auto; padding:24px; transform:none !important; background:transparent; box-shadow:none }
body.overview section.slide{ position:relative; opacity:1; transform:none !important; pointer-events:auto;
  width:100%; aspect-ratio:16/9; height:auto; border-radius:8px; background:var(--surface);
  box-shadow:var(--shadow); padding:16px; cursor:pointer; transition:transform .15s ease;
  font-size:8px; /* 缩小整页文字 */
}
body.overview section.slide:hover{ transform:scale(1.03) }
body.overview section.slide h1,
body.overview section.slide h2,
body.overview section.slide h3{ font-size:1.6em }

/* 演讲者视图 */
body.speaker nav.ctrl{ display:none }
body.speaker .stage{ display:grid; grid-template-columns:2fr 1fr; gap:0; padding:0 }
body.speaker .deck{ width:100%; height:100vh; border-radius:0 }
body.speaker .panel{ background:var(--surface-2); padding:24px; overflow:auto; border-left:1px solid var(--border) }
body.speaker .panel h4{ margin:0 0 8px; color:var(--primary); font-size:14px; text-transform:uppercase; letter-spacing:.1em }
body.speaker .panel .timer{ font-size:48px; font-variant-numeric:tabular-nums; margin:0 0 24px }
body.speaker .panel .notes{ display:block !important; font-size:16px; line-height:1.6; margin:0 0 24px;
  padding:16px; background:var(--surface); border-radius:8px; border-left:4px solid var(--accent) }
body:not(.speaker) .panel{ display:none }

/* 黑屏 */
body.blackout .stage{ background:#000 } body.blackout .deck{ visibility:hidden }

/* ?export=1 时关动画/控制条/光标 */
body.export *,body.export *::before,body.export *::after{
  transition:none !important; animation:none !important;
}
body.export nav.ctrl, body.export .toast, body.export .panel{ display:none !important }
body.export{ cursor:none !important }
body.export section.slide{ opacity:0; transform:none } /* 仍由 active 控制 */

/* 打印 PDF */
@media print{
  @page{ size: 1920px 1080px; margin:0 }   /* 4:3 时改 1440px 1080px */
  html,body{ height:auto; overflow:visible; background:#fff !important }
  body{ display:block }
  nav.ctrl,.toast,.panel{ display:none !important }
  .stage{ width:auto; height:auto }
  .deck{ width:1920px; height:auto; transform:none !important; box-shadow:none; border-radius:0; background:transparent }
  section.slide{ position:relative !important; opacity:1 !important; transform:none !important;
    width:1920px; height:1080px; page-break-after:always; break-inside:avoid;
    background:var(--bg); border-radius:0; pointer-events:auto }
  section.slide:last-child{ page-break-after:auto }
  section.slide aside.notes{ display:none }
}

/* toast 快捷键浮层 */
.toast{ position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); z-index:200;
  background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:24px 32px;
  box-shadow:var(--shadow); font-size:14px; line-height:1.8; display:none }
.toast.show{ display:block }
.toast kbd{ background:var(--surface-2); border:1px solid var(--border); border-radius:4px; padding:2px 6px; font-family:inherit; margin-right:6px }
</style>
</head>
<body>

<div class="stage">
  <main class="deck" data-format="169">

    <!-- ====== 1. 封面 ====== -->
    <section class="slide active" data-index="0" data-layout="cover">
      <h1>{{TITLE}}</h1>
      <p class="sub">{{SUBTITLE}}</p>
      <p class="meta">{{DATE}} · {{AUTHOR}}</p>
      <aside class="notes">开场：用一句话点出本次演示要解决的核心问题。</aside>
    </section>

    <!-- ====== 2. 内容页 ====== -->
    <section class="slide" data-index="1" data-layout="content">
      <h2>核心要点</h2>
      <ul>
        <li>要点一</li>
        <li>要点二</li>
        <li>要点三</li>
      </ul>
      <aside class="notes">展开每条要点时各停留 30 秒，重点强调要点二。</aside>
    </section>

    <!-- ====== N. 结束 ====== -->
    <section class="slide" data-index="2" data-layout="ending">
      <h1>Q &amp; A</h1>
      <p class="sub">谢谢聆听</p>
      <aside class="notes">预留 5 分钟提问；如无问题，回到要点二做总结。</aside>
    </section>

  </main>

  <!-- 演讲者视图右侧面板（speaker 模式才显示） -->
  <aside class="panel" aria-label="演讲者视图">
    <h4>计时器</h4>
    <p class="timer" id="timer">00:00</p>
    <h4>当前页备注</h4>
    <div class="notes" id="speakerNotes"></div>
    <h4>下一页</h4>
    <p id="nextHint" style="color:var(--muted)"></p>
  </aside>
</div>

<nav class="ctrl" aria-label="幻灯片控制">
  <button data-act="prev" aria-label="上一页">‹</button>
  <span class="pos"><span id="cur">1</span> / <span id="tot">3</span></span>
  <button data-act="next" aria-label="下一页">›</button>
  <button data-act="full" aria-label="全屏">⛶</button>
  <button data-act="overview" aria-label="概览">▦</button>
  <button data-act="speaker" aria-label="演讲者视图">◧</button>
  <button data-act="theme" aria-label="切换主题">◐</button>
  <button data-act="help" aria-label="快捷键帮助">?</button>
</nav>

<div class="toast" id="toast" aria-hidden="true">
  <div><kbd>← →</kbd> 翻页 &nbsp; <kbd>Space</kbd> 下一页 &nbsp; <kbd>Home/End</kbd> 首末页</div>
  <div><kbd>F</kbd> 全屏 &nbsp; <kbd>O</kbd> 概览 &nbsp; <kbd>S</kbd> 演讲者视图 &nbsp; <kbd>T</kbd> 换主题 &nbsp; <kbd>B</kbd> 黑屏</div>
  <div><kbd>数字+Enter</kbd> 跳页 &nbsp; <kbd>Ctrl+P</kbd> 打印 PDF &nbsp; <kbd>?</kbd> 此提示</div>
</div>

<script>
(function(){
  const deck = document.querySelector('main.deck');
  const slides = Array.from(deck.querySelectorAll('section.slide'));
  const stage = document.querySelector('.stage');
  let cur = 0;
  let buf = '';
  let timerStart = null, timerInt = null;

  function setActive(i){
    cur = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach((s, k) => s.classList.toggle('active', k === cur));
    document.getElementById('cur').textContent = cur + 1;
    if (document.body.classList.contains('speaker')) updateSpeaker();
  }
  function next(){ setActive(cur + 1) }
  function prev(){ setActive(cur - 1) }
  function fit(){
    if (document.body.classList.contains('overview')) return;
    const sw = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--slide-w'));
    const sh = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--slide-h'));
    const stageRect = stage.getBoundingClientRect();
    const scale = Math.min(stageRect.width / sw, stageRect.height / sh) * 0.96;
    deck.style.transform = 'scale(' + scale + ')';
  }
  function toggleFullscreen(){
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else document.exitFullscreen();
  }
  function toggleOverview(){
    document.body.classList.toggle('overview');
    if (document.body.classList.contains('overview')){
      slides.forEach((s, k) => s.onclick = () => { document.body.classList.remove('overview'); setActive(k); fit(); });
    }
    fit();
  }
  function toggleSpeaker(){
    document.body.classList.toggle('speaker');
    if (document.body.classList.contains('speaker')){
      timerStart = Date.now();
      timerInt = setInterval(()=>{
        const s = Math.floor((Date.now() - timerStart)/1000);
        document.getElementById('timer').textContent =
          String(Math.floor(s/60)).padStart(2,'0') + ':' + String(s%60).padStart(2,'0');
      }, 1000);
      updateSpeaker();
    } else {
      clearInterval(timerInt); timerInt = null;
    }
    fit();
  }
  function updateSpeaker(){
    const note = slides[cur].querySelector('aside.notes');
    document.getElementById('speakerNotes').textContent = note ? note.textContent.trim() : '（本页无备注）';
    const nx = slides[cur+1];
    document.getElementById('nextHint').textContent = nx
      ? '下一页：' + (nx.querySelector('h1,h2,h3')?.textContent || '（无标题）')
      : '已是最后一页';
  }
  function showHelp(){
    const t = document.getElementById('toast');
    t.classList.add('show');
    clearTimeout(showHelp._t);
    showHelp._t = setTimeout(()=>t.classList.remove('show'), 4000);
  }

  // 多主题切换：青蓝 / 晴空 / 雅紫，循环 + localStorage 记忆
  const THEMES = ['aqua','azure','violet'];
  const THEME_KEY = 'deck-theme';
  (function initTheme(){
    const saved = localStorage.getItem(THEME_KEY);
    document.documentElement.setAttribute('data-theme', THEMES.includes(saved) ? saved : 'aqua');
  })();
  function cycleTheme(){
    const now = document.documentElement.getAttribute('data-theme') || 'aqua';
    const next = THEMES[(THEMES.indexOf(now) + 1) % THEMES.length];
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem(THEME_KEY, next);
  }

  // 键盘
  document.addEventListener('keydown', e => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (/^[0-9]$/.test(k)) { buf += k; return; }
    if (k === 'Enter' && buf) { setActive(parseInt(buf,10) - 1); buf = ''; return; }
    buf = '';
    switch(k){
      case 'ArrowRight': case 'PageDown': case ' ': next(); e.preventDefault(); break;
      case 'ArrowLeft':  case 'PageUp':   case 'Backspace': prev(); e.preventDefault(); break;
      case 'Home': setActive(0); break;
      case 'End':  setActive(slides.length - 1); break;
      case 'f': case 'F': toggleFullscreen(); break;
      case 'o': case 'O': toggleOverview(); break;
      case 's': case 'S': toggleSpeaker(); break;
      case 't': case 'T': cycleTheme(); break;
      case 'b': case 'B': document.body.classList.toggle('blackout'); break;
      case '?': showHelp(); break;
      case 'Escape':
        if (document.body.classList.contains('overview')) document.body.classList.remove('overview');
        if (document.body.classList.contains('speaker'))  toggleSpeaker();
        fit(); break;
    }
  });

  // 控制条
  document.querySelector('nav.ctrl').addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    ({ prev, next, full: toggleFullscreen, overview: toggleOverview, speaker: toggleSpeaker, theme: cycleTheme, help: showHelp })[b.dataset.act]?.();
  });

  // 触屏
  let tx = 0;
  document.addEventListener('touchstart', e => tx = e.touches[0].clientX, {passive:true});
  document.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 50) (dx < 0 ? next : prev)();
  });

  // 自适应窗口
  window.addEventListener('resize', fit);
  document.addEventListener('fullscreenchange', fit);

  // ?export=1 钩子（供未来 toolkits/html_slides_to_pptx 截图用）
  if (new URLSearchParams(location.search).get('export') === '1'){
    document.body.classList.add('export');
  }

  // 全局 deckAPI（toolkits/html_slides_to_pptx 必须依赖此 API）
  window.deckAPI = {
    slideCount: slides.length,
    goToSlide: (i) => setActive(i),
    getCurrent: () => cur,
    getNotes: (i) => {
      const s = slides[i]; if (!s) return '';
      const n = s.querySelector('aside.notes');
      return n ? n.textContent.trim() : '';
    },
  };

  document.getElementById('tot').textContent = slides.length;
  setActive(0);
  fit();
})();
</script>
</body>
</html>
```

---

## 2. 各 layout 的快速速查

| `data-layout` | 用途 | MD 信号 |
|---|---|---|
| `cover` | 封面 | 首个 `# H1` |
| `section` | 章节分隔（大数字 + 章节名） | 后续 `# H1` |
| `content` | 标题 + 列表/正文 | `## H2` 之下有正文 |
| `two-col` | 左右两栏对比 | MD 中有"对比 / vs / 前后 / 优缺点"语义；或两个并列 `###` |
| `image` | 整页图（沉浸式） | 单独一行 `![](url)`，且无相邻正文 |
| `image-text` | 半图半文 | `![](url)` + 紧跟段落或列表 |
| `quote` | 大字号引用（金句页） | `>` 引用块占据该 `##` 主体 |
| `table` | 表格 | MD 表格 |
| `code` | 代码 | 围栏代码块 |
| `ending` | 结束页 | 自动添加，或匹配 `## 致谢/Q&A/总结` |

按需扩展更多 layout（如 `quote-with-cite`、`stat`、`timeline`），但每加一个都要在 SKILL.md 切片规则里记录映射规则。

---

## 高质量组件库（达标关键，强烈建议复用）

> 这套组件是从质量样板 `ai-product-catalog-slides-v1.html` 提炼并泛化（改用本骨架的 CSS 变量、系统字体）。
> 把下面的 CSS 追加进 deck 的 `<style>`，在内容页里**混搭 ≥4 种**组件，即可满足「版面质量硬标准」里的字号、填充、多样化要求。
> 内容页结构建议：`<section class="slide" data-layout="content"><h2>标题</h2> …组件… </section>`，`.slide` 已是 flex 纵向居中，组件之间靠 `gap` 自然撑开版心。

```css
/* —— 小节标签：给一页里的多个区块分组 —— */
.sec-label{ font-size:23px; font-weight:700; color:var(--primary-dark); display:flex; align-items:center; gap:10px; margin-bottom:16px }
.sec-label::before{ content:""; width:22px; height:4px; border-radius:2px; background:var(--accent) }

/* —— 卡片网格 —— */
.grid2{ display:grid; grid-template-columns:repeat(2,1fr); gap:28px }
.grid3{ display:grid; grid-template-columns:repeat(3,1fr); gap:26px }
.grid4{ display:grid; grid-template-columns:repeat(4,1fr); gap:22px }
.grid5{ display:grid; grid-template-columns:repeat(5,1fr); gap:20px }
.card{ background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:30px 28px;
  position:relative; overflow:hidden; box-shadow:var(--shadow) }
.card::before{ content:""; position:absolute; inset:0 0 auto 0; height:6px; background:var(--primary) }
.card.t-accent::before{ background:var(--accent) } .card.t-good::before{ background:var(--good) }
.card .ico{ font-size:40px; display:block; margin-bottom:14px }
.card .ti{ font-size:28px; font-weight:600; color:var(--primary-dark); margin:0 0 12px }
.card .de{ font-size:21px; color:var(--muted); line-height:1.6 }
.card .tag{ display:inline-block; margin-top:16px; background:var(--surface-2); color:var(--primary-dark);
  padding:8px 18px; border-radius:8px; font-size:18px; font-weight:600 }

/* —— KPI 大数字 —— */
.kpi-row{ display:flex; gap:26px }
.kpi-box{ flex:1; background:var(--surface); border:1.5px solid var(--border); border-top:5px solid var(--good);
  border-radius:16px; padding:26px 18px; text-align:center; box-shadow:var(--shadow) }
.kpi-v{ font-size:50px; font-weight:700; color:var(--good); line-height:1; margin-bottom:8px }
.kpi-l{ font-size:21px; color:var(--muted); line-height:1.4 }

/* —— 统计条（一行多个数字） —— */
.stat-strip{ display:flex; background:var(--surface); border:1px solid var(--border); border-radius:16px;
  overflow:hidden; box-shadow:var(--shadow) }
.stat-item{ flex:1; text-align:center; padding:24px 14px; border-right:1px solid var(--border) }
.stat-item:last-child{ border-right:none }
.stat-n{ font-size:44px; font-weight:700; color:var(--primary); line-height:1; margin-bottom:8px }
.stat-n.acc{ color:var(--accent) }
.stat-d{ font-size:19px; color:var(--muted) }

/* —— 前后对比条（数值文字独立、深色、绝不裁切） —— */
.metrics{ display:flex; flex-direction:column; gap:26px }
.metric-head{ display:flex; justify-content:space-between; align-items:baseline; margin-bottom:12px }
.metric-name{ font-size:23px; font-weight:700; color:var(--text) }
.metric-delta{ font-size:20px; font-weight:700; color:var(--good) }
.mbar{ position:relative; height:40px; background:var(--surface-2); border-radius:10px;
  display:flex; align-items:center; overflow:hidden; margin-bottom:12px }
.mbar:last-child{ margin-bottom:0 }
.mbar-fill{ position:absolute; left:0; top:0; height:100%; border-radius:10px }
.mbar-fill.before{ background:var(--muted); opacity:.35 }
.mbar-fill.after{ background:linear-gradient(90deg, var(--primary), var(--accent)) }
.mbar-val{ position:relative; z-index:1; padding-left:16px; font-size:20px; font-weight:700; color:var(--text); white-space:nowrap }

/* —— 图标清单 —— */
.ilist{ display:flex; flex-direction:column; gap:18px }
.ilist-item{ display:flex; gap:18px; align-items:flex-start; background:var(--surface); border:1px solid var(--border);
  border-radius:14px; padding:18px 20px; box-shadow:var(--shadow) }
.ilist-ico{ width:56px; height:56px; border-radius:14px; flex-shrink:0; display:flex; align-items:center; justify-content:center;
  font-size:28px; color:#fff; background:linear-gradient(135deg, var(--primary), var(--accent-2)) }
.ilist-txt b{ display:block; font-size:23px; color:var(--primary-dark); font-weight:600; margin-bottom:3px }
.ilist-txt span{ font-size:19px; color:var(--muted); line-height:1.45 }

/* —— 架构分层图 —— */
.arch{ display:flex; flex-direction:column; gap:14px }
.arch-row{ border-radius:16px; padding:24px 30px; color:#fff; display:flex; align-items:center; gap:28px; box-shadow:var(--shadow) }
.arch-l1{ background:linear-gradient(100deg, var(--primary-dark), var(--primary)) }
.arch-l2{ background:linear-gradient(100deg, var(--primary), var(--accent-2)) }
.arch-l3{ background:linear-gradient(100deg, var(--accent-2), var(--accent)) }
.arch-base{ background:var(--surface-2); color:var(--primary-dark); border:2px dashed var(--primary) }
.ar-label{ flex:0 0 260px; font-size:24px; font-weight:700; line-height:1.35 }
.ar-label small{ display:block; font-size:17px; font-weight:400; opacity:.9; margin-top:5px }
.ar-items{ flex:1; display:flex; flex-wrap:wrap; gap:11px; align-items:center }
.ar-chip{ background:rgba(255,255,255,.2); padding:11px 19px; border-radius:9px; font-size:21px; white-space:nowrap }
.arch-base .ar-chip{ background:#fff; border:1px solid var(--border); color:var(--primary-dark) }
.arch-arrow{ align-self:center; color:var(--accent); font-size:24px; line-height:.4; margin:-7px 0 }

/* —— 流程箭头图 —— */
.flow{ display:flex; align-items:stretch; justify-content:center }
.flow-node{ flex:1; background:var(--surface); border:1.5px solid var(--border); border-radius:16px;
  padding:26px 16px; text-align:center; box-shadow:var(--shadow) }
.flow-node.hl{ border-color:var(--accent); background:linear-gradient(180deg, var(--surface), var(--surface-2)) }
.fn-ico{ font-size:40px; margin-bottom:12px } .fn-title{ font-size:24px; font-weight:600; color:var(--primary-dark); margin-bottom:7px }
.fn-desc{ font-size:18px; color:var(--muted); line-height:1.45 }
.flow-arrow{ flex:0 0 50px; display:flex; align-items:center; justify-content:center; color:var(--accent); font-size:30px; font-weight:700 }

/* —— 路径步骤（横向卡片，色阶递进） —— */
.path{ display:flex; gap:20px; align-items:stretch }
.path-step{ flex:1; border-radius:18px; padding:30px 20px; text-align:center; color:#fff; box-shadow:var(--shadow);
  background:linear-gradient(165deg, var(--primary), var(--primary-dark)) }
.path-step.s2{ background:linear-gradient(165deg, var(--accent-2), var(--primary)) }
.path-step.s3{ background:linear-gradient(165deg, var(--accent), var(--accent-2)) }
.path-num{ width:56px; height:56px; border-radius:50%; background:rgba(255,255,255,.2); border:2px solid rgba(255,255,255,.4);
  display:flex; align-items:center; justify-content:center; font-size:26px; font-weight:700; margin:0 auto 16px }
.path-title{ font-size:26px; font-weight:600; margin-bottom:8px }
.path-time{ font-size:18px; color:rgba(255,255,255,.88); margin-bottom:14px }
.path-desc{ font-size:18px; color:rgba(255,255,255,.92); line-height:1.6 }

/* —— 时间轴 —— */
.timeline{ display:flex; align-items:stretch }
.tl-phase{ flex:1; padding:0 18px; position:relative }
.tl-phase::before{ content:""; position:absolute; top:30px; left:0; right:0; height:3px; background:var(--border) }
.tl-phase:first-child::before{ left:50% } .tl-phase:last-child::before{ right:50% }
.tl-dot{ width:60px; height:60px; border-radius:50%; background:var(--primary); color:#fff; display:flex; align-items:center;
  justify-content:center; font-size:26px; font-weight:700; margin:0 auto 20px; position:relative; z-index:1;
  box-shadow:0 0 0 7px var(--bg); border:2px solid var(--accent) }
.tl-card{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:24px 22px; box-shadow:var(--shadow) }
.tl-title{ font-size:24px; font-weight:600; color:var(--primary-dark); margin-bottom:5px }
.tl-period{ font-size:18px; color:var(--accent); font-weight:600; margin-bottom:14px }
.tl-list{ list-style:none; padding:0; margin:0 } .tl-list li{ font-size:19px; padding:7px 0 7px 18px; position:relative; line-height:1.45 }
.tl-list li::before{ content:""; position:absolute; left:0; top:14px; width:6px; height:6px; border-radius:50%; background:var(--accent-2) }

/* —— 痛点·方案双栏（带左色条的面板） —— */
.duo{ display:grid; grid-template-columns:1fr 1.1fr; gap:48px; align-content:center }
.panel{ background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:28px 32px; box-shadow:var(--shadow) }
.panel.pain{ border-left:6px solid var(--bad) } .panel.solve{ border-left:6px solid var(--good) }
.col-h{ font-size:25px; font-weight:700; margin-bottom:18px } .col-h.pain{ color:var(--bad) } .col-h.solve{ color:var(--good) }
.bul{ font-size:22px; line-height:1.5; padding:11px 0 11px 28px; position:relative }
.bul::before{ content:""; position:absolute; left:2px; top:21px; width:10px; height:10px; border-radius:50%; background:var(--primary) }
.panel.pain .bul::before{ background:var(--bad) }
.panel.solve .bul::before{ background:var(--good) }

/* —— 标签云 / 强调框 —— */
.chips{ display:flex; flex-wrap:wrap; gap:14px }
.chip{ display:inline-flex; align-items:center; gap:6px; background:var(--surface-2); color:var(--primary-dark);
  padding:12px 22px; border-radius:10px; font-size:22px; font-weight:500 }
.note{ background:var(--surface-2); border-left:6px solid var(--accent); padding:26px 32px; border-radius:0 14px 14px 0;
  font-size:25px; color:var(--primary-dark); font-weight:500; line-height:1.55 }
.note.dark{ background:linear-gradient(100deg, var(--primary-dark), var(--primary)); color:#fff; border:none }
```

**用法示例（一页里混搭 3 种组件，垂直撑满）：**

```html
<section class="slide" data-layout="content">
  <h2>AI 合同智审系统</h2>
  <div class="duo">
    <div class="panel pain"><div class="col-h pain">⚠️ 解决什么问题</div>
      <div class="bul">合同审核量大，法务精力有限</div>
      <div class="bul">人工审核易遗漏风险条款</div></div>
    <div class="panel solve"><div class="col-h solve">✓ 我们能做什么</div>
      <div class="bul">风险条款自动识别</div>
      <div class="bul">版本差异智能比对</div></div>
  </div>
  <div><div class="sec-label">效果对比</div>
    <div class="metrics" style="display:grid;grid-template-columns:1fr 1fr;gap:36px">
      <div><div class="metric-head"><span class="metric-name">风险覆盖率</span><span class="metric-delta">▲ 25pt</span></div>
        <div class="mbar"><div class="mbar-fill before" style="width:70%"></div><span class="mbar-val">人工 70%</span></div>
        <div class="mbar"><div class="mbar-fill after" style="width:95%"></div><span class="mbar-val">AI 95%+</span></div></div>
      <div><div class="metric-head"><span class="metric-name">审核周期</span><span class="metric-delta">↓ 80%</span></div>
        <div class="mbar"><div class="mbar-fill before" style="width:100%"></div><span class="mbar-val">原 3-5 天</span></div>
        <div class="mbar"><div class="mbar-fill after" style="width:25%"></div><span class="mbar-val">1 天内</span></div></div>
    </div>
  </div>
  <aside class="notes">先讲痛点，再用对比条收尾，强调覆盖率从 70% 到 95%。</aside>
</section>
```

> 这些组件都是**纯 CSS + emoji 图标**，零外链、可打印、可截图，完全符合骨架契约。
> emoji 当图标即可（💡🧠⚖️📊📡🔍📝🗂️🔠🏷️🕸️…），需要更精致时再画内联 SVG。

---

## 多主题与切换器

### 默认（3 主题 + 运行时切换）

- 3 套清新配色：**青蓝 `aqua` / 晴空 `azure` / 雅紫 `violet`**，已写进骨架 `:root` + `[data-theme="..."]`。
- **所有颜色走 CSS 变量**；切换 `data-theme` 即整页换肤。
- 切换入口：控制条「◐」+ 键盘 **T**，循环切换并 `localStorage` 记忆（key：`deck-theme`）。
- 新增配色：加一个 `[data-theme="xxx"]` 块，并把 `xxx` 加入 JS 的 `THEMES` 数组。

### 单主题模式（用户要求关闭主题切换）

用户说「关闭主题 / 单一配色 / 不要换肤」时：

1. 保留一套 `[data-theme="aqua"]`（或用户指定的主题变量块），`<html data-theme="aqua">` 固定。
2. **删除**：控制条 `button[data-act="theme"]`、JS 中 `THEMES` / `cycleTheme` / `initTheme` 的 localStorage 逻辑、`T` 键分支、toast 里「换主题」一行。
3. 仍可用 `prefers-color-scheme: dark` 作系统深色兜底（可选）。

### 锁定指定主题（用户点名某一配色）

用户说「用晴空主题 / theme azure / 默认雅紫」时：

1. 只保留该主题的 `[data-theme="..."]` 变量（或保留三套 CSS 但 HTML 固定 `data-theme="azure"` 且**无切换器**——推荐前者以减小体积）。
2. 去掉切换器（同单主题模式）。
3. 若用户说「3 主题但默认晴空」，则保留切换器，`initTheme` 初始值设为 `azure`，不写 localStorage 覆盖除非用户已选过。

### 主题 id 速查

| id | 中文名 | 主色倾向 |
|---|---|---|
| `aqua` | 青蓝 | 青绿 + 暖橙点缀 |
| `azure` | 晴空 | 蓝 +  cyan 点缀 |
| `violet` | 雅紫 | 紫 + 粉点缀 |

### 与模板库的关系

`templates/ppt-layouts/` 中的 `dark_tech` / `minimal_business` / `modern_academic` 属于**整包模板**（样式 + 装饰倾向），优先级高于内置 3 主题。用户同时指定模板与内置主题时，以模板为准。

---

## 版面填充与安全区（杜绝头重脚轻 / 控制条遮挡）

- `.slide` 已设 `display:flex; flex-direction:column; justify-content:center; gap:30px`：
  - 内容**少** → 默认 `center`，整体垂直居中，不要堆在顶部。
  - 内容**多** → 把该页 `.slide` 改 `justify-content:space-between` 让区块撑满。
- `.slide` 的 `padding` 底部已留 **116px 安全区**，固定控制条 `nav.ctrl`（`bottom:16px`）不会压住内容；不要把内容塞进这块安全区。
- 每页目标：内容占版心 **≥75%** 高度。偏空时优先「加一个组件 / 把列表升级成卡片或对比条 / 适度延展本页主题」，而不是放任大白或硬缩字。
- 一页放不下：宁可切成两页，**绝不缩字到 <20px** 来硬塞。
- 自检：把窗口缩到一半大小预览，确认①底部控制条不遮内容；②没有明显上挤下空；③最小字仍清晰。

---

## 3. 模板挑选指南（templates/ppt-layouts/）

用户点名后，**只取色 + 字体 + 装饰倾向**，重画 CSS 变量；不要拷贝 SVG 文件——SVG 是给 ppt-master 那一套用的。

| 模板 | 关键 CSS 变量 | 装饰建议 |
|---|---|---|
| `dark_tech` | `--bg:#0a0e1a; --primary:#0EA5E9; --accent:#10B981` 深色 | 网格底纹、霓虹边、`linear-gradient(135deg,...)` |
| `minimal_business` | `--bg:#fafaf9; --primary:#1f2937; --accent:#D97706` 暖白 | 大量留白、细线分隔、无渐变 |
| `modern_academic` | `--bg:#f8fafc; --primary:#1e40af; --accent:#7c3aed` 学院蓝 | 衬线大标题、章节序号居左 |

读 `templates/ppt-layouts/<name>/design_spec.md` 获取该模板的字号、间距、icon 风格细节，再翻译成本骨架的 CSS 变量。

---

## 4. 多 md 合并

```
file1.md → 章节封面（取自 file1 文件名）→ file1 内容页
file2.md → 章节封面（取自 file2 文件名）→ file2 内容页
…
```

如果用户给的多个 md 已经各自有 `# 标题`，使用各自的 H1 作为章节名，不再额外加文件名章节封面。

---

## 5. 常见踩坑

| 坑 | 规避 |
|---|---|
| **字号偏小、读者看着费劲**（最高频反馈） | @1920 正文 ≥20px、表格 ≥22px、卡片标题 ≥26px、主标题 48–56px；宁大勿小，放不下就切页，**绝不缩到 <20px 硬塞** |
| **头重脚轻**：内容堆上半屏、下半屏大白 | `.slide` flex 纵向 `center`（少）/`space-between`（多）；内容占版心 ≥75%；偏空先延展+换更丰富组件，再考虑居中 |
| **控制条遮住底部内容** | `.slide` 底部留 ≥116px 安全区；控制条保持紧凑（小 padding、bottom:16） |
| **对比条文字被压小/裁切** | 数值放 `.mbar-val`（条内左侧、深色 ≥18px），彩色填充只表示比例，别把文字塞进填充里 |
| **通篇圆点列表、单调** | 一份 deck 混搭 ≥4 种组件（卡片/KPI/对比条/架构图/流程图/时间轴/双栏…，见 §高质量组件库） |
| 有架构/流程/对比/时间线语义却纯文字罗列 | 优先出图（CSS 框图 `.arch`/`.flow`/`.timeline` 或内联 SVG） |
| `.deck` 用 `transform: scale` 后子元素 click 坐标错位 | 不影响——按钮在 `nav.ctrl` 里，不在 deck 内 |
| 演讲者视图缩略图字看不清 | 给 `body.overview section.slide` 加 `font-size:8px`，标题再放大 1.6 倍 |
| MD 里 `---` 同时是 YAML 分隔符 | 切页只认**正文区**的 `---`，YAML frontmatter 不算 |
| 图片 base64 过大导致 HTML 几 MB | >500KB 单图给警告；>5MB 拒绝内联，改外链并提示用户保留同目录图片 |
| 打印 PDF 时背景色丢失 | 浏览器打印面板需用户勾选"打印背景图形"，**话术里要主动提醒** |
| 全屏后字号意外缩放 | `fit()` 在 `fullscreenchange` 事件里重算 transform |
| 切主题后某些颜色没变 | 检查该处是否写死了 hex；**所有颜色必须走 CSS 变量**，深色文字/边框也不例外 |

---

## 6. 反幻觉清单（自检时勾一遍）

- [ ] 每个数字、人名、日期都能在源 MD 里找到出处
- [ ] 没有"提效 60%"这种没有根据的指标
- [ ] 演讲者备注没有捏造原文没说过的事实
- [ ] 章节顺序与 MD 一致，没有"为了节奏"重排
- [ ] 强制断页 `---` 都被尊重
- [ ] 末页 ending 没有重复添加（MD 已有 Q&A 时跳过）

---

## 7. 与未来 `toolkits/html_slides_to_pptx/` 的接口契约（重申）

只要本骨架严守以下 4 点，未来任意改 CSS / 加 layout 都不影响截图转换器：

1. `<main class="deck" data-format="...">` 包 N 个 `<section class="slide" data-index="N" data-layout="...">`
2. `window.deckAPI.{slideCount, goToSlide, getCurrent, getNotes}` 全部存在且行为正确
3. `?export=1` 触发 `body.export`，关动画 + 隐控件
4. 字体只用系统栈，不依赖外部字体加载

转换器只调 `deckAPI.goToSlide(i)` + `page.screenshot()` 就拿到全部 N 页，不解析 HTML。
