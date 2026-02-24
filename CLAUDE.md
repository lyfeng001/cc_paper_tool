# 论文深度分析工具链

当用户输入 `/analyze-paper <arxiv_url> [paper_name]` 时，按 `.claude/commands/analyze-paper.md` 中定义的 5 个 Phase 执行，生成两种 PDF 报告。

## 工具文件

- `generate_pdf.py` — PDF 生成器（Markdown → HTML+KaTeX → Playwright → PDF）
- `extract_pages.py` — PDF 逐页文本提取
- `setup.sh` — 一键安装依赖（PyMuPDF, markdown, playwright, chromium）

## 快速开始

```bash
# 1. 安装依赖（首次）
bash setup.sh

# 2. 使用 Claude Code 的 slash command
/analyze-paper https://arxiv.org/abs/2601.16163 cosmos_policy
```

## 工作目录结构

执行后当前目录下会生成：

```
./
├── papers/{name}.pdf              # 原始论文 PDF
├── extracted/{name}_pages.json    # 逐页提取文本（中间产物）
├── translations/{name}_p*.md      # 逐页翻译（<!-- PAGE N --> 标记，中间产物）
├── {name}_annotated.md            # 精炼版 markdown 源文件
└── output/
    ├── {name}_dual.pdf            # 逐行翻译版（左原文右翻译）
    └── {name}_summary.pdf         # 精炼版（单页）
```

## 执行流程

详见 `.claude/commands/analyze-paper.md`，核心 5 个 Phase：
1. 资料收集（下载 PDF + 搜索/克隆代码）
2. 精炼版报告（结构化深度分析 + 代码解读）
3. 逐行翻译版（逐页忠实翻译 + 行内批注）
4. PDF 生成（HTML+KaTeX 渲染）
5. 质量检查
