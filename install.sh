#!/usr/bin/env bash
# 手动安装 sanyi-manhua-review（macOS / Linux）
# 用法：bash install.sh [all|claude|agents]
set -euo pipefail
NAME="sanyi-manhua-review"
SRC="$(cd "$(dirname "$0")" && pwd)/skills/$NAME"
TARGET="${1:-all}"
install_to () { mkdir -p "$1"; rm -rf "$1/$NAME"; cp -R "$SRC" "$1/$NAME"; echo "✓ 已安装到 $1/$NAME"; }
[[ "$TARGET" == "all" || "$TARGET" == "claude" ]] && install_to "$HOME/.claude/skills"
[[ "$TARGET" == "all" || "$TARGET" == "agents" ]] && install_to "$HOME/.agents/skills"
echo "完成。请重启 Claude Code / Codex / Kimi Code（Kimi 可用 /reload）后生效。"
