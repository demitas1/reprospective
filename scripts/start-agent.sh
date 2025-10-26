#!/bin/bash
# Reprospective host-agent 起動スクリプト
# host-agentのコレクターをバックグラウンドで起動する

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOST_AGENT_DIR="$PROJECT_ROOT/host-agent"

# PIDファイルディレクトリ
PID_DIR="$HOST_AGENT_DIR/.pids"
mkdir -p "$PID_DIR"

# ログディレクトリ
LOG_DIR="$HOST_AGENT_DIR/logs"
mkdir -p "$LOG_DIR"

# 使用方法
usage() {
    echo "使い方: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  --all              すべてのエージェントを起動 (デフォルト)"
    echo "  --desktop          デスクトップモニターのみ起動"
    echo "  --files            ファイルシステムウォッチャーのみ起動"
    echo "  -h, --help         このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                 # すべて起動"
    echo "  $0 --desktop       # デスクトップモニターのみ"
    echo "  $0 --files         # ファイルウォッチャーのみ"
    exit 1
}

# エージェントが既に実行中かチェック
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

# エージェントを起動
start_agent() {
    local name=$1
    local script=$2
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"

    if is_running "$name"; then
        echo "  ⚠️  $name は既に実行中です (PID: $(cat $pid_file))"
        return
    fi

    echo "  🚀 $name を起動中..."

    # 仮想環境の確認
    if [ ! -d "$HOST_AGENT_DIR/venv" ]; then
        echo "     ❌ 仮想環境が見つかりません"
        echo "     💡 先に仮想環境をセットアップしてください:"
        echo "        cd host-agent && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        return 1
    fi

    # バックグラウンドで起動
    cd "$HOST_AGENT_DIR"
    nohup ./venv/bin/python "$script" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"

    # 起動確認（少し待つ）
    sleep 1
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "     ✅ 起動完了 (PID: $pid)"
        echo "     📝 ログ: $log_file"
    else
        echo "     ❌ 起動に失敗しました"
        echo "     📝 ログを確認: $log_file"
        rm -f "$pid_file"
        return 1
    fi
}

# オプション解析
START_ALL=true
START_DESKTOP=false
START_FILES=false

if [ $# -eq 0 ]; then
    START_ALL=true
else
    START_ALL=false
    while [ $# -gt 0 ]; do
        case "$1" in
            --all)
                START_ALL=true
                ;;
            --desktop)
                START_DESKTOP=true
                ;;
            --files)
                START_FILES=true
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
if [ "$START_ALL" = true ]; then
    START_DESKTOP=true
    START_FILES=true
fi

echo "================================"
echo "host-agent 起動"
echo "================================"
echo ""

# 設定ファイルの確認
if [ ! -f "$HOST_AGENT_DIR/config/config.yaml" ]; then
    echo "⚠️  設定ファイルが見つかりません"
    echo "💡 config.example.yaml をコピーして config.yaml を作成してください:"
    echo "   cd host-agent/config && cp config.example.yaml config.yaml"
    exit 1
fi

# エージェントを起動
STARTED_COUNT=0

if [ "$START_DESKTOP" = true ]; then
    if start_agent "desktop-monitor" "collectors/linux_x11_monitor.py"; then
        STARTED_COUNT=$((STARTED_COUNT + 1))
    fi
fi

if [ "$START_FILES" = true ]; then
    if start_agent "filesystem-watcher" "collectors/filesystem_watcher.py"; then
        STARTED_COUNT=$((STARTED_COUNT + 1))
    fi
fi

echo ""
echo "================================"
echo "✅ 起動完了 ($STARTED_COUNT エージェント)"
echo "================================"
echo ""
echo "📊 実行中のエージェント:"
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        name=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  ✓ $name (PID: $pid)"
        fi
    fi
done

echo ""
echo "💡 便利なコマンド:"
echo "   ./scripts/stop-agent.sh                # すべて停止"
echo "   ./scripts/stop-agent.sh --desktop      # デスクトップモニターのみ停止"
echo "   tail -f $LOG_DIR/desktop-monitor.log   # ログ確認"
echo "   cd host-agent && python scripts/show_sessions.py      # データ確認"
echo ""
