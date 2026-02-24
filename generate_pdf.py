#!/usr/bin/env python3
"""
论文报告 PDF 生成器（路径无关版本）

用法:
  python3 generate_pdf.py <workspace_dir> dual [paper_name]
  python3 generate_pdf.py <workspace_dir> summary [paper_name]
  python3 generate_pdf.py <workspace_dir> all [paper_name]

workspace_dir 结构:
  papers/            原始 PDF
  translations/      逐页翻译 markdown（含 <!-- PAGE N --> 标记）
  *_annotated.md     精炼版 markdown
  output/            输出目录（自动创建）
"""
import fitz
import os
import re
import sys
import glob
import tempfile
import markdown
from playwright.sync_api import sync_playwright

PAGE_W = 595.28  # A4 pt
PAGE_H = 841.89

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css">
<script defer
  src="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.js">
</script>
<script defer
  src="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false}
    ],
    throwOnError: false
  });">
</script>
<style>
@page {
  size: 595.28pt 841.89pt;
  margin: 30pt 28pt 30pt 28pt;
}
body {
  font-family: "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei",
               "Hiragino Sans GB", sans-serif;
  font-size: 9pt;
  line-height: 1.7;
  color: #1a1a1a;
  word-wrap: break-word;
  overflow-wrap: break-word;
}
h1 { font-size: 14pt; margin: 12pt 0 6pt; color: #111; }
h2 { font-size: 12pt; margin: 10pt 0 5pt; color: #222; }
h3 { font-size: 10.5pt; margin: 8pt 0 4pt; color: #333; }
h4 { font-size: 9.5pt; margin: 6pt 0 3pt; color: #333; }
p { margin: 4pt 0; }
blockquote {
  margin: 6pt 0; padding: 6pt 10pt;
  border-left: 3pt solid #3366cc; background: #edf0fa;
  color: #1a3366; font-size: 8.5pt; line-height: 1.6;
}
blockquote p { margin: 2pt 0; }
table {
  border-collapse: collapse; width: 100%;
  font-size: 7pt; margin: 6pt 0;
}
th, td { border: 0.5pt solid #ccc; padding: 3pt 4pt; text-align: left; }
th { background: #e0e4ee; font-weight: bold; }
tr:nth-child(even) { background: #f6f6f6; }
pre {
  background: #f4f4f4; padding: 6pt 8pt;
  font-size: 7.5pt; line-height: 1.4;
  overflow-x: hidden; white-space: pre-wrap; word-break: break-all;
}
code {
  font-family: "SF Mono", "Menlo", "Courier New", monospace;
  font-size: 8pt; background: #f0f0f0; padding: 1pt 3pt; border-radius: 2pt;
}
pre code { background: none; padding: 0; }
hr { border: none; border-top: 0.5pt solid #ccc; margin: 8pt 0; }
.katex-display {
  margin: 6pt 0; padding: 4pt 8pt;
  background: #f9f9f2; border-left: 2pt solid #5a9a5a;
  overflow-x: auto;
}
</style>
</head>
<body>
%%CONTENT%%
</body>
</html>"""


# ---------- 公式保护：防止 markdown 破坏 LaTeX ----------

def protect_math(md_text):
    """将 $...$ 和 $$...$$ 替换为占位符，返回 (处理后文本, 还原映射)"""
    placeholders = {}
    counter = [0]

    def _replace_block(m):
        key = f"MATHBLOCK{counter[0]:04d}"
        counter[0] += 1
        # 保留原始 LaTeX，用 <span> 包裹防止 markdown 处理
        placeholders[key] = m.group(0)
        return key

    def _replace_inline(m):
        key = f"MATHINLINE{counter[0]:04d}"
        counter[0] += 1
        placeholders[key] = m.group(0)
        return key

    # 先处理 $$...$$ (块级，可能跨行)
    text = re.sub(r'\$\$(.+?)\$\$', _replace_block, md_text, flags=re.DOTALL)
    # 再处理 $...$ (行内，不跨行)
    text = re.sub(r'(?<!\$)\$(?!\$)(.+?)\$(?!\$)', _replace_inline, text)
    return text, placeholders


def restore_math(html_text, placeholders):
    """将占位符还原为原始 LaTeX"""
    for key, original in placeholders.items():
        html_text = html_text.replace(key, original)
    return html_text


# ---------- Markdown → HTML ----------

def md_to_html(md_text):
    """Markdown → HTML，保护公式不被 markdown 破坏"""
    protected, placeholders = protect_math(md_text)
    html = markdown.markdown(protected, extensions=[
        'tables', 'fenced_code'
    ])
    html = restore_math(html, placeholders)
    return html


# ---------- 翻译文件合并 ----------

def merge_translations(workspace, paper_name):
    pattern = os.path.join(workspace, "translations", f"{paper_name}_p*.md")
    files = sorted(glob.glob(pattern))
    if not files:
        return {}
    all_text = ""
    for f in files:
        with open(f, 'r', encoding='utf-8') as fh:
            all_text += fh.read() + "\n"
    pages = {}
    parts = re.split(r'<!--\s*PAGE\s+(\d+)\s*-->', all_text)
    idx = 1
    while idx < len(parts) - 1:
        page_num = int(parts[idx])
        content = parts[idx + 1].strip()
        pages[page_num] = content
        idx += 2
    return pages


# ---------- Playwright 渲染 ----------

_browser = None

def get_browser():
    """复用浏览器实例，避免每页都启动"""
    global _browser
    if _browser is None:
        pw = sync_playwright().start()
        _browser = pw.chromium.launch()
    return _browser


def close_browser():
    global _browser
    if _browser:
        _browser.close()
        _browser = None


def render_html_to_pdf(html_str, output_path):
    """用 Playwright 将 HTML 渲染为 PDF"""
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False,
                                     mode='w', encoding='utf-8') as f:
        f.write(html_str)
        html_path = f.name
    try:
        browser = get_browser()
        page = browser.new_page()
        page.goto(f'file://{html_path}', wait_until='networkidle')
        page.wait_for_timeout(1500)
        page.pdf(path=output_path, format='A4',
                 margin={'top': '0.4in', 'bottom': '0.4in',
                         'left': '0.4in', 'right': '0.4in'},
                 print_background=True)
        page.close()
    finally:
        os.unlink(html_path)


# ---------- 逐页渲染 + 双页合并 ----------

def generate_aligned_pdf(workspace, paper_name):
    pdf_file = os.path.join(workspace, "papers", f"{paper_name}.pdf")
    output_dir = os.path.join(workspace, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{paper_name}_dual.pdf")
    print(f"  处理: {paper_name}")

    pages_dict = merge_translations(workspace, paper_name)
    if not pages_dict:
        print(f"    无翻译文件，跳过")
        return

    src = fitz.open(pdf_file)
    src_n = len(src)
    print(f"    原文: {src_n} 页, 翻译覆盖: {len(pages_dict)} 页")

    out = fitz.open()
    spread_w = PAGE_W * 2

    for pg_num in range(1, src_n + 1):
        if pg_num in pages_dict:
            # 为这一页单独生成翻译 PDF
            html_body = md_to_html(pages_dict[pg_num])
            full_html = HTML_TEMPLATE.replace("%%CONTENT%%", html_body)
            tmp_pdf = os.path.join(output_dir,
                                   f"_{paper_name}_p{pg_num}.pdf")
            render_html_to_pdf(full_html, tmp_pdf)

            trans_doc = fitz.open(tmp_pdf)
            trans_pages = len(trans_doc)

            # 第一个 spread：左=原文，右=翻译第1页
            sp = out.new_page(width=spread_w, height=PAGE_H)
            _place_src(sp, src, pg_num - 1)
            sp.show_pdf_page(fitz.Rect(PAGE_W, 0, spread_w, PAGE_H),
                            trans_doc, 0)
            _divider(sp, pg_num)

            # 翻译溢出页：左=空白（重复原文），右=翻译后续页
            for tp in range(1, trans_pages):
                sp = out.new_page(width=spread_w, height=PAGE_H)
                _place_src(sp, src, pg_num - 1)  # 重复原文
                sp.show_pdf_page(fitz.Rect(PAGE_W, 0, spread_w, PAGE_H),
                                trans_doc, tp)
                _divider(sp, pg_num)

            trans_doc.close()
            os.unlink(tmp_pdf)

            if trans_pages > 1:
                print(f"    第 {pg_num} 页翻译溢出 → {trans_pages} 页")
        else:
            # 无翻译：左=原文，右=空白
            sp = out.new_page(width=spread_w, height=PAGE_H)
            _place_src(sp, src, pg_num - 1)
            _divider(sp, pg_num)

    total = len(out)
    out.save(output_file, deflate=True, garbage=4)
    out.close()
    src.close()
    print(f"    输出: {output_file} ({total} 页)")


def _place_src(spread, src_doc, idx):
    r = src_doc[idx].rect
    sx, sy = PAGE_W / r.width, PAGE_H / r.height
    s = min(sx, sy)
    sw, sh = r.width * s, r.height * s
    ox, oy = (PAGE_W - sw) / 2, (PAGE_H - sh) / 2
    spread.show_pdf_page(fitz.Rect(ox, oy, ox + sw, oy + sh), src_doc, idx)


def _divider(spread, pg):
    spread.draw_line((PAGE_W, 0), (PAGE_W, PAGE_H),
                     color=(0.8, 0.8, 0.8), width=0.8)
    tw = fitz.TextWriter(spread.rect)
    f = fitz.Font("helv")
    tw.append((PAGE_W - 20, PAGE_H - 12), str(pg), font=f, fontsize=7)
    tw.write_text(spread, color=(0.5, 0.5, 0.5))


PAPER_MAP = {}  # 不再硬编码，自动发现


# ---------- 精炼版（单页）----------

def generate_summary_pdf(workspace, paper_name):
    """将 *_annotated.md 渲染为单页 PDF"""
    md_path = os.path.join(workspace, f"{paper_name}_annotated.md")
    if not os.path.exists(md_path):
        print(f"  跳过精炼版 {paper_name}: 无 annotated.md")
        return

    output_dir = os.path.join(workspace, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{paper_name}_summary.pdf")

    print(f"  精炼版: {paper_name}")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    html_body = md_to_html(md_text)
    full_html = HTML_TEMPLATE.replace("%%CONTENT%%", html_body)
    render_html_to_pdf(full_html, output_file)
    print(f"    输出: {output_file}")


def discover_papers(workspace):
    """扫描 papers/ 目录，返回 paper_name 列表"""
    papers_dir = os.path.join(workspace, "papers")
    if not os.path.isdir(papers_dir):
        return []
    return sorted(f[:-4] for f in os.listdir(papers_dir) if f.endswith('.pdf'))


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_pdf.py <workspace> "
              "[dual|summary|all] [paper_name]")
        sys.exit(1)

    workspace = os.path.abspath(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    only = sys.argv[3] if len(sys.argv) > 3 else None
    papers = [only] if only else discover_papers(workspace)

    if mode in ("all", "dual"):
        print("=" * 60)
        print("生成逐行翻译双页 PDF")
        print("=" * 60)
        for name in papers:
            pdf_path = os.path.join(workspace, "papers", f"{name}.pdf")
            trans = os.path.join(workspace, "translations", f"{name}_p*.md")
            if not os.path.exists(pdf_path) or not glob.glob(trans):
                print(f"  跳过 {name}: 无 PDF 或翻译文件")
                continue
            try:
                generate_aligned_pdf(workspace, name)
            except Exception as e:
                import traceback
                print(f"  错误: {name} -> {e}")
                traceback.print_exc()

    if mode in ("all", "summary"):
        print("=" * 60)
        print("生成精炼版 PDF")
        print("=" * 60)
        for name in papers:
            try:
                generate_summary_pdf(workspace, name)
            except Exception as e:
                import traceback
                print(f"  错误: {name} -> {e}")
                traceback.print_exc()

    close_browser()
    print("\n完成！输出:", os.path.join(workspace, "output"))


if __name__ == "__main__":
    main()