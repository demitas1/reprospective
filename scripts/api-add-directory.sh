#!/bin/bash
set -e

# ディレクトリ追加スクリプト
# 使い方:
#   ./scripts/api-add-directory.sh /path/to/directory "表示名" "説明"
#   ./scripts/api-add-directory.sh /path/to/directory "表示名"
#   ./scripts/api-add-directory.sh /path/to/directory

# 設定
API_URL="${API_GATEWAY_URL:-http://localhost:8800}"

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "監視対象ディレクトリ追加"
echo "================================"
echo ""

# 引数チェック
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ エラー: ディレクトリパスを指定してください${NC}"
    echo ""
    echo "使い方:"
    echo "  $0 <ディレクトリパス> [表示名] [説明]"
    echo ""
    echo "例:"
    echo "  $0 /home/user/projects \"プロジェクト\" \"開発用ディレクトリ\""
    echo "  $0 /home/user/Documents \"ドキュメント\""
    echo "  $0 /home/user/work"
    exit 1
fi

DIRECTORY_PATH="$1"
DISPLAY_NAME="${2:-}"
DESCRIPTION="${3:-}"

# ディレクトリパスが絶対パスかチェック
if [[ ! "$DIRECTORY_PATH" =~ ^/ ]]; then
    echo -e "${YELLOW}⚠️  警告: 相対パスが指定されています。絶対パスに変換します。${NC}"
    DIRECTORY_PATH="$(cd "$(dirname "$DIRECTORY_PATH")" && pwd)/$(basename "$DIRECTORY_PATH")"
    echo "   変換後: $DIRECTORY_PATH"
    echo ""
fi

echo -e "${BLUE}📝 追加情報:${NC}"
echo "  パス: $DIRECTORY_PATH"
echo "  表示名: ${DISPLAY_NAME:-（未設定）}"
echo "  説明: ${DESCRIPTION:-（未設定）}"
echo "  状態: 有効"
echo ""

# JSON作成
JSON_DATA=$(cat <<EOF
{
  "directory_path": "$DIRECTORY_PATH",
  "enabled": true,
  "display_name": $(if [ -n "$DISPLAY_NAME" ]; then echo "\"$DISPLAY_NAME\""; else echo "null"; fi),
  "description": $(if [ -n "$DESCRIPTION" ]; then echo "\"$DESCRIPTION\""; else echo "null"; fi)
}
EOF
)

# API呼び出し
echo -e "${BLUE}🚀 API呼び出し中...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/directories/" \
  -H "Content-Type: application/json" \
  -d "$JSON_DATA")

# HTTPステータスコードを取得
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""

# レスポンス処理
if [ "$HTTP_CODE" -eq 201 ]; then
    echo -e "${GREEN}✅ ディレクトリ追加成功！${NC}"
    echo ""

    if command -v jq &> /dev/null; then
        # jqで整形表示
        echo "$BODY" | jq -r '"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: \(.id)
パス: \(.directory_path)
状態: \(if .enabled then "✅ 有効" else "⏸️  無効" end)
表示名: \(.display_name // "（未設定）")
説明: \(.description // "（未設定）")
作成日時: \(.created_at)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"'
    else
        echo "$BODY" | python3 -m json.tool
    fi

    echo ""
    echo "💡 次のステップ:"
    echo "  - 一覧確認: ./scripts/api-list-directories.sh"
    echo "  - 無効化: ./scripts/api-toggle-directory.sh <ID>"
elif [ "$HTTP_CODE" -eq 409 ]; then
    echo -e "${RED}❌ エラー: このディレクトリは既に登録されています${NC}"
    echo ""
    if command -v jq &> /dev/null && echo "$BODY" | jq -e '.detail' > /dev/null 2>&1; then
        echo "詳細: $(echo "$BODY" | jq -r '.detail')"
    else
        echo "$BODY"
    fi
else
    echo -e "${RED}❌ エラー: ディレクトリの追加に失敗しました (HTTP $HTTP_CODE)${NC}"
    echo ""
    if command -v jq &> /dev/null && echo "$BODY" | jq -e '.detail' > /dev/null 2>&1; then
        echo "詳細: $(echo "$BODY" | jq -r '.detail')"
    else
        echo "$BODY"
    fi
fi
