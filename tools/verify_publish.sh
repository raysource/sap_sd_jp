#!/usr/bin/env bash
# 公開後の検証: 遠端が本当に手元と一致しているかを「push の出力」ではなく
# git ls-remote / gh api / ファイル数で確かめる。
#
#   bash tools/verify_publish.sh
set -euo pipefail
cd "$(dirname "$0")/.."
R="raysource/sap_sd_jp"
BR="main"

LOCAL=$(git rev-parse HEAD)
LSR=$(git ls-remote origin -h "refs/heads/$BR" | cut -f1)
API=$(gh api "repos/$R/commits/$BR" --jq .sha)

echo "local HEAD      : $LOCAL"
echo "git ls-remote   : $LSR"
echo "gh api commits  : $API"
if [ "$LOCAL" = "$LSR" ] && [ "$LOCAL" = "$API" ]; then
  echo "RESULT: 一致（3 経路とも同じ commit）"
else
  echo "RESULT: 不一致 — push が届いていないか、別 commit を見ている"; exit 1
fi

gh repo view "$R" --json name,visibility,defaultBranchRef,url \
  --jq '"repo            : \(.name)  visibility=\(.visibility)  default=\(.defaultBranchRef.name)\nurl             : \(.url)"'

N_REMOTE=$(gh api "repos/$R/git/trees/$BR?recursive=1" --jq '[.tree[]|select(.type=="blob")]|length')
N_LOCAL=$(git -c core.quotepath=false ls-files | wc -l | tr -d ' ')
echo "remote blobs    : $N_REMOTE"
echo "local tracked   : $N_LOCAL"
[ "$N_REMOTE" = "$N_LOCAL" ] && echo "RESULT: ファイル数一致" || { echo "RESULT: ファイル数不一致"; exit 1; }

echo "=== 主要ファイルが遠端から読めるか（サイズ） ==="
for f in index.html config.html glossary.html SAPSD_学習WBS.xlsx README.md \
         assets/diagrams/mindmap.svg assets/img/sd/t01/01_1_image1078.png; do
  S=$(gh api "repos/$R/contents/$f" --jq .size 2>/dev/null || echo "NG")
  printf "  %-42s %s bytes\n" "$f" "$S"
done
