#!/usr/bin/env bash
# sap_jp_sd（SAP SD トレーニングコース日本語版）を独立リポジトリとして公開する。
#   https://github.com/raysource/sap_sd_jp （public）
#
#   bash tools/publish_to_github.sh          # init（無ければ）+ remote + commit + push（何度でも再実行可）
#
# 注意: このスクリプトを走らせると sites ディレクトリに .git ができるため、
#       親リポジトリ（raysource/sap-consult）からは「入れ子リポジトリ」になる。
#       親へは tools/include_nested_repo_files.sh で取り込む（sap_sd_cn / sap_cn と同じ扱い）。
set -euo pipefail
cd "$(dirname "$0")/.."
R="raysource/sap_sd_jp"
BR=main

if [ ! -d .git ]; then
  git init -q -b "$BR"
fi
# リポジトリ内だけの identity（グローバル設定は触らない）
git config user.name  "$(git config user.name  || echo Jason)"
git config user.email "$(git config user.email || echo jason@localhost)"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "https://github.com/$R.git"
else
  git remote add origin "https://github.com/$R.git"
fi

git add -A
if git diff --cached --quiet; then
  echo "コミットする変更なし"
else
  git -c core.quotepath=false status --short | sed 's#^#  #' | head -20
  echo "  … 合計 $(git diff --cached --name-only | wc -l | tr -d ' ') ファイル"
  git commit -q -m "${1:-sap_jp_sd: SAP SD トレーニングコース（日本語版）— 16 ページ / 設定 48 タスク / 実機画面 269 枚}"
fi

git push -u origin "$BR"
echo "---"
echo "local HEAD : $(git rev-parse HEAD)"
echo "remote main: $(git ls-remote origin -h refs/heads/$BR | cut -f1)"
