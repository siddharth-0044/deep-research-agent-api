#!/usr/bin/env bash
# PreToolUse hook: block Claude from pushing to main. Exit 2 blocks; other failures fail open.
# Portable to macOS: bash 3.2 (no `set -u`, which breaks on empty arrays) and no GNU-only tools.
input=$(cat) || exit 1

block() {
  echo "Pushing to main is blocked. Push a feature branch and open a PR." >&2
  exit 2
}

# Read tool_input.command and cwd with jq, or with python3 when jq is missing.
if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""') || exit 1
  cwd=$(printf '%s' "$input" | jq -r '.cwd // ""') || exit 1
elif command -v python3 >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))') || exit 1
  cwd=$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cwd", ""))') || exit 1
else
  # No JSON reader, so the push target cannot be checked: stop anything that looks like a push.
  case $input in
    *push*)
      echo "Cannot check this git push: install jq (brew install jq) or python3. Blocked to keep main safe." >&2
      exit 2
      ;;
  esac
  exit 0
fi

push_re='git([[:space:]].*)?[[:space:]]push'
[[ $cmd =~ $push_re ]] || exit 0

# Split on && || ; | into one segment per line, then inspect each git push segment.
segs=$cmd
segs=${segs//&&/$'\n'}
segs=${segs//||/$'\n'}
segs=${segs//;/$'\n'}
segs=${segs//|/$'\n'}

while IFS= read -r seg; do
  t=()
  read -ra t <<<"$seg"
  n=${#t[@]}
  dir=$cwd
  i=0
  while (( i < n )) && [[ ${t[i]} != git ]]; do i=$((i + 1)); done
  (( i < n )) || continue
  i=$((i + 1))
  # git's own options: -C <dir> sets the repo, -c <key=value> takes a value.
  while (( i < n )) && [[ ${t[i]} == -* ]]; do
    case ${t[i]} in
      -C) i=$((i + 1)); dir=${t[i]} ;;
      -c) i=$((i + 1)) ;;
    esac
    i=$((i + 1))
  done
  [[ ${t[i]} == push ]] || continue
  i=$((i + 1))
  pos=()
  while (( i < n )); do
    case ${t[i]} in
      --all|--mirror) block ;;
      -*) ;;
      *) pos+=("${t[i]}") ;;
    esac
    i=$((i + 1))
  done
  cur=$(git -C "$dir" symbolic-ref --short -q HEAD 2>/dev/null)
  # pos[0] is the remote; anything after it is a refspec.
  if (( ${#pos[@]} <= 1 )); then
    [[ $cur == main ]] && block
    continue
  fi
  j=1
  while (( j < ${#pos[@]} )); do
    r=${pos[j]}
    r=${r#+}
    case $r in
      *:*) dst=${r##*:} ;;
      *) dst=$r ;;
    esac
    dst=${dst#refs/heads/}
    [[ $dst == main ]] && block
    [[ $dst == HEAD && $cur == main ]] && block
    j=$((j + 1))
  done
done <<<"$segs"
exit 0
