# -*- coding: utf-8 -*-
"""日本語版だけの追加ページ：用語集（日本語 ⇔ 画面の中国語 ⇔ 英語）と IMG パス対照。

このモジュールは sap_jp_sd 固有。中国語の物差し（原教材）と日本語訳を並べて見せるための
ページで、親エージェント（人）が日本語で書く。データは all 生成物から取る（手書きしない）:
  - work/ja/glossary.json  … 用語ベース（日本語 ⇔ 中国語）
  - work/sd_source_ja.json / work/sd_source.json … 48 タスクの日本語 / 中国語の IMG パス
  - p_admin.TERMS / TCODES … 英語名・説明・T-code（すでに日本語化済み）
"""
import json
import os
import re

import common
from common import TASK, TASK_JA, esc, note, steps_list, tbl
from p_admin import TCODES, TERMS

# ---------------------------------------------------------------- データ
def _glossary():
    p = os.path.join(common.ROOT, "work", "ja", "glossary.json")
    if not os.path.exists(p):
        return {}, {}, []
    d = json.load(open(p, encoding="utf-8"))
    return d.get("terms", {}), d.get("path_nodes", {}), d.get("notes", [])


def _freq():
    """用語の出現回数（学習順に近い並びを作るため）。中国語コーパスを数える。"""
    parts = []
    for kind in ("py_atoms", "js_atoms", "model_atoms"):
        p = os.path.join(common.ROOT, "work", "ja", "%s.json" % kind)
        if not os.path.exists(p):
            continue
        for v in json.load(open(p, encoding="utf-8"))["atoms"].values():
            parts.append(v["text"])
    p = os.path.join(common.ROOT, "work", "sd_source.json")
    if os.path.exists(p):
        parts.append(open(p, encoding="utf-8").read())
    return "\n".join(parts)


GUI_TERMS = [
    ("保存", "保存", "F11 / Ctrl+S"),
    ("Enter キー", "回车", "確認して次へ"),
    ("新規エントリ", "新条目", "Ctrl+F に近い操作"),
    ("実行", "执行", "F8"),
    ("照会（表示モード）", "显示", "参照のみ"),
    ("変更（変更モード）", "更改", "入力可"),
    ("登録（新規作成）", "创建", "伝票・マスタの新規"),
    ("戻る", "返回", "F3"),
    ("終了", "退出", "Shift+F3"),
    ("取消（取り消し）", "撤销", "F12"),
    ("コピー", "复制", "既存データから"),
    ("削除", "删除", "—"),
    ("選択（行を選ぶ）", "选中", "—"),
    ("チェックを入れる", "勾选", "—"),
    ("旗アイコン", "小旗子", "変更内容を反映"),
    ("必須項目", "必填", "—"),
    ("任意項目", "可选", "—"),
    ("非表示項目", "隐藏", "画面レイアウトによる"),
    ("項目（フィールド）", "字段", "F1 で項目ヘルプ"),
    ("入力ヘルプ（候補一覧）", "F4 取值列表", "F4"),
]


