#!/bin/bash
set -e

# ディレクトリ情報更新スクリプト
# 使い方:
#   ./scripts/api-update-directory.sh <ID> [--path <新パス>] [--name <表示名>] [--desc <説明>] [--enable|--disable]

# 設定
API_URL="${API_GATEWAY_URL:-http://localhost:8800}"

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "監視対象ディレクトリ情報更新"
echo "================================"
echo ""

# 引数チェック
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ エラー: ディレクトリIDと更新項目を指定してください${NC}"
    echo ""
    echo "使い方:"
    echo "  $0 <ディレクトリID> [オプション]"
    echo ""
    echo "オプション:"
    echo "  --path <新パス>       ディレクトリパスを変更"
    echo "  --name <表示名>       表示名を変更"
    echo "  --desc <説明>         説明を変更"
    echo "  --enable              有効化"
    echo "  --disable             無効化"
    echo ""
    echo "例:"
    echo "  $0 1 --name \"新しい名前\""
    echo "  $0 1 --desc \"新しい説明\""
    echo "  $0 1 --name \"プロジェクト\" --desc \"開発用ディレクトリ\""
    echo "  $0 1 --path /home/user/new_path"
    echo "  $0 1 --disable"
    echo ""
    echo "💡 ID確認: ./scripts/api-list-directories.sh"
    exit 1
fi

DIRECTORY_ID="$1"
shift

# 数値チェック
if ! [[ "$DIRECTORY_ID" =~ ^[0-9]+$ ]]; then
    echo -e "${RED}❌ エラー: IDは数値で指定してください${NC}"
    exit 1
fi

# オプション解析
NEW_PATH=""
NEW_NAME=""
NEW_DESC=""
NEW_ENABLED=""
HAS_UPDATE=false

while [ $# -gt 0 ]; do
    case "$1" in
        --path)
            NEW_PATH="$2"
            HAS_UPDATE=true
            shift 2
            ;;
        --name)
            NEW_NAME="$2"
            HAS_UPDATE=true
            shift 2
            ;;
        --desc)
            NEW_DESC="$2"
            HAS_UPDATE=true
            shift 2
            ;;
        --enable)
            NEW_ENABLED="true"
            HAS_UPDATE=true
            shift
            ;;
        --disable)
            NEW_ENABLED="false"
            HAS_UPDATE=true
            shift
            ;;
        *)
            echo -e "${RED}❌ エラー: 不明なオプション: $1${NC}"
            exit 1
            ;;
    esac
done

if ! $HAS_UPDATE; then
    echo -e "${RED}❌ エラー: 更新項目が指定されていません${NC}"
    exit 1
fi

# 更新前の情報取得
echo -e "${BLUE}📋 現在の情報を取得中...${NC}"
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
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "【現在の情報】"

if command -v jq &> /dev/null; then
    echo "$INFO_BODY" | jq -r '"  パス: \(.directory_path)
  状態: \(if .enabled then "有効" else "無効" end)
  表示名: \(.display_name // "（未設定）")
  説明: \(.description // "（未設定）")"'
else
    echo "$INFO_BODY" | python3 -m json.tool
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# JSON作成（部分更新対応）
JSON_PARTS=()

if [ -n "$NEW_PATH" ]; then
    # 絶対パスチェック
    if [[ ! "$NEW_PATH" =~ ^/ ]]; then
        echo -e "${YELLOW}⚠️  警告: 相対パスが指定されています。絶対パスに変換します。${NC}"
        NEW_PATH="$(cd "$(dirname "$NEW_PATH")" && pwd)/$(basename "$NEW_PATH")"
        echo "   変換後: $NEW_PATH"
        echo ""
    fi
    JSON_PARTS+=("\"directory_path\": \"$NEW_PATH\"")
fi

if [ -n "$NEW_NAME" ]; then
    JSON_PARTS+=("\"display_name\": \"$NEW_NAME\"")
fi

if [ -n "$NEW_DESC" ]; then
    JSON_PARTS+=("\"description\": \"$NEW_DESC\"")
fi

if [ -n "$NEW_ENABLED" ]; then
    JSON_PARTS+=("\"enabled\": $NEW_ENABLED")
fi

# JSON組み立て
IFS=","
JSON_DATA="{${JSON_PARTS[*]}}"
unset IFS

echo -e "${BLUE}📝 更新内容:${NC}"
if [ -n "$NEW_PATH" ]; then echo "  新しいパス: $NEW_PATH"; fi
if [ -n "$NEW_NAME" ]; then echo "  新しい表示名: $NEW_NAME"; fi
if [ -n "$NEW_DESC" ]; then echo "  新しい説明: $NEW_DESC"; fi
if [ -n "$NEW_ENABLED" ]; then
    if [ "$NEW_ENABLED" = "true" ]; then
        echo "  状態: 有効化"
    else
        echo "  状態: 無効化"
    fi
fi
echo ""

echo -e "${BLUE}🚀 API呼び出し中...${NC}"

# API呼び出し
RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${API_URL}/api/v1/directories/${DIRECTORY_ID}" \
  -H "Content-Type: application/json" \
  -d "$JSON_DATA")

# HTTPステータスコードを取得
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo ""

# レスポンス処理
if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✅ 更新成功！${NC}"
    echo ""

    if command -v jq &> /dev/null; then
        # 更新後の情報を表示
        echo "$BODY" | jq -r '"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID: \(.id)
パス: \(.directory_path)
状態: \(if .enabled then "✅ 有効" else "⏸️  無効" end)
表示名: \(.display_name // "（未設定）")
説明: \(.description // "（未設定）")
更新日時: \(.updated_at)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"'
    else
        echo "$BODY" | python3 -m json.tool
    fi

    echo ""
    echo "💡 次のステップ:"
    echo "  - 一覧確認: ./scripts/api-list-directories.sh"
elif [ "$HTTP_CODE" -eq 404 ]; then
    echo -e "${RED}❌ エラー: ID $DIRECTORY_ID のディレクトリが見つかりません${NC}"
    echo ""
    echo "💡 ヒント: ./scripts/api-list-directories.sh で存在するIDを確認してください"
elif [ "$HTTP_CODE" -eq 409 ]; then
    echo -e "${RED}❌ エラー: 指定されたパスは既に登録されています${NC}"
    echo ""
    if command -v jq &> /dev/null && echo "$BODY" | jq -e '.detail' > /dev/null 2>&1; then
        echo "詳細: $(echo "$BODY" | jq -r '.detail')"
    else
        echo "$BODY"
    fi
else
    echo -e "${RED}❌ エラー: 更新に失敗しました (HTTP $HTTP_CODE)${NC}"
    echo ""
    if command -v jq &> /dev/null && echo "$BODY" | jq -e '.detail' > /dev/null 2>&1; then
        echo "詳細: $(echo "$BODY" | jq -r '.detail')"
    else
        echo "$BODY"
    fi
fi
