#!/bin/bash
# IU Comment Scraper - 安装依赖脚本

echo "======================================"
echo "IU Comment Scraper - 安装依赖"
echo "======================================"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 未安装，请先安装 Python3"
    exit 1
fi
echo "✓ Python3 已安装：$(python3 --version)"

# 检查 pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "✗ pip 未安装"
    exit 1
fi

PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# 安装依赖
echo ""
echo "正在安装 Python 依赖..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
$PIP_CMD install -r "$SCRIPT_DIR/requirements.txt" --user -q

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装完成"
else
    echo "✗ 依赖安装失败"
    exit 1
fi

echo ""
echo "======================================"
echo "安装完成！"
echo "======================================"
echo ""
echo "使用方法:"
echo "  python3 $SCRIPT_DIR/scrape_iu_comments.py"
echo ""