# よく出る用語の英語名（SAP の英語表記）。用語対照表の 3 列目に使う。
# TERMS（p_admin）にも英語があるが 48 語分しかないので、頻度上位をここで補う。
JEN = {
    "得意先": "Customer", "得意先マスタ": "Customer Master", "データ": "Data",
    "品目": "Material", "品目マスタ": "Material Master", "受注伝票": "Sales Order",
    "条件": "Condition", "条件タイプ": "Condition Type", "条件テーブル": "Condition Table",
    "条件レコード": "Condition Record", "アクセス順序": "Access Sequence",
    "納入": "Delivery", "納入日": "Delivery Date", "出荷伝票": "Outbound Delivery",
    "割当": "Assignment", "価格設定": "Pricing", "伝票": "Document",
    "マスタ": "Master Data", "販売グループ": "Sales Group", "販売事務所": "Sales Office",
    "タイプ": "Type", "カテゴリ": "Category", "明細カテゴリ": "Item Category",
    "明細": "Item", "プロセス": "Process", "請求書": "Billing Document",
    "請求": "Billing", "テーブル": "Table", "決定": "Determination", "定義": "Define",
    "教材": "Teaching Material", "在庫": "Stock", "構造": "Structure", "エリア": "Area",
    "販売組織": "Sales Organization", "流通チャネル": "Distribution Channel",
    "製品部門": "Division", "販売エリア": "Sales Area", "計算スキーマ": "Pricing Procedure",
    "登録": "Create", "価格": "Price", "システム": "System", "タスク": "Task",
    "出荷": "Shipping", "勘定": "Account", "勘定設定": "Account Determination",
    "勘定キー": "Account Key", "勘定割当グループ": "Account Assignment Group",
    "転記": "Posting", "出庫過転記": "Post Goods Issue", "ピッキング": "Picking",
    "収益": "Revenue", "収益勘定": "Revenue Account", "プラント": "Plant",
    "見積": "Quotation", "引合": "Inquiry", "ステータス": "Status",
    "設定": "Configuration", "順序": "Sequence", "出荷ポイント": "Shipping Point",
    "積込ポイント": "Loading Point", "保管場所": "Storage Location",
    "会社コード": "Company Code", "輸送条件": "Shipping Conditions",
    "計算タイプ": "Calculation Type", "売上税": "Output Tax", "税コード": "Tax Code",
    "税分類": "Tax Classification", "パートナ": "Partner", "出荷先": "Ship-to Party",
    "受注先": "Sold-to Party", "支払先": "Payer", "請求先": "Bill-to Party",
    "所要量確認": "Availability Check", "正味価額": "Net Value",
    "販売ビュー": "Sales View", "更新グループ": "Update Group",
    "伝票フロー": "Document Flow", "元伝票": "Original Document",
    "受注一覧": "Sales Order List", "販売分析": "Sales Analysis",
    "総勘定元帳": "General Ledger", "貸借対照表": "Balance Sheet",
    "会計伝票": "Accounting Document", "財務会計": "Financial Accounting",
    "権限": "Authorization", "環境": "Environment", "標準値": "Standard Value",
    "実習": "Exercise", "講師": "Instructor", "受講者": "Student",
    "用語集": "Glossary", "コース": "Course", "学習ルート": "Learning Path",
    "完成基準": "Acceptance Criteria", "セルフチェックテスト": "Self-check",
    "カスタマイジング": "Customizing (IMG)", "業務処理": "Application / Execute",
    "画面": "Screen", "スクリーンショット": "Screenshot", "自作図": "Self-drawn Diagram",
    "フロー図": "Flowchart", "構造図": "Structure Chart", "マインドマップ": "Mind Map",
    "受注": "Sales Order", "購買": "Purchasing", "ロジスティクス": "Logistics",
    "不完全性": "Incompletion", "与信": "Credit", "出力": "Output",
    "販売": "Sales", "登録・保守": "Maintain", "番号": "Number",
    "組織データ": "Organizational Data", "会社": "Company", "得意先-品目": "Customer-Material",
    "品目決定": "Material Determination", "リストと除外": "Listing / Exclusion",
    "単位": "Unit", "金額": "Amount", "数量": "Quantity", "日付": "Date",
    "期間": "Period", "有効期間": "Validity Period", "為替": "Exchange Rate",
    "与信管理": "Credit Management", "売掛金": "Receivables", "入金": "Incoming Payment",
    "消込": "Clearing", "売上原価": "Cost of Goods Sold", "原価": "Cost",
    "利益": "Profit", "限界利益": "Contribution Margin", "伝票タイプ": "Document Type",
    "納入日程行": "Schedule Line", "確認": "Confirmation", "伝達": "Transfer",
    "所要量": "Requirement", "所要量タイプ": "Requirement Type",
    "戦略": "Strategy", "評価": "Valuation", "個別在庫": "Special Stock",
    "プロジェクト": "Project", "WBS": "WBS Element", "在庫評価": "Inventory Valuation",
    "レコード": "Record", "ビュー": "View", "一覧": "List", "説明": "Description",
    "解説": "Commentary", "標準": "Standard", "クリック": "Click", "チェック": "Check",
    "分析": "Analysis", "企業構造": "Enterprise Structure", "項目": "Field", "入力": "Input",
    "入力値": "Input Value", "保存": "Save", "新規エントリ": "New Entries", "実行": "Execute",
    "照会": "Display", "変更": "Change", "削除": "Delete", "選択": "Select", "戻る": "Back",
    "終了": "Exit", "コピー": "Copy", "必須": "Required", "任意": "Optional",
    "非表示": "Hidden", "ボタン": "Button", "ラベル": "Label", "タイトル": "Title",
    "章": "Chapter", "ページ": "Page", "手順": "Procedure", "ステップ": "Step",
    "ポイント": "Point", "誤解": "Misconception", "つまずき": "Pitfall",
    "会計": "Accounting", "財務": "Finance", "税": "Tax", "在庫管理": "Inventory Management",
    "購買発注": "Purchase Order", "生産": "Production", "原価計算": "Costing",
    "組織": "Organization", "組織構造": "Organizational Structure",
    "販売構造": "Sales Structure", "出荷構造": "Shipping Structure",
    "パートナ決定": "Partner Determination", "与信限度": "Credit Limit",
    "不完全性チェック": "Incompletion Check", "得意先勘定グループ": "Customer Account Group",
}


