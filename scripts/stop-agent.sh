#!/bin/bash
# Reprospective host-agent 停止スクリプト
# 実行中のhost-agentコレクターを停止する

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOST_AGENT_DIR="$PROJECT_ROOT/host-agent"

# PIDファイルディレクトリ
PID_DIR="$HOST_AGENT_DIR/.pids"

# 使用方法
usage() {
    echo "使い方: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --all              すべてのエージェントを停止 (デフォルト)"
    echo "  --desktop          デスクトップモニターのみ停止"
    echo "  --files            ファイルシステムウォッチャーのみ停止"
    echo "  --input            入力モニターのみ停止"
    echo "  -h, --help         このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                 # すべて停止"
    echo "  $0 --desktop       # デスクトップモニターのみ"
    echo "  $0 --files         # ファイルウォッチャーのみ"
    echo "  $0 --input         # 入力モニターのみ"
    exit 1
}

# エージェントが実行中かチェック
is_running() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # 実行中
        else
            # PIDファイルは存在するがプロセスは存在しない
            rm -f "$pid_file"
            return 1  # 実行中でない
        fi
    fi
    return 1  # 実行中でない
}

# エージェントを停止
stop_agent() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"

    if ! is_running "$name"; then
        echo "  ℹ️  $name は実行されていません"
        return
    fi

    local pid=$(cat "$pid_file")
    echo "  🛑 $name を停止中 (PID: $pid)..."

    # SIGTERMを送信
    kill "$pid" 2>/dev/null || true

    # プロセスが終了するまで待機（最大10秒）
    local count=0
    while ps -p "$pid" > /dev/null 2>&1; do
        sleep 0.5
        count=$((count + 1))
        if [ $count -ge 20 ]; then
            # タイムアウト: 強制終了
            echo "     ⚠️  正常終了しなかったため強制終了します..."
            kill -9 "$pid" 2>/dev/null || true
            break
        fi
    done

    # PIDファイルを削除
    rm -f "$pid_file"

    # 終了確認
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "     ❌ 停止に失敗しました"
        return 1
    else
        echo "     ✅ 停止完了"
    fi
}

# オプション解析
STOP_ALL=true
STOP_DESKTOP=false
STOP_FILES=false
STOP_INPUT=false

if [ $# -eq 0 ]; then
    STOP_ALL=true
else
    STOP_ALL=false
    while [ $# -gt 0 ]; do
        case "$1" in
            --all)
                STOP_ALL=true
                ;;
            --desktop)
                STOP_DESKTOP=true
                ;;
            --files)
                STOP_FILES=true
                ;;
            --input)
                STOP_INPUT=true
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo "❌ 不明なオプション: $1"
                usage
                ;;
        esac
        shift
    done
fi

# allオプションの場合はすべて有効化
if [ "$STOP_ALL" = true ]; then
    STOP_DESKTOP=true
    STOP_FILES=true
    STOP_INPUT=true
fi

echo "================================"
echo "host-agent 停止"
echo "================================"
echo ""

# PIDディレクトリが存在しない場合
if [ ! -d "$PID_DIR" ]; then
    echo "ℹ️  実行中のエージェントはありません"
    exit 0
fi

# エージェントを停止
STOPPED_COUNT=0

if [ "$STOP_DESKTOP" = true ]; then
    if stop_agent "desktop-monitor"; then
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
fi

if [ "$STOP_FILES" = true ]; then
    if stop_agent "filesystem-watcher"; then
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
fi

if [ "$STOP_INPUT" = true ]; then
    if stop_agent "input-monitor"; then
        STOPPED_COUNT=$((STOPPED_COUNT + 1))
    fi
fi

echo ""
echo "================================"
echo "✅ 停止完了 ($STOPPED_COUNT エージェント)"
echo "================================"
echo ""

# 残存エージェントの確認
REMAINING=false
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        name=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            if [ "$REMAINING" = false ]; then
                echo "📊 実行中のエージェント:"
                REMAINING=true
            fi
            echo "  ✓ $name (PID: $pid)"
        fi
    fi
done

if [ "$REMAINING" = false ]; then
    echo "ℹ️  実行中のエージェントはありません"
fi

echo ""
echo "💡 エージェントを再起動する場合:"
echo "   ./scripts/start-agent.sh"
echo ""
