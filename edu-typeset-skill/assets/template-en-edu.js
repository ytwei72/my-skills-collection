/**
 * 模板类型：英语教学辅导材料
 * Template: English Teaching & Learning Aid Material
 *
 * 适用场景：英语课外辅导材料、教辅练习册、讲义、阅读理解配套资料
 * 使用方式：将本文件中的样式定义（STYLES、COLOR、FONT）和组件函数
 *           复制到 build_doc.js 中，填入实际文档内容后运行。
 *
 * 注意：模板中的示例内容（书名、学校名等）均为占位符，使用时替换为实际内容。
 */

const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
    ShadingType, VerticalAlign, PageNumber, PageBreak, LevelFormat,
  } = require('docx');
  const fs = require('fs');
  
  // ══════════════════════════════════════════════════════════
  //  COLOR PALETTE  色彩系统
  // ══════════════════════════════════════════════════════════
  const COLOR = {
    titleDeep:   '1A3A5C',   // 书名/大标题
    chapterBlue: '2E6B9E',   // 章节标题
    sectionGray: '4A4A4A',   // 小节标题
    bodyText:    '1A1A1A',   // 正文
    engText:     '00008B',   // 英语原文（深蓝）
    cnTranslate: '333333',   // 中文译文（深灰）
    hintRed:     '8B0000',   // 提示语/警示框
    answerGreen: '006400',   // 答案
    analysisGray:'333333',   // 解析说明
    ruleColor:   '8B4513',   // 语法规则框
    noteColor:   '555555',   // 注释/页眉
    border:      'BBBBBB',   // 通用边框
    // 背景色
    bgHint:      'FFF8DC',   // 提示语背景（cornsilk）
    bgAnswer:    'F0FFF0',   // 答案背景（honeydew）
    bgChapter:   'EBF3FB',   // 章节背景（浅蓝）
    bgRule:      'FFF9F0',   // 规则框背景（浅橙）
    bgAnswerHead:'D4EDDA',   // 答案标签背景（深绿）
  };
  
  // ══════════════════════════════════════════════════════════
  //  FONT SETTINGS  字体设置
  // ══════════════════════════════════════════════════════════
  const FONT = {
    cnBody:   '宋体',         // 中文正文
    cnTitle:  '黑体',         // 大标题
    cnHead:   '微软雅黑',     // 标题/说明
    enBody:   'Times New Roman',  // 英文正文
    enHead:   'Times New Roman',  // 英文标题
  };
  
  // ══════════════════════════════════════════════════════════
  //  HELPER UTILITIES  基础工具函数
  // ══════════════════════════════════════════════════════════
  
  /** 细边框（表格通用） */
  function border(color = COLOR.border) {
    const b = { style: BorderStyle.SINGLE, size: 4, color };
    return { top: b, bottom: b, left: b, right: b };
  }
  
  /** 水平分割线（段落底边框实现，不用表格） */
  function hrule(color = COLOR.chapterBlue) {
    return new Paragraph({
      children: [new TextRun({ text: '' })],
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color, space: 1 } },
      spacing: { before: 120, after: 120 },
    });
  }
  
  /** 空白间距段落 */
  function spacer(before = 80, after = 80) {
    return new Paragraph({ children: [new TextRun('')], spacing: { before, after } });
  }

  /**
   * 还原 Pandoc / Markdown 中间稿里的转义字符。
   * docx→md 时连续下划线常被写成 \_\_\_\_；若原样写入 docx 会显示为「反斜杠+下划线」。
   * 所有来自 extract / pandoc 的字符串在写入 TextRun 前必须经此函数（或在 engPara/cnPara 内已调用）。
   */
  function normalizeExtractedText(text) {
    if (text == null || text === '') return '';
    return String(text)
      .replace(/\\([\\_*`[\]()#+.!-])/g, '$1')
      .replace(/\uFF3F/g, '_');
  }
  
  /** 英语正文段落（深蓝色，首行缩进） */
  function engPara(text) {
    text = normalizeExtractedText(text);
    return new Paragraph({
      children: [new TextRun({ text, font: FONT.enBody, size: 22, color: COLOR.engText })],
      spacing: { before: 80, after: 80, line: 300 },
      indent: { firstLine: 360 },
    });
  }
  
  /** 中文译文段落（斜体深灰，首行缩进） */
  function cnPara(text) {
    text = normalizeExtractedText(text);
    return new Paragraph({
      children: [new TextRun({ text, font: FONT.cnBody, size: 21, color: COLOR.cnTranslate, italics: true })],
      spacing: { before: 60, after: 80, line: 280 },
      indent: { firstLine: 360 },
    });
  }
  
  // ══════════════════════════════════════════════════════════
  //  BLOCK COMPONENTS  内容块组件
  // ══════════════════════════════════════════════════════════
  
  /**
   * 封面标题块
   * @param {string} enTitle  英文书名
   * @param {string} cnTitle  中文书名
   * @param {string} subtitle 副标题（系列名/版本说明）
   * @param {string} org      出版机构/学校（可选）
   * @param {string} orgNote  机构备注（可选，如"内部流通"）
   */
  function coverBlock(enTitle, cnTitle, subtitle, org = '', orgNote = '') {
    const items = [
      new Paragraph({ children: [new TextRun({ text: '', size: 48 })], spacing: { before: 0, after: 480 } }),
      new Paragraph({
        children: [new TextRun({ text: enTitle, font: FONT.enHead, size: 52, bold: true, color: COLOR.titleDeep })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 200 },
      }),
      new Paragraph({
        children: [new TextRun({ text: cnTitle, font: FONT.cnTitle, size: 44, bold: true, color: COLOR.titleDeep })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 400 },
      }),
      hrule(COLOR.chapterBlue),
      new Paragraph({
        children: [new TextRun({ text: subtitle, font: FONT.cnHead, size: 28, bold: true, color: COLOR.chapterBlue })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 160 },
      }),
    ];
    if (org) {
      items.push(new Paragraph({
        children: [new TextRun({ text: org, font: FONT.cnBody, size: 22, color: COLOR.sectionGray })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 40 },
      }));
    }
    if (orgNote) {
      items.push(new Paragraph({
        children: [new TextRun({ text: orgNote, font: FONT.cnBody, size: 20, color: COLOR.noteColor, italics: true })],
        alignment: AlignmentType.CENTER,
        spacing: { before: 40, after: 480 },
      }));
    }
    return items;
  }
  
  /**
   * 书目目的/前言表格
   * @param {Array<[string, string]>} items  [[标签, 说明文字], ...]
   * @param {string} title  表格前的标题文字
   * @param {string} closing  表格后的结语（可选）
   */
  function purposeTable(items, title = '本书目的', closing = '') {
    const rows = items.map(([label, text]) =>
      new TableRow({ children: [
        new TableCell({
          width: { size: 1200, type: WidthType.DXA },
          borders: border(), shading: { fill: COLOR.bgChapter, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 140, right: 140 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text: label, font: FONT.cnHead, size: 22, bold: true, color: COLOR.chapterBlue })],
            alignment: AlignmentType.CENTER,
          })],
        }),
        new TableCell({
          width: { size: 7760, type: WidthType.DXA },
          borders: border(),
          margins: { top: 80, bottom: 80, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text, font: FONT.cnBody, size: 22, color: COLOR.bodyText })],
          })],
        }),
      ]}),
    );
    const result = [
      new Paragraph({
        children: [new TextRun({ text: title, font: FONT.cnHead, size: 26, bold: true, color: COLOR.chapterBlue })],
        spacing: { before: 240, after: 120 },
      }),
      new Table({ width: { size: 8960, type: WidthType.DXA }, columnWidths: [1200, 7760], rows }),
    ];
    if (closing) {
      result.push(spacer(80, 40));
      result.push(new Paragraph({
        children: [new TextRun({ text: closing, font: FONT.cnBody, size: 22, italics: true, color: COLOR.sectionGray })],
        alignment: AlignmentType.CENTER, spacing: { before: 80, after: 240 },
      }));
    }
    return result;
  }
  
  /**
   * 章节标题块（带左色块边框 + 浅蓝背景）
   * @param {string} enTitle  英文标题
   * @param {string} cnTitle  中文标题（可选）
   */
  function chapterBlock(enTitle, cnTitle = '') {
    return [
      spacer(0, 160),
      new Table({
        width: { size: 8960, type: WidthType.DXA },
        columnWidths: [8960],
        rows: [new TableRow({ children: [new TableCell({
          borders: {
            top: { style: BorderStyle.NONE },
            bottom: { style: BorderStyle.SINGLE, size: 8, color: COLOR.chapterBlue },
            left: { style: BorderStyle.THICK, size: 24, color: COLOR.chapterBlue },
            right: { style: BorderStyle.NONE },
          },
          shading: { fill: COLOR.bgChapter, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 200, right: 140 },
          children: [
            new Paragraph({
              children: [new TextRun({ text: enTitle, font: FONT.enHead, size: 30, bold: true, color: COLOR.chapterBlue })],
              spacing: { before: 0, after: cnTitle ? 40 : 0 },
            }),
            ...(cnTitle ? [new Paragraph({
              children: [new TextRun({ text: cnTitle, font: FONT.cnHead, size: 24, color: COLOR.sectionGray })],
              spacing: { before: 0, after: 0 },
            })] : []),
          ],
        })]})],
      }),
      spacer(120, 0),
    ];
  }
  
  /**
   * 小节标题（带底部细线）
   * @param {string} text   标题文字
   * @param {string} color  颜色（默认深灰）
   */
  function sectionHead(text, color = COLOR.sectionGray) {
    return new Paragraph({
      children: [new TextRun({ text, font: FONT.cnHead, size: 24, bold: true, color })],
      spacing: { before: 240, after: 80 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color, space: 1 } },
    });
  }
  
  /**
   * 提示语框（带左侧深红粗线 + 米黄背景）
   * @param {string} text  提示内容（多行用 \n 分隔，函数内会拆分）
   */
  function hintBox(text) {
    const lines = text.split('\n');
    return new Table({
      width: { size: 8960, type: WidthType.DXA },
      columnWidths: [8960],
      rows: [new TableRow({ children: [new TableCell({
        borders: {
          top: { style: BorderStyle.DOTTED, size: 6, color: COLOR.hintRed },
          bottom: { style: BorderStyle.DOTTED, size: 6, color: COLOR.hintRed },
          left: { style: BorderStyle.THICK, size: 16, color: COLOR.hintRed },
          right: { style: BorderStyle.NONE },
        },
        shading: { fill: COLOR.bgHint, type: ShadingType.CLEAR },
        margins: { top: 60, bottom: 60, left: 180, right: 140 },
        children: [
          new Paragraph({
            children: [new TextRun({ text: '【提示语】', font: FONT.cnHead, size: 20, bold: true, color: COLOR.hintRed })],
            spacing: { before: 0, after: 40 },
          }),
          ...lines.map(line => new Paragraph({
            children: [new TextRun({ text: line, font: FONT.cnBody, size: 21, color: COLOR.hintRed })],
            spacing: { before: 0, after: 20 },
          })),
        ],
      })]})],
    });
  }
  
  /**
   * 答案解析块（双行表格：答案行 + 解析行）
   * @param {string|number} num      题号
   * @param {string} answer          答案文本
   * @param {string} analysis        解析文本（可为空）
   */
  function answerBlock(num, answer, analysis = '') {
    const rows = [
      new TableRow({ children: [
        new TableCell({
          width: { size: 1000, type: WidthType.DXA },
          borders: border('AADDAA'),
          shading: { fill: COLOR.bgAnswerHead, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text: `答案 ${num}`, font: FONT.cnHead, size: 21, bold: true, color: '1E5631' })],
            alignment: AlignmentType.CENTER,
          })],
        }),
        new TableCell({
          width: { size: 7960, type: WidthType.DXA },
          borders: border('AADDAA'),
          shading: { fill: COLOR.bgAnswer, type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text: answer, font: FONT.enBody, size: 22, bold: true, color: COLOR.answerGreen })],
          })],
        }),
      ]}),
    ];
    if (analysis) {
      rows.push(new TableRow({ children: [
        new TableCell({
          width: { size: 1000, type: WidthType.DXA },
          borders: border(),
          shading: { fill: 'F8F8F8', type: ShadingType.CLEAR },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: [new TextRun({ text: '解析', font: FONT.cnHead, size: 21, color: COLOR.hintRed })],
            alignment: AlignmentType.CENTER,
          })],
        }),
        new TableCell({
          width: { size: 7960, type: WidthType.DXA },
          borders: border(),
          margins: { top: 60, bottom: 60, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text: analysis, font: FONT.cnBody, size: 21, color: COLOR.analysisGray })],
            spacing: { line: 280 },
          })],
        }),
      ]}));
    }
    return new Table({ width: { size: 8960, type: WidthType.DXA }, columnWidths: [1000, 7960], rows });
  }
  
  /**
   * 语法规则框（带左侧棕色粗线 + 浅橙背景）
   * @param {string} title   规则框标题
   * @param {string[]} lines 规则内容行数组
   */
  function ruleBox(title, lines) {
    return new Table({
      width: { size: 8960, type: WidthType.DXA },
      columnWidths: [8960],
      rows: [new TableRow({ children: [new TableCell({
        borders: {
          top: { style: BorderStyle.SINGLE, size: 6, color: COLOR.ruleColor },
          bottom: { style: BorderStyle.SINGLE, size: 6, color: COLOR.ruleColor },
          left: { style: BorderStyle.THICK, size: 12, color: COLOR.ruleColor },
          right: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border },
        },
        shading: { fill: COLOR.bgRule, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 180, right: 140 },
        children: [
          new Paragraph({
            children: [new TextRun({ text: title, font: FONT.cnHead, size: 22, bold: true, color: COLOR.ruleColor })],
            spacing: { before: 60, after: 60 },
          }),
          ...lines.map(line => new Paragraph({
            children: [new TextRun({ text: line, font: line.match(/[a-zA-Z]/) ? FONT.enBody : FONT.cnBody, size: 21, color: COLOR.bodyText })],
            spacing: { before: 40, after: 40 },
            indent: { left: 240 },
          })),
        ],
      })]})],
    });
  }
  
  /**
   * 顺口溜/记忆口诀框（居中，双边框）
   * @param {string[]} lines  口诀行数组
   */
  function rhymeBox(lines) {
    return new Table({
      width: { size: 8960, type: WidthType.DXA },
      columnWidths: [8960],
      rows: [new TableRow({ children: [new TableCell({
        borders: {
          top: { style: BorderStyle.DOUBLE, size: 6, color: COLOR.chapterBlue },
          bottom: { style: BorderStyle.DOUBLE, size: 6, color: COLOR.chapterBlue },
          left: { style: BorderStyle.DOUBLE, size: 6, color: COLOR.chapterBlue },
          right: { style: BorderStyle.DOUBLE, size: 6, color: COLOR.chapterBlue },
        },
        shading: { fill: 'EEF5FB', type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 200, right: 200 },
        children: lines.map(line => new Paragraph({
          children: [new TextRun({
            text: line,
            font: line.match(/[\u4e00-\u9fa5]/) ? FONT.cnBody : FONT.enBody,
            size: 22, color: COLOR.chapterBlue,
          })],
          alignment: AlignmentType.CENTER,
          spacing: { before: 40, after: 40 },
        })),
      })]})],
    });
  }
  
  /**
   * 通用两列对照表（词汇辨析、知识点对比等）
   * @param {string[]} headers      表头 [左列名, 右列名]
   * @param {string[][]} rows_data  数据行 [[左, 右], ...]
   * @param {number[]} colWidths    列宽 DXA，默认 [4480, 4480]
   */
  function twoColumnTable(headers, rows_data, colWidths = [4480, 4480]) {
    const headerRow = new TableRow({
      tableHeader: true,
      children: headers.map((h, i) => new TableCell({
        width: { size: colWidths[i], type: WidthType.DXA },
        borders: border(COLOR.chapterBlue),
        shading: { fill: COLOR.bgChapter, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({ text: h, font: FONT.cnHead, size: 21, bold: true, color: COLOR.chapterBlue })],
          alignment: AlignmentType.CENTER,
        })],
      })),
    });
    const dataRows = rows_data.map(cells => new TableRow({
      children: cells.map((cell, i) => new TableCell({
        width: { size: colWidths[i], type: WidthType.DXA },
        borders: border(),
        margins: { top: 60, bottom: 60, left: 120, right: 120 },
        children: [new Paragraph({
          children: [new TextRun({
            text: cell,
            font: cell.match(/[a-zA-Z]/) ? FONT.enBody : FONT.cnBody,
            size: 21, color: COLOR.bodyText,
          })],
        })],
      })),
    }));
    return new Table({
      width: { size: colWidths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
      columnWidths: colWidths,
      rows: [headerRow, ...dataRows],
    });
  }
  
  // ══════════════════════════════════════════════════════════
  //  DOCUMENT BUILDER  文档构建入口
  // ══════════════════════════════════════════════════════════
  
  /**
   * 构建完整文档
   * @param {Object} meta    文档元数据（见下方说明）
   * @param {Array}  content 正文内容数组（Paragraph / Table 实例）
   * @param {Array}  appendix 附录内容数组（Paragraph / Table 实例）
   * @param {string} outputPath 输出路径
   *
   * meta 结构：
   * {
   *   enTitle: 'Book English Title',
   *   cnTitle: '书名',
   *   subtitle: '副标题/系列名',
   *   org: '学校/机构名（可选）',
   *   orgNote: '内部说明（可选）',
   *   headerText: '页眉文字',
   * }
   */
  function buildDocument(meta, content, appendix, outputPath) {
    const doc = new Document({
      styles: {
        default: {
          document: {
            run: { font: FONT.enBody, size: 22, color: COLOR.bodyText },
            paragraph: { spacing: { line: 276 } },
          },
        },
        paragraphStyles: [
          {
            id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
            run: { font: FONT.cnTitle, size: 36, bold: true, color: COLOR.titleDeep },
            paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 },
          },
          {
            id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
            run: { font: FONT.cnHead, size: 28, bold: true, color: COLOR.chapterBlue },
            paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 },
          },
        ],
      },
      sections: [{
        properties: {
          page: {
            size: { width: 11906, height: 16838 },        // A4
            margin: { top: 1134, right: 1134, bottom: 1134, left: 1440 },
          },
        },
        headers: {
          default: new Header({
            children: [new Paragraph({
              children: [new TextRun({ text: meta.headerText ?? `${meta.enTitle}  ${meta.cnTitle}`, font: FONT.cnHead, size: 18, color: COLOR.noteColor })],
              border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border, space: 1 } },
              spacing: { before: 0, after: 80 },
            })],
          }),
        },
        footers: {
          default: new Footer({
            children: [new Paragraph({
              children: [
                new TextRun({ text: '第 ', font: FONT.cnBody, size: 18, color: COLOR.noteColor }),
                new TextRun({ children: [PageNumber.CURRENT], font: FONT.enBody, size: 18, color: COLOR.noteColor }),
                new TextRun({ text: ' 页', font: FONT.cnBody, size: 18, color: COLOR.noteColor }),
              ],
              alignment: AlignmentType.CENTER,
              border: { top: { style: BorderStyle.SINGLE, size: 4, color: COLOR.border, space: 1 } },
              spacing: { before: 80, after: 0 },
            })],
          }),
        },
        children: [
          // 封面
          ...coverBlock(meta.enTitle, meta.cnTitle, meta.subtitle, meta.org, meta.orgNote),
          new Paragraph({ children: [new PageBreak()] }),
          // 正文
          ...content,
          // 附录
          new Paragraph({ children: [new PageBreak()] }),
          sectionHead('附录：知识点总结', COLOR.titleDeep),
          hrule(COLOR.chapterBlue),
          spacer(80, 80),
          ...appendix,
          // 版权尾注
          spacer(160, 80),
          hrule(COLOR.chapterBlue),
          new Paragraph({
            children: [new TextRun({ text: meta.copyright ?? '内部学习材料，版权所有，未经许可不得转载。', font: FONT.cnBody, size: 18, color: COLOR.noteColor, italics: true })],
            alignment: AlignmentType.CENTER,
            spacing: { before: 80, after: 80 },
          }),
        ],
      }],
    });
  
    return Packer.toBuffer(doc).then(buf => {
      fs.writeFileSync(outputPath, buf);
      console.log(`✅ 文档已生成：${outputPath}`);
      return outputPath;
    }).catch(err => { console.error(err); process.exit(1); });
  }
  
  // ══════════════════════════════════════════════════════════
  //  USAGE EXAMPLE  使用示例（替换为实际内容）
  // ══════════════════════════════════════════════════════════
  /*
  const content = [
    ...chapterBlock('Chapter 1 · Title', '第一章·标题'),
    sectionHead('课文与练习'),
    hintBox('根据提示语填空'),
    engPara('English text with blanks【1. verb form】here.'),
    cnPara('对应中文译文。'),
    spacer(),
    answerBlock(1, 'called（非谓语·过去分词·被动）', '解析内容...'),
    spacer(60, 60),
    ruleBox('非谓语动词三要点', [
      '（1）非谓语动词就是指"不是谓语"的动词。',
      '（2）非谓语动词是在句子有谓语动词的情况下出现的。',
      '（3）三种形式：to do、doing、done',
    ]),
  ];
  
  const appendix = [
    sectionHead('不规则动词表（三词经）', COLOR.chapterBlue),
    twoColumnTable(
      ['原形', '过去式', '过去分词', '中文'],
      [['go', 'went', 'gone', '去'], ['come', 'came', 'come', '来']],
      [2240, 2240, 2240, 2240]
    ),
    spacer(80, 80),
    ruleBox('双写规则', [
      '条件：词尾为 p/b/t/d/m/n/k/g，后三字母为"辅-元-辅"，且为单音节词。',
      '示例：stop → stopped / stopping',
    ]),
  ];
  
  buildDocument(
    {
      enTitle: 'Book English Title',
      cnTitle: '书名',
      subtitle: '副标题',
      org: '学校名称',
      orgNote: '内部流通',
      headerText: 'Book English Title  书名',
      copyright: '内部学习材料，版权所有。',
    },
    content,
    appendix,
    '/mnt/user-data/outputs/output_排版版.docx'
  );
  */
  
  module.exports = {
    COLOR, FONT,
    border, hrule, spacer, normalizeExtractedText, engPara, cnPara,
    coverBlock, purposeTable, chapterBlock, sectionHead,
    hintBox, answerBlock, ruleBox, rhymeBox, twoColumnTable,
    buildDocument,
  };