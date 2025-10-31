#!/bin/bash
set -e

# ディレクトリ有効/無効切り替えスクリプト
# 使い方:
#   ./scripts/api-toggle-directory.sh <ID>

# 設定
API_URL="${API_GATEWAY_URL:-http://localhost:8800}"

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "監視対象ディレクトリ 有効/無効切り替え"
echo "================================"
echo ""

# 引数チェック
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ エラー: ディレクトリIDを指定してください${NC}"
    echo ""
    echo "使い方:"
    echo "  $0 <ディレクトリID>"
    echo ""
    echo "例:"
    echo "  $0 1"
    echo ""
    echo "💡 ID確認: ./scripts/api-list-directories.sh"
    exit 1
fi

DIRECTORY_ID="$1"

# 数値チェック
if ! [[ "$DIRECTORY_ID" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}❌ エラー: IDは数値で指定してください${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 ディレクトリID: $DIRECTORY_ID を切り替え中...${NC}"
echo ""

# API呼び出し
RESPONSE=$(curl -s -w "\n%{http_code}" -X PATCH "${API_URL}/api/v1/directories/${DIRECTORY_ID}/toggle")

# HTTPステータスコードを取得
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

# レスポンス処理
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ 切り替え成功！${NC}"
    echo ""

    if command -v jq &> /dev/null; then
        # 現在の状態を取得
        ENABLED=$(echo "$BODY" | jq -r '.enabled')

        if [ "$ENABLED" = "true" ]; then
            STATUS_TEXT="✅ 有効"
            STATUS_MSG="ディレクトリが有効化されました。監視が開始されます。"
        else
            STATUS_TEXT="⏸️  無効"
            STATUS_MSG="ディレクトリが無効化されました。監視が停止されます。"
        fi

        # 詳細表示
        echo "$BODY" | jq -r '"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: \(.id)
パス: \(.directory_path)
状態: '"$STATUS_TEXT"'
表示名: \(.display_name // "（未設定）")
説明: \(.description // "（未設定）")
更新日時: \(.updated_at)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"'
        echo ""
        echo -e "${YELLOW}${STATUS_MSG}${NC}"
    else
        echo "$BODY" | python3 -m json.tool
    fi

    echo ""
    echo "💡 次のステップ:"
    echo "  - 一覧確認: ./scripts/api-list-directories.sh"
    echo "  - 再度切り替え: ./scripts/api-toggle-directory.sh $DIRECTORY_ID"
elif [ "$HTTP_CODE" -eq 404 ]; then
    echo -e "${RED}❌ エラー: ID $DIRECTORY_ID のディレクトリが見つかりません${NC}"
    echo ""
    echo "💡 ヒント: ./scripts/api-list-directories.sh で存在するIDを確認してください"
else
    echo -e "${RED}❌ エラー: 切り替えに失敗しました (HTTP $HTTP_CODE)${NC}"
    echo ""
    if command -v jq &> /dev/null && echo "$BODY" | jq -e '.detail' > /dev/null 2>&1; then
        echo "詳細: $(echo "$BODY" | jq -r '.detail')"
    else
        echo "$BODY"
    fi
fi