def _term_rows():
    terms, _nodes, _notes = _glossary()
    en_of = {}
    for zh, en, _code, _desc in TERMS:
        en_of.setdefault(zh, en)
    corpus = _freq()
    rows, rattrs = [], []
    items = sorted(terms.items(), key=lambda kv: (-(corpus.count(kv[0])), kv[1]))
    for zh, ja in items:
        en = JEN.get(ja) or en_of.get(zh) or "—"
        rows.append([ja, zh, en])
        rattrs.append('data-key="%s"' % esc("%s %s %s" % (ja, zh, en)))
    return rows, rattrs, len(rows)


def _path_rows():
    rows = []
    for n in sorted(TASK_JA):
        j = (TASK_JA[n].get("path") or "").strip()
        z = (TASK[n].get("path") or "").strip()
        if not j:
            continue
        rows.append(["%02d" % n, esc(TASK_JA[n]["title"]), esc(j),
                     "<code>%s</code>" % esc(z) if z else "—"])
    return rows


# ---------------------------------------------------------------- ページ
def page_glossary(stats):
    b = []
    b.append('<p class="breadcrumb"><a href="index.html">ホーム</a> / <span>用語集</span></p>')
    b.append('<h1>用語集と T-code クイックリファレンス</h1>')
    b.append('<p class="kicker">日本語 ⇔ 画面の中国語 ⇔ 英語 · IMG パス対照 · よく使う T-code · '
             '伝票タイプコード · テーブル</p>')
    b.append(note("tip", "調べ方",
                  "ページ内は <b>Cmd/Ctrl + F</b> で日本語・中国語・英語のどれでも検索できます。"
                  "システム上で項目の意味が分からないときは、カーソルを項目に置いて <b>F1</b>（項目ヘルプ）、"
                  "<b>F4</b>（入力ヘルプ＝候補一覧）を押します。"
                  "画面は<b>中国語インターフェース</b>なので、日本語の用語から画面の中国語へ読み替える表を先頭に置いています。"))

    rows, rattrs, n_terms = _term_rows()
    b.append('<h2 id="terms">1. 用語対照表（日本語 ⇔ 画面の中国語）（%d 語）</h2>' % n_terms)
    b.append('<div class="filterbar"><input type="search" id="taskfilter" '
             'placeholder="キーワードで絞り込み（例: 販売エリア / 销售范围 / sales area / VOV4）"></div>')
    b.append('<p class="hitcount" id="hitcount">全 %d 件を表示</p>' % n_terms)
    b.append(tbl(["日本語（学習用）", "画面の中国語", "英語"],
                 rows, row_attrs=rattrs, tid="idxtable"))
    b.append(note("info", "表の読み方",
                  "左が学習で使う日本語用語、中央が<b>自分の画面に出る中国語</b>、右が SAP の英語名です。"
                  "画面の中国語は教材の実機スクリーンショットと同じ表記です（例: 販売エリア ⇔ 销售范围）。"))

    b.append('<h2 id="gui">2. 画面操作の用語（日本語 ⇔ 中国語）</h2>')
    b.append('<p>ボタン名・ショートカットは日本語教材と中国語画面で表記が違います。'
             '「日本語で覚えて、画面では中国語を探す」ための対応表です。</p>')
    b.append(tbl(["操作（日本語）", "画面の中国語", "ショートカット / 補足"],
                 [[esc(a), esc(b), esc(c)] for a, b, c in GUI_TERMS]))

    b.append('<h2 id="imgpath">3. IMG パス対照（日本語 ⇔ 中国語）</h2>')
    b.append('<p>IMG（カスタマイジング）のメニューパスは<b>言語依存</b>です。教材は中国語のパスなので、'
             '日本語版 IMG のノード名との対応をタスク番号順に並べました。'
             '自分の画面が中国語なら<b>右の列</b>を、日本語表示なら<b>左の列</b>をたどります。</p>')
    b.append(tbl(["タスク", "タスク名（日本語）", "IMG パス（日本語）", "原教材の中国語パス"],
                 _path_rows(), cls="tbl", first_mono=True))

    b.append('<h2 id="tcodes">4. よく使う T-code（%d 個）</h2>' % len(TCODES))
    b.append(tbl(["T-code", "用途", "工程", "教材タスク"],
                 [['<code>%s</code>' % esc(tc), esc(desc), esc(grp), esc(src)]
                  for tc, desc, grp, src in TCODES], first_mono=True))

    b.append('<h2 id="codes">5. 伝票タイプ / カテゴリコード</h2>')
    b.append(tbl(["コード", "意味", "使う場面"], [
        ["<code>IN</code>", "引合 Inquiry", "VA11"],
        ["<code>QT</code>", "見積 Quotation", "VA21"],
        ["<code>OR</code>", "標準受注伝票", "VA01（教材のシナリオ）"],
        ["<code>LF</code>", "出荷伝票", "VL01N"],
        ["<code>F2</code>", "請求書（教材のシナリオ）", "VF01"],
        ["<code>G2</code>", "貸方伝票（取消・返品でよく使う）", "VF01"],
        ["<code>TAN</code>", "標準明細カテゴリ", "受注伝票の明細"],
        ["<code>AG / WE / RE / RG</code>", "受注先 / 出荷先 / 請求先 / 支払先", "パートナ役割"],
        ["<code>601</code>", "出荷の出庫移動タイプ", "出庫過転記"],
    ]))
    b.append(note("warn", "コードはシステムによって異なります",
                  "上のコードは「よくある値」であって唯一の値ではありません。"
                  "<b>OR / LF / F2 / TAN はどれも設定可能</b>で、多くの企業は自社の Z タイプをコピーして使います。"
                  "学習では「コードがどの役割を表すか」を覚え、実際の値は自分のシステムで F4 を見て確認します。"))

    b.append('<h2 id="tables">6. よく使うテーブル（データを見る）</h2>')
    b.append(tbl(["テーブル", "内容", "SE16N / SE16 での見方"], [
        ["<code>VBAK</code> / <code>VBAP</code>", "受注伝票ヘッダ / 明細", "伝票番号で照会"],
        ["<code>VBEP</code>", "納入日程行（所要量伝達・確認数量）", "伝票番号で照会"],
        ["<code>LIKP</code> / <code>LIPS</code>", "出荷伝票ヘッダ / 明細", "出荷番号で照会"],
        ["<code>VBRK</code> / <code>VBRP</code>", "請求書ヘッダ / 明細", "請求書番号で照会"],
        ["<code>KONV</code>", "伝票条件（その伝票で実際に使われた価格）", "伝票番号で照会"],
        ["<code>KONH</code> / <code>KONP</code>", "条件レコードヘッダ / 金額", "条件タイプで照会"],
        ["<code>KNVV</code>", "得意先の販売エリアデータ", "得意先 + 販売エリア"],
        ["<code>MVKE</code>", "品目の販売ビュー（販売組織／チャネル単位）", "品目 + 販売組織"],
        ["<code>TVKO</code> / <code>TVTW</code> / <code>TSPA</code>", "販売組織 / 流通チャネル / 製品部門", "組織データ"],
        ["<code>TVAP</code> / <code>TVEP</code>", "明細カテゴリ / 納入日程行カテゴリの定義", "伝票制御"],
        ["<code>VBFA</code>", "伝票フロー（伝票のつながり）", "伝票番号で流れを照会"],
    ]))
    b.append(note("ref", "テーブル名について",
                  "テーブル名は「技術的な詳細」なので、業務ユーザーが暗記する必要はありません。"
                  "ただしコンサルタントのトラブルシューティングでは強力です（<code>VBFA</code> で伝票フロー、"
                  "<code>KONV</code> でその伝票の実際の価格が直接見られます）。照会には権限が必要です。"))

    b.append(steps_list([
        '<a href="index.html">ホーム</a>に戻ってコースマップを見る。',
        '迷ったときの自問: この問題は <a href="concept.html">概念</a>・<a href="org.html">組織</a>・'
        '<a href="master.html">マスタ</a>・<a href="pricing.html">価格設定</a>・'
        '<a href="flow.html">プロセス</a> のどれ？',
    ]))
    return b
