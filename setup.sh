#!/bin/bash
# 论文分析工具链 - 一键安装依赖
set -e

echo "=== 安装 Python 依赖 ==="
pip3 install PyMuPDF markdown playwright --break-system-packages 2>/dev/null \
  || pip3 install PyMuPDF markdown playwright

echo "=== 安装 Chromium (Playwright) ==="
python3 -m playwright install chromium

echo "=== 验证 ==="
python3 -c "
import fitz; print(f'PyMuPDF {fitz.version[0]}')
import markdown; print(f'markdown {markdown.__version__}')
from playwright.sync_api import sync_playwright; print('playwright OK')
"

echo "=== 安装完成 ==="
