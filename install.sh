#!/usr/bin/env sh
# 一行装好：把 quiver 的 skill 放进当前能找到的每个 Agent 客户端的 skills 目录。
# 不猜你的目录结构，只装到确实存在的客户端；一个都没有时退化成打印指引。
set -eu
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo "需要 Python 3.8+"; exit 1; fi

FOUND=0
[ -d "$HOME/.claude" ]    && { "$PY" scripts/install.py --all --client claude    && FOUND=1; }
[ -d "$HOME/.workbuddy" ] && { "$PY" scripts/install.py --all --client workbuddy && FOUND=1; }
[ -d "$HOME/.codex" ] && {
  mkdir -p "$HOME/.codex/skills"
  for d in skills/*/; do cp -R "$d" "$HOME/.codex/skills/"; done
  echo "已装进 $HOME/.codex/skills/"; FOUND=1
}

if [ "$FOUND" -eq 0 ]; then
  cat <<'EOF'
没找到已安装的 Agent 客户端。手动指定目标目录：

    python scripts/install.py --all --target /path/to/your/client/skills

或用通用路径——多数客户端都认 .agents/skills/：

    mkdir -p .agents/skills && cp -R skills/* .agents/skills/
EOF
fi
