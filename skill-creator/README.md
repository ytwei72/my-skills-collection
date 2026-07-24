# skill-creator

创建、改进并度量 Agent Skill 的元技能（meta-skill）。它把「写技能」这件事变成一个可迭代、可量化的闭环：起草 → 用测试用例跑 → 人工 + 量化评估 → 根据反馈改进 → 重复，最后再优化技能的触发描述并打包交付。

## 适用场景

- 想从零创建一个新技能，但不确定 `SKILL.md` 该怎么写、目录该怎么组织
- 已经有技能草稿，想通过测试用例验证它到底有没有效果
- 想量化对比「用技能」和「不用技能（baseline）」的差异（通过率、耗时、Token）
- 觉得技能「该触发时不触发」，想优化 frontmatter 里的 `description` 提高触发准确率
- 想把改好的技能打包成可分发的 `.skill` 文件

## 核心工作流

技能开发被拆成一个可重复的循环，本模块会判断你当前处在哪一步并接手推进：

1. **明确意图**：技能要让 Claude 做什么、什么时候触发、输出格式是什么、是否需要测试用例
2. **起草 `SKILL.md`**：填写 `name` / `description` 及正文指令
3. **写测试用例**：2-3 条真实用户会说的话，存到 `evals/evals.json`
4. **跑测试**：对每条用例同时起两个子代理——一个带技能、一个作为 baseline（新建技能用「无技能」，改进技能用「旧版本快照」）
5. **评估结果**：
   - 用 `eval-viewer/generate_review.py` 启动可视化页面，让人工逐条查看输出并留反馈
   - 用 `scripts/aggregate_benchmark.py` 汇总量化指标（通过率、耗时、Token 的均值 ± 标准差及 delta）
6. **改进技能**：结合人工反馈和量化数据重写技能，从少量样例中「泛化」而非「过拟合」
7. **重复迭代**，直到满意或反馈全部通过
8. **可选：优化描述**：用触发评测集自动优化 `description`，提高触发命中率
9. **打包交付**：生成 `.skill` 文件

## 实例：用 skill-creator 从零创建一个技能

下面以「创建一个把**发票 PDF** 提取成结构化 CSV 的技能 `invoice-extractor`」为例，走一遍完整流程。你只需用自然语言和 Claude 对话，本模块会自动接管每一步。

### 第 0 步：触发 skill-creator

对 Claude 说明你的意图即可触发本模块：

```
我想做一个技能：把发票 PDF 里的金额、日期、开票方、税号提取成一张 CSV 表。
```

### 第 1 步：明确意图（Claude 会反问澄清）

Claude 会围绕关键问题和你确认，例如：

- 技能要做什么：从发票 PDF 提取字段并输出 CSV
- 什么时候触发：用户上传发票/账单 PDF 并要求「提取」「整理成表格」时
- 输出格式：一行一张发票，列为 `发票号,开票日期,开票方,税号,金额(含税),税额`
- 是否需要测试用例：输出可客观校验（字段是否提取正确），**适合**建测试用例

### 第 2 步：起草 `SKILL.md`

Claude 生成技能目录与草稿，`invoice-extractor/SKILL.md` 大致如下：

```markdown
---
name: invoice-extractor
description: 从发票/账单 PDF 中提取发票号、日期、开票方、税号、金额等字段并输出为 CSV。当用户上传发票、账单、报销单 PDF 并希望提取关键信息、整理成表格或批量汇总时使用，即使用户没有明确说"提取字段"也应触发。
---

# Invoice Extractor

## 工作流
1. 读取 PDF 文本（扫描件先做 OCR）
2. 按下述字段定位并抽取，缺失字段留空而非编造
3. 输出 CSV，表头固定为：发票号,开票日期,开票方,税号,金额(含税),税额

## 字段说明
- 金额：取"价税合计"，去掉货币符号，保留两位小数
- 税号：15/18/20 位纳税人识别号
...
```

### 第 3 步：写测试用例

Claude 准备 2-3 条真实用例，存到 `invoice-extractor/evals/evals.json`（先只写 prompt，断言留到跑测试时补）：

```json
{
  "skill_name": "invoice-extractor",
  "evals": [
    {"id": 1, "prompt": "把这张增值税专用发票整理成 CSV", "files": ["evals/files/vat_invoice.pdf"]},
    {"id": 2, "prompt": "downloads 里有 3 张餐饮发票，帮我提取金额和日期汇总成表格", "files": ["evals/files/receipt1.pdf", "evals/files/receipt2.pdf", "evals/files/receipt3.pdf"]}
  ]
}
```

Claude 会把用例发给你确认：「这几条测试看起来对吗？要加吗？」

### 第 4 步：跑测试（带技能 + baseline 同时跑）

对每条用例同时起两个子代理——一个**带 `invoice-extractor`**，一个**不带任何技能（baseline）**，结果写入 sibling 工作区：

```
invoice-extractor-workspace/
└── iteration-1/
    ├── extract-vat-invoice/
    │   ├── with_skill/outputs/     # 带技能的产出
    │   └── without_skill/outputs/  # baseline 产出
    └── batch-receipts/
        ├── with_skill/outputs/
        └── without_skill/outputs/
```

跑的同时，Claude 会为每条用例补上可客观校验的**断言**，例如「CSV 表头与约定完全一致」「金额等于价税合计 1234.56」「缺失税号时留空而非编造」。

### 第 5 步：评估结果（人工 + 量化）

先汇总量化基准，再启动可视化审核页：

