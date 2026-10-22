#!/usr/bin/env bash
# Tests for block-push-to-main.sh. Run: bash .claude/hooks/test-block-push-to-main.sh
# Uses a throwaway git repo, so the project's own branches don't matter. Exits 1 on any failure.
HOOK="$(cd "$(dirname "$0")" && pwd)/block-push-to-main.sh"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
repo="$work/repo"
git init -q -b main "$repo"
git -C "$repo" -c user.name=t -c user.email=t@example.com commit -q --allow-empty -m init
git -C "$repo" branch feat/x
failures=0

json_escape() {
  local s=$1
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  printf '%s' "$s"
}

# expect <block|allow> <command> [PATH for the hook]
expect() {
  local want=$1 command=$2 path=${3:-$PATH} got
  printf '{"tool_input":{"command":"%s"},"cwd":"%s"}' "$(json_escape "$command")" "$(json_escape "$repo")" \
    | PATH="$path" "$BASH" "$HOOK" 2>/dev/null
  if [ $? -eq 2 ]; then got=block; else got=allow; fi
  if [ "$got" = "$want" ]; then
    printf 'ok    %-5s  %s\n' "$want" "$command"
  else
    printf 'FAIL  want %s, got %s  %s\n' "$want" "$got" "$command"
    failures=$((failures + 1))
  fi
}

run_cases() {
  local path=$1
  git -C "$repo" switch -q feat/x
  expect allow "git push" "$path"
  expect block "git push origin main" "$path"
  expect block "git push origin HEAD:main" "$path"
  expect block "git push origin feat/x:main" "$path"
  expect block "git push origin +main" "$path"
  expect block "git push origin refs/heads/main" "$path"
  expect block "git push origin HEAD:refs/heads/main" "$path"
  expect block "git push origin :main" "$path"
  expect block "git push --all" "$path"
  expect block "git push --mirror origin" "$path"
  expect allow "git push -u origin feat/main-menu" "$path"
  expect allow "git push -u origin HEAD" "$path"
  expect block "git add . && git commit -m x && git push origin main" "$path"
  expect block "git -c user.name=x push origin main" "$path"
  expect allow "git status" "$path"
  expect allow "ls -la; echo done" "$path"
  git -C "$repo" switch -q main
  expect block "git push" "$path"
  expect block "git push -u origin HEAD" "$path"
  expect allow "git push -u origin feat/x" "$path"
  expect block "git -C $repo push" "$path"
}

echo "== with the normal PATH"
run_cases "$PATH"

# Simulate a machine without jq: only bash, cat, git and python3 are reachable.
nojq="$work/bin-nojq"
mkdir -p "$nojq"
for tool in cat git python3; do
  real=$(command -v "$tool") && ln -s "$real" "$nojq/$tool"
done
if [ -e "$nojq/python3" ]; then
  echo "== without jq (python3 reads the JSON)"
  run_cases "$nojq"
else
  echo "== skipped the no-jq run: python3 is not installed"
fi

# Simulate a machine with neither jq nor python3: every push is blocked, nothing else is.
noparser="$work/bin-noparser"
mkdir -p "$noparser"
for tool in cat git; do
  ln -s "$(command -v "$tool")" "$noparser/$tool"
done
echo "== without jq or python3"
git -C "$repo" switch -q feat/x
expect block "git push -u origin feat/x" "$noparser"
expect allow "git status" "$noparser"

echo
if [ "$failures" -eq 0 ]; then
  echo "All hook tests passed."
else
  echo "$failures hook test(s) failed."
  exit 1
fi
