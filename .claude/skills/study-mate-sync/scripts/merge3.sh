#!/usr/bin/env bash
# 三方合并：上游 BASE..NEW 的改动合进本地包。
# 用法：merge3.sh <上游仓库> <BASE> <NEW> <本地包> <映射文件>
# 映射文件每行：<上游路径>\t<本地路径>（同路径可写一列）；以 # 开头为注释。
# 上游路径可以是目录前缀（以 / 结尾），本地路径同样以 / 结尾，按前缀映射。
# 跳过规则写在 SKIP 正则里（传环境变量 SKIP）。
set -u
UP=$1; BASE=$2; NEW=$3; LOCAL=$4; MAP=$5
SKIP=${SKIP:-'^$'}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

map_path() {  # 上游路径 -> 本地路径（无映射输出空）
  local p=$1 up lo
  while IFS=$'\t' read -r up lo; do
    [[ -z "$up" || "$up" == \#* ]] && continue
    lo=${lo:-$up}
    if [[ "$up" == */ ]]; then
      [[ "$p" == "$up"* ]] && { echo "$lo${p#"$up"}"; return; }
    elif [[ "$p" == "$up" ]]; then echo "$lo"; return; fi
  done < "$MAP"
}

is_binary() { git -C "$UP" diff --numstat "$BASE" "$NEW" -- "$1" | grep -q '^-'; }

git -C "$UP" -c core.quotepath=false diff --name-status --no-renames "$BASE" "$NEW" | while IFS=$'\t' read -r st path; do
  [[ "$path" =~ $SKIP ]] && { echo "SKIP     $path"; continue; }
  lp=$(map_path "$path"); [[ -z "$lp" ]] && continue
  dst="$LOCAL/$lp"
  case $st in
    D)
      if [[ -f "$dst" ]]; then rm "$dst"; echo "DELETE   $lp"; fi ;;
    A)
      mkdir -p "$(dirname "$dst")"
      if [[ -f "$dst" ]]; then echo "EXISTS?  $lp（本地已有同名文件，未覆盖）"; continue; fi
      git -C "$UP" show "$NEW:$path" > "$dst"; echo "ADD      $lp" ;;
    M)
      if [[ ! -f "$dst" ]]; then echo "MISSING  $lp（本地没有，上游改了）"; continue; fi
      if is_binary "$path"; then git -C "$UP" show "$NEW:$path" > "$dst"; echo "BINARY   $lp"; continue; fi
      git -C "$UP" show "$BASE:$path" | tr -d '\r' > "$TMP/base"
      git -C "$UP" show "$NEW:$path"  | tr -d '\r' > "$TMP/new"
      tr -d '\r' < "$dst" > "$TMP/ours"
      git merge-file -L 本地 -L 上游基线 -L 上游新版 "$TMP/ours" "$TMP/base" "$TMP/new"
      rc=$?
      cp "$TMP/ours" "$dst"
      if [[ $rc -eq 0 ]]; then echo "MERGED   $lp"; else echo "CONFLICT $lp ($rc)"; fi ;;
  esac
done
