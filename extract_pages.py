#!/usr/bin/env python3
"""
逐页提取 PDF 文本，保存为 JSON，供翻译 agent 使用。

用法:
  python3 extract_pages.py <workspace_dir>
  # workspace_dir 下需有 papers/ 目录，输出到 extracted/

  python3 extract_pages.py <workspace_dir> <paper_name>
  # 只提取指定论文，如 cosmos_policy
"""
import fitz
import json
import os
import sys
import glob


def extract(workspace, paper_name=None):
    papers_dir = os.path.join(workspace, "papers")
    extract_dir = os.path.join(workspace, "extracted")
    os.makedirs(extract_dir, exist_ok=True)

    if paper_name:
        pdfs = [os.path.join(papers_dir, f"{paper_name}.pdf")]
    else:
        pdfs = sorted(glob.glob(os.path.join(papers_dir, "*.pdf")))

    for pdf_path in pdfs:
        if not os.path.exists(pdf_path):
            print(f"  跳过: {pdf_path} 不存在")
            continue
        doc = fitz.open(pdf_path)
        pages = []
        for i in range(len(doc)):
            pages.append({"page": i + 1, "text": doc[i].get_text()})
        doc.close()

        base = os.path.splitext(os.path.basename(pdf_path))[0]
        out_path = os.path.join(extract_dir, f"{base}_pages.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        print(f"  {base}: {len(pages)} 页 → {out_path}")


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    name = sys.argv[2] if len(sys.argv) > 2 else None
    print("提取 PDF 文本...")
    extract(ws, name)
    print("完成")
