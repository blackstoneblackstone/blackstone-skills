#!/bin/bash
# IU Comment Scraper - 运行脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "IU Comment Scraper"
echo "======================================"
echo ""

# 运行爬虫
python3 "$SCRIPT_DIR/scrape_iu_comments.py"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "运行完成！"
    echo "======================================"
else
    echo ""
    echo "======================================"
    echo "运行失败 (退出码：$exit_code)"
    echo "======================================"
fi

exit $exit_code
