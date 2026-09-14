# SAP SD トレーニングコース（日本語版） — `sap_jp_sd/`

中国語版コース **`sap_cn`**（公開: https://sap-cn-sd.vercel.app/ ）を**日本語にしたもの**です。
内容・構成・画面は同一で、**本文の言語だけを日本語**にしています。静的な HTML なので、
`index.html` をダブルクリックすればオフラインで開けます（サーバー不要・ネット接続不要）。

- 入口: `index.html`（コースマップ = マインドマップ + 学習ルート）
- Excel: `SAPSD_学習WBS.xlsx`（8 シート）
- 実機スクリーンショット: `assets/img/{sd,prep}/**`（269 枚・**中国語インターフェースの SAP GUI**）
- 自作図: `assets/diagrams/*.svg`（7 枚: マインドマップ / フロー図 / 構造図）

## 日本語版で足したもの（中国語版との違い）

1. **ホームの「このサイトについて（日本語版）」** — 本文は日本語・画面は中国語という関係の説明。
2. **`glossary.html` を「用語対照表」として書き直し** — ① 用語対照表（日本語 ⇔ **画面の中国語** ⇔ 英語、291 語・絞り込み付き）、
   ② 画面操作の用語（保存/回车、新規エントリ/新条目、照会/显示 …）、③ **IMG パス対照（日本語 ⇔ 中国語、48 タスク全部）**、
   ④ 常用 T-code、⑤ 伝票タイプ / カテゴリコード、⑥ よく使うテーブル。
3. **`config.html`（設定 48 タスク）** — 各タスクに **原教材の中国語パス**（`原教材の中国語パス` 行）と、
   手順 1 行ごとの **「原文（中国語）」折りたたみ**を併記。日本語の用語と画面の中国語を突き合わせながら進められます。
4. それ以外のページでも、IMG パス行には自動で中国語原文が付きます（`pathline()` が日本語パスから逆引き）。

> 画面（スクリーンショット）は原教材の**中国語インターフェース**のままです。ボタン名・メッセージ・
> 得意先名などの**画面に出る値は中国語のまま**引用しています（本文中で「…」に入れて示しています）。

## 16 ページの構成（教学順 = ナビ順）

| ページ | 内容 | 自作図 | 実機画面 |
|---|---|---|---|
| `index.html` | コースマップ、学習ルート、6 セクション、ロール別ルート | マインドマップ | — |
| `concept.html` | 概念と位置づけ: 実機画面、3 つの概念層、5 大伝票、12 のよくある誤解 | 構造図×2、フロー図×2 | 3 |
| `org.html` | 組織構造: 企業構造 / 販売構造 / 出荷構造 + 12 の設定タスク | 組織図 | 11 |
| `master.html` | マスタ: 得意先の 3 層、4 つのパートナ役割、品目の販売ビュー、条件レコード | — | 9 |
| `pricing.html` | 価格設定: 条件テーブル → アクセス順序 → 条件タイプ → 計算スキーマ → スキーマ決定 → 勘定設定 | 構造図 | 3 |
| `flow.html` | エンドツーエンド O2C（スイムレーン）、統合ポイント、ステータス、順序エラー | フロー図 | 1 |
| `order.html` | 見積 → 受注伝票（参照登録）、項目の読み方、在庫不足時の扱い | フロー図 | 8 |
| `delivery.html` | VL01N 納入 → ピッキング → 出庫過転記（601）→ 在庫と会計への影響 | — | 6 |
| `billing.html` | VF01 請求 → VF02 リリース → 会計伝票 → 元伝票 / 伝票フロー → 入金 | フロー図 | 8 |
| `analysis.html` | 伝票フロー、VA05、MCTA（前提条件つき）、照合、教材のつまずき集 | — | 8 |
| `config.html` | **設定 48 タスク**を A〜J の 10 グループで索引（IMG パス + 手順 + 画面 + 原文） | — | 96 |
| `practice.html` | 実習 5 タスク（やること / 完成基準 / よくある誤り / 対応する画面） | — | 10 |
| `instructor.html` | 講師用: 時間配分、板書ルート、必ず問う 12 問と解答、採点基準 | — | — |
| `worksheet.html` | 受講者用: 記入表（伝票番号 / ステータス / 金額 / 自己判定）、印刷可 | — | — |
| `quiz.html` | セルフチェック 30 問（概念 5 / 組織 4 / マスタ 5 / 価格設定 6 / プロセス 7 / 分析 3）、合格 75% | — | — |
| `glossary.html` | **用語対照表（日本語 ⇔ 中国語画面）** + T-code + 伝票タイプ + テーブル | — | — |

