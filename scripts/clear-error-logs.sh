#!/bin/bash
# フロントエンドエラーログ消去スクリプト
#
# 使用方法:
#   ./scripts/clear-error-logs.sh        # 確認プロンプトあり
#   ./scripts/clear-error-logs.sh -f     # 強制実行（確認なし）

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログファイルパス
LOG_FILE="./logs/errors.log"

# 強制実行フラグ
FORCE=false
if [ "$1" = "-f" ] || [ "$1" = "--force" ]; then
    FORCE=true
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}フロントエンドエラーログ消去${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ログファイルの存在確認
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠ ログファイルが存在しません: $LOG_FILE${NC}"
    echo ""
    echo "消去する必要はありません。"
    echo ""
    exit 0
fi

# ログファイルが空の場合
if [ ! -s "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠ ログファイルは存在しますが、既に空です${NC}"
    echo ""
    echo "消去する必要はありません。"
    echo ""
    exit 0
fi

# エラーログの総件数を表示
TOTAL_COUNT=$(wc -l < "$LOG_FILE")
echo -e "${YELLOW}現在のエラー件数: $TOTAL_COUNT 件${NC}"
echo ""

# 最新5件のエラーメッセージを表示（プレビュー）
echo -e "${BLUE}最新5件のプレビュー:${NC}"
if command -v jq &> /dev/null; then
    tail -n 5 "$LOG_FILE" | jq -r '.message' | nl
else
    tail -n 5 "$LOG_FILE" | nl
fi
echo ""

# 確認プロンプト（強制実行でない場合）
if [ "$FORCE" = false ]; then
    echo -e "${RED}警告: この操作は元に戻せません！${NC}"
    echo -e "${YELLOW}すべてのエラーログを削除しますか？ (yes/no)${NC}"
    read -r response

    if [ "$response" != "yes" ]; then
        echo ""
        echo -e "${GREEN}キャンセルしました。${NC}"
        echo ""
        exit 0
    fi
fi

# ログファイルをクリア
> "$LOG_FILE"

echo ""
echo -e "${GREEN}✅ エラーログを消去しました${NC}"
echo ""
echo "ログファイル: $LOG_FILE"
echo "削除件数: $TOTAL_COUNT 件"
echo ""

# 確認
if [ -s "$LOG_FILE" ]; then
    echo -e "${RED}⚠ エラー: ログファイルのクリアに失敗しました${NC}"
    exit 1
else
    echo -e "${GREEN}ログファイルは空になりました。${NC}"
    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo ""
echo "使用方法:"
echo "  ./scripts/clear-error-logs.sh       # 確認プロンプトあり"
echo "  ./scripts/clear-error-logs.sh -f    # 強制実行（確認なし）"
echo ""
echo "その他のコマンド:"
echo "  ./scripts/show-error-logs.sh        # エラーログを表示"
echo ""
