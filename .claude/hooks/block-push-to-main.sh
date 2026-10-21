#!/usr/bin/env bash
# PreToolUse hook: block Claude from pushing to main. Exit 2 blocks; other failures fail open.
set -u
input=$(cat) || exit 1
cmd=$(jq -r '.tool_input.command // ""' <<<"$input") || exit 1
cwd=$(jq -r '.cwd // ""' <<<"$input") || exit 1
[[ "$cmd" =~ git([[:space:]].*)?[[:space:]]push ]] || exit 0

block() {
  echo "Pushing to main is blocked. Push a feature branch and open a PR." >&2
  exit 2
}

# Split on && || ; | and newlines, then inspect each git push segment.
while IFS= read -r seg; do
  read -ra t <<<"$seg"
  dir=$cwd; i=0
  while (( i < ${#t[@]} )) && [[ ${t[i]} != git ]]; do ((i++)); done
  (( i < ${#t[@]} )) || continue
  ((i++))
  while (( i < ${#t[@]} )) && [[ ${t[i]} == -* ]]; do
    [[ ${t[i]} == -C ]] && { dir=${t[i+1]:-$dir}; ((i++)); }
    ((i++))
  done
  [[ ${t[i]:-} == push ]] || continue
  ((i++))
  pos=()
  for a in "${t[@]:i}"; do
    case $a in
      --all|--mirror) block ;;
      -*) ;;
      *) pos+=("$a") ;;
    esac
  done
  refs=("${pos[@]:1}")
  cur=$(git -C "$dir" symbolic-ref --short -q HEAD 2>/dev/null || true)
  if (( ${#refs[@]} == 0 )); then
    [[ $cur == main ]] && block
    continue
  fi
  for r in "${refs[@]}"; do
    r=${r#+}
    if [[ $r == *:* ]]; then dst=${r##*:}; else dst=$r; fi
    dst=${dst#refs/heads/}
    [[ $dst == main ]] && block
    [[ $dst == HEAD && $cur == main ]] && block
  done
done < <(sed -E 's/(&&|\|\||;|\|)/\n/g' <<<"$cmd")
exit 0
