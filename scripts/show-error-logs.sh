#!/bin/bash
# フロントエンドエラーログ表示スクリプト
#
# 使用方法:
#   ./scripts/show-error-logs.sh [件数]
#
# 例:
#   ./scripts/show-error-logs.sh       # 最新10件を表示
#   ./scripts/show-error-logs.sh 20    # 最新20件を表示
#   ./scripts/show-error-logs.sh all   # 全件を表示

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログファイルパス
LOG_FILE="./logs/errors.log"

# 表示件数（デフォルト: 10件）
LIMIT=${1:-10}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}フロントエンドエラーログ表示${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ログファイルの存在確認
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠ ログファイルが存在しません: $LOG_FILE${NC}"
    echo ""
    echo "エラーログを生成するには:"
    echo "  1. docker compose up -d でサービスを起動"
    echo "  2. http://localhost:3333/?test=error-logger にアクセス"
    echo "  3. テストボタンをクリックしてエラーを発生させる"
    echo ""
    exit 0
fi

# ログファイルが空の場合
if [ ! -s "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠ ログファイルは存在しますが、エントリがありません${NC}"
    echo ""
    echo "エラーログを生成するには:"
    echo "  1. http://localhost:3333/?test=error-logger にアクセス"
    echo "  2. テストボタンをクリックしてエラーを発生させる"
    echo ""
    exit 0
fi

# エラーログの総件数を表示
TOTAL_COUNT=$(wc -l < "$LOG_FILE")
echo -e "${GREEN}総エラー件数: $TOTAL_COUNT 件${NC}"
echo ""

# 表示モードの判定
if [ "$LIMIT" = "all" ]; then
    echo -e "${BLUE}全エラーログを表示:${NC}"
    echo ""

    # jqがインストールされている場合は整形表示
    if command -v jq &> /dev/null; then
        cat "$LOG_FILE" | while IFS= read -r line; do
            echo "$line" | jq -C '.'
            echo ""
        done
    else
        cat "$LOG_FILE"
    fi
else
    echo -e "${BLUE}最新 $LIMIT 件のエラーログを表示:${NC}"
    echo ""

    # jqがインストールされている場合は整形表示
    if command -v jq &> /dev/null; then
        tail -n "$LIMIT" "$LOG_FILE" | while IFS= read -r line; do
            echo "$line" | jq -C '.'
            echo ""
        done
    else
        tail -n "$LIMIT" "$LOG_FILE"
    fi
fi

echo -e "${BLUE}========================================${NC}"
echo ""
echo "使用方法:"
echo "  ./scripts/show-error-logs.sh       # 最新10件を表示"
echo "  ./scripts/show-error-logs.sh 20    # 最新20件を表示"
echo "  ./scripts/show-error-logs.sh all   # 全件を表示"
echo ""
echo "その他のコマンド:"
echo "  ./scripts/clear-error-logs.sh      # エラーログを全消去"
echo "  tail -f $LOG_FILE | jq '.'         # リアルタイム監視"
echo ""
