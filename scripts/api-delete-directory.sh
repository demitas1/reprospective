#!/bin/bash
set -e

# ディレクトリ削除スクリプト
# 使い方:
#   ./scripts/api-delete-directory.sh <ID>

# 設定
API_URL="${API_GATEWAY_URL:-http://localhost:8800}"

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "監視対象ディレクトリ削除"
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

# 削除前に情報取得
echo -e "${BLUE}📋 削除対象ディレクトリ情報を取得中...${NC}"
INFO_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/api/v1/directories/${DIRECTORY_ID}")
INFO_HTTP_CODE=$(echo "$INFO_RESPONSE" | tail -n1)
INFO_BODY=$(echo "$INFO_RESPONSE" | sed '$d')

if [ "$INFO_HTTP_CODE" -ne 200 ]; then
    echo -e "${RED}❌ エラー: ID $DIRECTORY_ID のディレクトリが見つかりません${NC}"
    echo ""
    echo "💡 ヒント: ./scripts/api-list-directories.sh で存在するIDを確認してください"
    exit 1
fi

echo ""

# 削除対象の詳細を表示
if command -v jq &> /dev/null; then
    echo "$INFO_BODY" | jq -r '"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: \(.id)
パス: \(.directory_path)
状態: \(if .enabled then "✅ 有効" else "⏸️  無効" end)
表示名: \(.display_name // "（未設定）")
説明: \(.description // "（未設定）")
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"'
else
    echo "$INFO_BODY" | python3 -m json.tool
fi

echo ""
echo -e "${YELLOW}⚠️  このディレクトリを削除しますか？${NC}"
echo -e "${YELLOW}   この操作は取り消せません。${NC}"
echo ""
read -p "削除を実行する場合は 'yes' と入力してください: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo -e "${BLUE}ℹ️  削除をキャンセルしました${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🗑️  削除中...${NC}"

# API呼び出し
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null -X DELETE "${API_URL}/api/v1/directories/${DIRECTORY_ID}")

echo ""

# レスポンス処理
if [ "$HTTP_CODE" -eq 204 ]; then
    echo -e "${GREEN}✅ ディレクトリ削除成功！${NC}"
    echo ""
    echo "ID $DIRECTORY_ID のディレクトリが削除されました。"
    echo ""
    echo "💡 次のステップ:"
    echo "  - 一覧確認: ./scripts/api-list-directories.sh"
elif [ "$HTTP_CODE" -eq 404 ]; then
    echo -e "${RED}❌ エラー: ID $DIRECTORY_ID のディレクトリが見つかりません${NC}"
    echo ""
    echo "💡 ヒント: 既に削除されている可能性があります"
else
    echo -e "${RED}❌ エラー: 削除に失敗しました (HTTP $HTTP_CODE)${NC}"
fi