## 出典（重要）

1. **実機スクリーンショット**は教材ドキュメント `S4.docx`（`../sap_sd_cn/S4.docx`、425 ページ・埋め込み画像 1385 枚）の
   SD モジュールと準備章から **269 枚**を再利用したもの。各図の説明行に**元のファイル名**（例 `01_1_image1297.png`）を
   残してあるので、Word 原稿と 1 枚ずつ突き合わせできます。**画像は加工していません**（本サイトで描き直したものではありません）。
2. **タスク番号・IMG パス・手順は教材と一致**。`work/sd_source.json`（中国語原文・原教材のまま）と
   `work/sd_source_ja.json`（日本語訳）を持ち、ページはこの 2 つから生成します（手で書き写していません）。
3. **自作図（`assets/diagrams/*.svg`）は本コースの自作**で、構造と順序を説明するためのものです。
   図中の数値はコースのシナリオ値であって、標準値ではありません。

## 標準値の書き方

バージョン / 業界ソリューションで変わりうる箇所は、断定せず**「自システムでの確認方法」**（F1 / F4、IMG パス、SE16N のテーブル）を示しています。
教材の画面で確認できたシナリオ値はそのまま出典付きで掲載しています:
正味価額 960,000.00 RMB、請求書 `F2` 90000000、請求書日付 2021.04.15、支払先 10000000、120 PC、
品目 F999-100、出荷ポイント Z999（颐寧出荷ポイント）、勘定割当グループ M1/M2、計算スキーマ RVAA01。

> 教材の `F1 / F2` は 2 つの意味があります: SAP GUI では **F1/F4 はファンクションキー**（項目ヘルプ / 入力ヘルプ）、
> **`F2` は請求書の伝票タイプ**です。ページ上では文脈を明示しています。

## ディレクトリ

```
sap_jp_sd/
├─ index.html … quiz.html … glossary.html   16 ページ（日本語）
├─ assets/
│  ├─ style.css main.js quiz.js             共有デザイン（中国語版からコピー、未改変）
│  ├─ sd.css sd.js                          サイト追加スタイル / ライトボックス（日本語化 + 原文併記の CSS を追加）
│  ├─ img/{sd,prep}/…                       実機スクリーンショット 269 枚（原ディレクトリ構造のまま）
│  └─ diagrams/*.svg                        自作図 7 枚（日本語ラベルで再生成）
├─ tools/
│  ├─ sitegen/{common.py,p_overview.py,p_process.py,p_admin.py}  ページ本体（日本語）
│  ├─ sitegen/p_jp.py                       日本語版だけの追加ページ（用語対照表）
│  ├─ make_diagrams.py                      自作図ジェネレータ（Python → SVG）
│  ├─ build_pages.py                        16 ページ生成（冪等）
│  ├─ make_course_xlsx.py                   Excel 生成（8 シート）
│  ├─ verify_course.py                      サイト専用検証器
│  └─ hub_stats.json                        トレーニングサイト索引用の自己申告
└─ work/
   ├─ i18n.py                               構造保存型の翻訳ツール（collect → batches → merge → check → apply）
   ├─ jp_finalize.py                        翻訳後の構造パッチ（lang=ja / 原文併記 / Excel 名 / 用語集の差し替え）
   ├─ qa_ja.py                              中国語の残留チェック（意図的な残置と区別して数える）
   ├─ check_diagram_fit.py                  自作 SVG の文字はみ出しチェック
   ├─ ja/                                   BRIEF.md / glossary.json（用語ベース）/ batch / out / *_map.json
   ├─ sd_source.json                        原教材の 48 タスク（**中国語原文**、照合用）
   ├─ sd_source_ja.json                     同 48 タスクの**日本語訳**（ページはこちらを表示）
   ├─ img_manifest.json / gui_screenshot_text.json / diagram_qa.json
```

