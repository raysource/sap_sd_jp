#!/usr/bin/env bash
# 逐路径对账: 遠端のファイル一覧と手元の tracked を突き合わせる。
#   - git ls-files は既定で CJK ファイル名をエスケープするので core.quotepath=false を使う
#   - comm は両側を同じ照合順序（LC_ALL=C）で sort しないと幻の差分が出る
#   - trees API はディレクトリのエントリも返すので type=="blob" で絞る
#
#   bash tools/reconcile_remote.sh
set -euo pipefail
cd "$(dirname "$0")/.."
R="raysource/sap_sd_jp"
BR="${1:-main}"

gh api "repos/$R/git/trees/$BR?recursive=1" --jq '.tree[]|select(.type=="blob")|.path' \
  | LC_ALL=C sort > /tmp/jp_r.txt
git -c core.quotepath=false ls-files | LC_ALL=C sort > /tmp/jp_l.txt

echo "remote blobs=$(wc -l < /tmp/jp_r.txt | tr -d ' ')  local tracked=$(wc -l < /tmp/jp_l.txt | tr -d ' ')"
echo "--- だけで遠端に在る（空が正しい）"
comm -23 /tmp/jp_r.txt /tmp/jp_l.txt | head -10
echo "--- だけで手元に在る（空が正しい）"
comm -13 /tmp/jp_r.txt /tmp/jp_l.txt | head -10

echo "--- ディレクトリ別の内訳（遠端）"
for d in . assets/img assets/diagrams tools work; do
  n=$(grep -c "^${d#./}/" /tmp/jp_r.txt || true)
  printf "  %-18s %s\n" "$d" "$n"
done
echo "  *.html             $(grep -c '\.html$' /tmp/jp_r.txt || true)"
echo "  *.xlsx             $(grep -c '\.xlsx$' /tmp/jp_r.txt || true)"
