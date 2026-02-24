<div align="center">

# 📄 cc_paper_tool

**AI-Powered arxiv Paper Analyzer for Claude Code**

[![Python 3](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Slash_Command-blueviolet?logo=anthropic&logoColor=white)](https://claude.ai)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green?logo=playwright&logoColor=white)](https://playwright.dev)
[![KaTeX](https://img.shields.io/badge/KaTeX-Math_Rendering-orange)](https://katex.org)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](LICENSE)

一个基于 Claude Code 的 arxiv 论文深度分析工具。输入论文链接，自动生成两种 PDF 报告。

</div>

---

- **逐行翻译版** (`*_dual.pdf`) — 左页原文，右页逐句中文翻译 + 行内批注
- **精炼版** (`*_summary.pdf`) — 结构化深度分析 + 代码解读

## 使用方式

```bash
# 1. 克隆仓库
git clone git@github.com:lyfeng001/cc_paper_tool.git
cd cc_paper_tool

# 2. 安装依赖
bash setup.sh

# 3. 在项目目录下启动 Claude Code，输入：
/analyze-paper https://arxiv.org/abs/2601.16163 cosmos_policy
```

## 工作流程

`/analyze-paper` 会自动执行 5 个阶段：

1. **资料收集** — 下载 PDF，搜索并克隆开源代码
2. **精炼版报告** — 全文结构化翻译 + 批注 + 代码分析
3. **逐行翻译版** — 逐页忠实翻译，并行多 agent 加速
4. **PDF 生成** — Markdown → HTML + KaTeX → Playwright → PDF
5. **质量检查** — 公式渲染、页面对齐、批注完整性

## 产出结构

```
./
├── papers/{name}.pdf              # 原始论文
├── extracted/{name}_pages.json    # 逐页文本提取
├── translations/{name}_p*.md      # 逐页翻译
├── {name}_annotated.md            # 精炼版源文件
└── output/
    ├── {name}_dual.pdf            # 逐行翻译版
    └── {name}_summary.pdf         # 精炼版
```

## 依赖

- Python 3
- [PyMuPDF](https://pymupdf.readthedocs.io/) — PDF 文本提取与合并
- [markdown](https://python-markdown.github.io/) — Markdown → HTML
- [Playwright](https://playwright.dev/python/) + Chromium — HTML 渲染为 PDF
- [KaTeX](https://katex.org/) (CDN) — LaTeX 公式渲染

## 手动使用脚本

也可以跳过 slash command，直接调用脚本：

```bash
# 提取 PDF 文本
python3 extract_pages.py . {paper_name}

# 生成 PDF（需先完成翻译）
python3 generate_pdf.py . dual {paper_name}    # 逐行翻译版
python3 generate_pdf.py . summary {paper_name} # 精炼版
python3 generate_pdf.py . all                   # 全部
```

## License

本项目采用 [CC BY-NC 4.0](LICENSE) 许可证 — 允许自由使用和修改，但禁止商业用途。