```bash
python -m scripts.aggregate_benchmark invoice-extractor-workspace/iteration-1 --skill-name invoice-extractor
python eval-viewer/generate_review.py invoice-extractor-workspace/iteration-1 \
  --skill-name "invoice-extractor" \
  --benchmark invoice-extractor-workspace/iteration-1/benchmark.json
```

浏览器里有两个标签页：**Outputs** 逐条看输出并留反馈，**Benchmark** 看「带技能 vs baseline」的通过率/耗时/Token 对比。假设你留下反馈：「批量那条把 3 张发票合并成 1 行了，应该 3 行」。

### 第 6 步：根据反馈改进技能

Claude 读取 `feedback.json`，定位到问题——技能没说清「多文件 = 多行」，于是在 `SKILL.md` 里补充规则并解释原因（而非硬塞 MUST）：

```markdown
## 多张发票
每个 PDF 对应 CSV 里的一行。批量处理时逐个文件抽取后追加行，不要合并，
因为用户通常需要按发票逐笔对账。
```

### 第 7 步：重复迭代

改完后跑 `iteration-2/`，审核页加 `--previous-workspace invoice-extractor-workspace/iteration-1` 以并排对比上一轮。重复直到反馈全部通过或你满意。

### 第 8 步（可选）：优化触发描述

生成 20 条触发评测（含该触发/不该触发的近似用例），后台跑优化循环，用测试集得分挑出最佳 `description` 回填 frontmatter：

```bash
python -m scripts.run_loop \
  --eval-set invoice-extractor-workspace/trigger-eval.json \
  --skill-path invoice-extractor \
  --model <当前会话模型 ID> \
  --max-iterations 5 --verbose
```

### 第 9 步：打包交付

```bash
python -m scripts.package_skill invoice-extractor
```

得到 `invoice-extractor.skill`，即可分发或一键安装到 Claude 中。

---

## 目录结构

```
skill-creator/
├── SKILL.md              # 技能主体：完整工作流与写作规范
├── LICENSE.txt
├── agents/               # 专用子代理的指令说明
│   ├── grader.md         # 评分代理：对照断言逐条评判输出并给出证据
│   ├── comparator.md     # 盲评代理：不告知来源地对比两份输出
│   └── analyzer.md       # 分析代理：分析基准结果 / 谁赢了以及为什么
├── references/
│   └── schemas.md        # evals / grading / benchmark 等各类 JSON 结构定义
├── assets/
│   └── eval_review.html  # 触发评测集的人工审核模板
├── eval-viewer/
│   ├── generate_review.py# 生成并托管评测结果审核页（输出对比 + 基准两个标签页）
│   └── viewer.html
└── scripts/              # 确定性任务的可执行脚本
    ├── run_eval.py           # 跑触发评测：测某个 description 是否会触发技能
    ├── improve_description.py# 根据评测结果生成更优的 description
    ├── run_loop.py           # 触发优化主循环：train/test 拆分 + 多轮迭代，避免过拟合
    ├── aggregate_benchmark.py# 汇总各次运行的 grading.json 为基准统计
    ├── generate_report.py    # 生成优化过程的 HTML 报告
    ├── quick_validate.py     # 快速校验技能结构是否合法
    ├── package_skill.py      # 打包技能为可分发的 .skill 文件
    └── utils.py
```

## 渐进式披露（Progressive Disclosure）

技能采用三级加载机制，这也是写技能时组织内容的核心原则：

1. **元数据**（`name` + `description`）——始终在上下文中（约 100 词），决定是否触发
2. **`SKILL.md` 正文**——技能触发时加载（建议 < 500 行）
3. **捆绑资源**（`scripts/` / `references/` / `assets/`）——按需读取，脚本甚至无需加载即可执行

## 常用命令

汇总一次迭代的量化基准（在 `skill-creator` 目录下运行）：

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
```

启动评测结果审核页（第 2 轮及以后再加 `--previous-workspace`）：

```bash
python eval-viewer/generate_review.py <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json
```

> 无显示环境（Cowork / headless）时改用 `--static <output_path>` 生成独立 HTML 文件。

运行描述优化主循环（后台执行，`--model` 用当前会话所用模型 ID）：

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-skill> \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

打包技能为 `.skill` 文件：

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

## 写技能的几个要点

- **描述要「稍微 pushy」**：Claude 倾向于「该用时不用」，`description` 里要同时写清楚「做什么」和「什么时候用」，并适当强调触发场景
- **解释「为什么」而非堆砌 MUST**：与其写一堆全大写的 ALWAYS/NEVER，不如说明某条指令背后的原因，让模型理解意图后自行发挥
- **泛化而非过拟合**：只在几个样例上迭代是为了快，但技能要能用在成千上万个未见过的场景上，别为个别样例塞进死板约束
- **发现重复劳动就沉淀成脚本**：如果多个测试用例都各自写了类似的辅助脚本，就把它写一次放进 `scripts/`，让技能直接调用

## 运行环境说明

- **Claude Code / Cowork**：支持子代理，完整工作流（并行跑测试、baseline 对比、评分、量化基准）均可用
- **Claude.ai**：无子代理，逐条串行跑测试、跳过 baseline 与量化基准，以人工反馈为主；描述优化依赖 `claude` CLI，此环境下跳过

更完整的流程、写作规范与各环境差异，见 [`SKILL.md`](./SKILL.md)；各类 JSON 结构定义见 [`references/schemas.md`](./references/schemas.md)。
