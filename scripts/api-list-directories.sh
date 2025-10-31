#!/bin/bash
set -e

# ディレクトリ一覧取得スクリプト
# 使い方:
#   ./scripts/api-list-directories.sh           # 全ディレクトリ取得
#   ./scripts/api-list-directories.sh --enabled  # 有効なディレクトリのみ

# 設定
API_URL="${API_GATEWAY_URL:-http://localhost:8800}"

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================"
echo "監視対象ディレクトリ一覧取得"
echo "================================"
echo ""

# オプション解析
ENABLED_ONLY=false
if [[ "$1" == "--enabled" ]]; then
    ENABLED_ONLY=true
fi

# API呼び出し
if $ENABLED_ONLY; then
    echo -e "${BLUE}📋 有効なディレクトリのみ取得中...${NC}"
    URL="${API_URL}/api/v1/directories/?enabled_only=true"
else
    echo -e "${BLUE}📋 全ディレクトリ取得中...${NC}"
    URL="${API_URL}/api/v1/directories/"
fi

echo ""

# curlでAPI呼び出し（整形して表示）
if command -v jq &> /dev/null; then
    # jqがある場合は整形表示
    RESPONSE=$(curl -s "$URL")

    # レスポンスが空配列かチェック
    if [[ "$RESPONSE" == "[]" ]]; then
        echo -e "${GREEN}✅ データなし（空のリスト）${NC}"
        exit 0
    fi

    # 整形表示
    echo "$RESPONSE" | jq -r '.[] | "
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: \(.id)
パス: \(.directory_path)
状態: \(if .enabled then "✅ 有効" else "⏸️  無効" end)
表示名: \(.display_name // "（未設定）")
説明: \(.description // "（未設定）")
作成日時: \(.created_at)
更新日時: \(.updated_at)
"'

    # 件数表示
    COUNT=$(echo "$RESPONSE" | jq 'length')
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}✅ 取得完了: ${COUNT}件${NC}"
else
    # jqがない場合は生JSON表示
    curl -s "$URL" | python3 -m json.tool
    echo ""
    echo -e "${GREEN}✅ 取得完了${NC}"
fi

echo ""
echo "💡 ヒント:"
echo "  - 有効なディレクトリのみ: ./scripts/api-list-directories.sh --enabled"
echo "  - 全ディレクトリ: ./scripts/api-list-directories.sh"