## 再生成 / 検証

```bash
cd ~/Desktop/work/training/sap_jp_sd

python3 tools/make_diagrams.py       # 自作図 → assets/diagrams/*.svg（冪等）
python3 tools/build_pages.py         # 16 ページ（統計数字は自動で数える）
python3 tools/make_course_xlsx.py    # SAPSD_学習WBS.xlsx（8 シート）

python3 tools/verify_course.py                                              # サイト専用検証器
python3 ~/.hermes/skills/productivity/sap-training-sites/scripts/verify_site.py .   # 共有検証器
python3 work/qa_ja.py                # 中国語の残留（意図的な残置は別枠で表示）
python3 work/check_diagram_fit.py ../sap_cn .   # 図の文字はみ出し（中国語版との差分）
```

翻訳のやり直し（用語ベースを直して全部作り直す場合）:

```bash
# work/ja/orig/ に原文がある場合のみ: collect → (子エージェントが out/ を書く) → merge → check → apply
python3 work/i18n.py collect all && python3 work/i18n.py batches 4200
python3 work/i18n.py merge && python3 work/i18n.py check && python3 work/i18n.py apply all
python3 work/jp_finalize.py && python3 tools/build_pages.py
```

> 注意: `i18n.py apply py/js` は**収集時点のファイルハッシュでガード**しています。`jp_finalize.py` や
> 手作業の修正でソースを触った後は適用されません（壊さないための仕様）。用語だけ直したい場合は
> `work/ja/model_map.json` を直して `python3 work/i18n.py apply model`（こちらは冪等）、
> 本文はソースを直接直してからビルドし直します。

## 既知の境界（欠陥ではありません）

- **画面は中国語**です。日本語の用語と画面の表示は一致しないので、`glossary.html` の対照表と
  `config.html` の「原文（中国語）」を併用してください。
- スクリーンショットは教材原図の**小さめの切り抜き**（多くは幅 400〜700px、作者が赤枠を描いたもの）なので、
  2 倍以上に拡大すると粗くなります。ページには「画面表示サイズ 1×/1.5×/2×」と 4× ライトボックスがあります（投影は 1.5× 推奨）。
- **SAP システムにはログインできません**。ページ内の「練習」はすべて「自システムでどう確認するか」（F1/F4 + テーブル + T-code）の形で示し、
  実習タスクはアクセス可能な環境を前提にしています（`practice.html` に環境準備チェックリストと代替手段があります）。
- `tools/*.py` と `assets/*.js` のコメントも日本語化済み（中国語のコメント行 0）。表示テキストは文字列リテラル由来なので、
  ソースのコメント変更は HTML に影響しません（`build_pages.py` の出力は同じ）。
- 中国語版 `sap_cn/` とは独立したディレクトリです（同じ教材・同じ画面を使っています）。
  - **公開（GitHub / Vercel）は未実施**です。`sap_cn/tools/` の公開スクリプト（`publish_to_github.sh` / `verify_publish.sh` /
    `reconcile_remote.sh`）のパスを差し替えれば同じ手順で公開できます。
  - **トレーニングサイト索引（`../index.html`）へのカード追加も未実施**です（`../tools/make_hub_page.py` は共有ファイルのため、
    他サイトの索引に影響します）。本站は `tools/hub_stats.json` に自分の統計を自己申告済みなので、登録は SITES / ORDER に
    1 行足して `python3 ../tools/make_hub_page.py` を実行するだけです。
