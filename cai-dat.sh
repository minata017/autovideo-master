#!/usr/bin/env bash
set -euo pipefail
task_script_dir=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  task_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
fi
task_app_dir="${AUTOVIDEO_DIR:-${task_script_dir:-$HOME/autovideo-master}}"
if [[ ! -f "$task_app_dir/autovideo.py" ]]; then
  if [[ -d "$task_app_dir" && -n "$(ls -A -- "$task_app_dir")" ]]; then
    echo 'Destination is not empty. Choose AUTOVIDEO_DIR.' >&2; exit 1
  fi
  mkdir -p -- "$task_app_dir"
  task_download="$(mktemp -d)"
  curl -fsSL 'https://github.com/minata017/autovideo-master/archive/refs/heads/main.tar.gz' -o "$task_download/repo.tar.gz"
  tar -xzf "$task_download/repo.tar.gz" -C "$task_download"
  cp -R "$task_download/autovideo-master-main/." "$task_app_dir/"
fi
mkdir -p "$task_app_dir/input/broll" "$task_app_dir/output" "$task_app_dir/temp" "$task_app_dir/bin"
[[ -f "$task_app_dir/.env" ]] || cp "$task_app_dir/.env.example" "$task_app_dir/.env"
if ! command -v uv >/dev/null 2>&1; then
  if [[ ! -x "$HOME/.local/bin/uv" ]]; then
    task_uv_script="$(mktemp)"
    curl -fsSL 'https://astral.sh/uv/install.sh' -o "$task_uv_script"
    sh "$task_uv_script"
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi
if [[ ! -x "$task_app_dir/.venv/bin/python" ]]; then
  uv venv --python 3.13 "$task_app_dir/.venv"
fi
uv pip install --python "$task_app_dir/.venv/bin/python" -r "$task_app_dir/requirements.txt"
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg
  else
    echo 'Install ffmpeg and ffprobe for your distribution, then rerun.' >&2; exit 1
  fi
fi
"$task_app_dir/.venv/bin/python" "$task_app_dir/autovideo.py" kiem-tra
printf 'Installed and checked: %s\n' "$task_app_dir"
printf 'Enter API keys in .env. Native macOS/Linux rendering requires verification on that platform.\n'
