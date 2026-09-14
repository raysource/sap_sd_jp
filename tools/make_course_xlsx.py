# -*- coding: utf-8 -*-
"""コース用 Excel を生成：SAPSD_学習WBS.xlsx

    python3 tools/make_course_xlsx.py

ワークシート：
0_説明        … この Excel は何か、どう使うか
1_コースシラバス    … 16 ページ × 学ぶ内容 × 対応する自作図 × ページ内の要点
2_学習WBS     … セクションごとに「タスク単位」まで分解、進捗をチェック可能（COUNTIF 集計付き）
3_実習記録    … 5 つの実習タスクの伝票番号/ステータス/金額の記録（印刷して手書き、または直接入力）
4_スクリーンショット索引    … ページで参照している実際のスクリーンショット 1 枚ごと（ページ / タスク / 元のファイル名）
5_用語集      … 中英対照
6_Tcodeクイックリファレンス   … よく使う T-code
7_自作図一覧  … 10 枚のフロー図/構造図/マインドマップ

すべての内容は生成済みの HTML と sitegen データから読み取り、手で書き写しません。
"""
import os
import re
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sitegen"))
import common  # noqa: E402
import p_admin  # noqa: E402
import p_overview  # noqa: E402
import p_process  # noqa: E402

OUT = os.path.join(ROOT, "SAPSD_学習WBS.xlsx")
HEAD_FILL = PatternFill("solid", fgColor="0A6ED1")
HEAD_FONT = Font(name="Microsoft YaHei", size=10, bold=True, color="FFFFFF")
CELL_FONT = Font(name="Microsoft YaHei", size=10)
TITLE_FONT = Font(name="Microsoft YaHei", size=13, bold=True, color="0854A0")
THIN = Side(style="thin", color="D9E1E8")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(vertical="top", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center")


def sheet(wb, name, title, headers, rows, widths, note=None):
    ws = wb.create_sheet(name)
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    r = 2
    if note:
        ws["A2"] = note
        ws["A2"].font = Font(name="Microsoft YaHei", size=9, color="6B7A8D")
        r = 3
    hrow = r + 1
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=hrow, column=i, value=h)
        c.fill, c.font, c.alignment, c.border = HEAD_FILL, HEAD_FONT, CENTER, BORDER
    for j, row in enumerate(rows):
        for i, v in enumerate(row, 1):
            c = ws.cell(row=hrow + 1 + j, column=i, value=v)
            c.font, c.alignment, c.border = CELL_FONT, WRAP, BORDER
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=hrow + 1, column=1)
    ws.row_dimensions[hrow].height = 22
    return ws, hrow


def read_pages():
    """生成済みの HTML から、各ページの h1/h2 構造 + スクリーンショット参照を抽出します。"""
    pages = {}
    for f, label, tip in common.NAV:
        p = os.path.join(ROOT, f)
        s = open(p, encoding="utf-8").read()
        h1 = re.search(r"<h1>(.*?)</h1>", s, re.S)
        h2 = [re.sub("<[^>]+>", "", x).strip() for x in re.findall(r"<h2[^>]*>(.*?)</h2>", s, re.S)]
        shots = re.findall(r'src="(assets/img/[^"]+)"', s)
        dias = re.findall(r'src="(assets/diagrams/[^"]+)"', s)
        pages[f] = {"label": label, "tip": tip,
                    "h1": re.sub("<[^>]+>", "", h1.group(1)).strip() if h1 else "",
                    "h2": h2, "shots": shots, "dias": dias}
    return pages


def main():
    pages = read_pages()
    wb = Workbook()
    wb.remove(wb.active)

    # 0_説明
    ws = wb.create_sheet("0_説明（はじめに）")
    ws["A1"] = "SAP SD トレーニングコース — 付属 Excel"
    ws["A1"].font = Font(name="Microsoft YaHei", size=14, bold=True, color="0854A0")
    lines = [
        "",
        "付属サイト：index.html（静的 HTML。ダブルクリックでオフライン表示でき、サーバは不要）",
        "コース構成：概念 → 組織構造 → マスタ → 価格設定 → エンドツーエンドプロセス → 設定 → 実習（16 ページ）",
        "",
        "本 Excel の 8 シート：",
        "1_コースシラバス   … 各ページで何を扱うか、どの自作図を使うか、ページ内の小見出し",
        "2_学習WBS    … セクションごとにチェック可能なタスクに分解（進捗集計の数式付き）",
        "3_実習記録   … 5 つの実習タスクでやること、記録する伝票番号（印刷して実習室に持ち込める）",
        "4_スクリーンショット索引   … ページが参照する実際の SAP GUI スクリーンショット一覧（元のファイル名付き、Word 原稿で照合可能）",
        "5_用語集     … 日本語 ⇔ 中国語（画面表記）⇔ 英語の用語対照",
        "6_Tcodeクイックリファレンス  … よく使う T-code と用途",
        "7_自作図一覧 … 当サイトが自作したフロー図/構造図/マインドマップ",
        "",
        "重要なお知らせ：",
        "· 「画面 N」の実際のスクリーンショットは教材ドキュメント S4.docx に埋め込まれた SAP GUI 画面（中国語インターフェース）から取得したもので、描き直していません。",
        "· フロー図/構造図/マインドマップは本コースの自作 SVG で、構造と順序を分かりやすく説明するためのものです。",
        "· 受注伝票タイプ OR、明細カテゴリ TAN、計算スキーマ RVAA01、条件タイプ PR00/MWST などの意味は共通ですが、",
        "ただし具体的なコードと項目はリリース/業界ソリューションによって異なります —— ご自身のシステムで F1/F4 または IMG パスを使って確認してください。",
    ]
    for i, ln in enumerate(lines, 2):
        ws.cell(row=i, column=1, value=ln).font = Font(name="Microsoft YaHei", size=10)
    ws.column_dimensions["A"].width = 110

    # 1_コースシラバス
    rows = []
    for f, label, tip in common.NAV:
        d = pages[f]
        rows.append([f, label, d["h1"], " / ".join(d["h2"][:8]),
                     len(d["shots"]), len(d["dias"])])
    sheet(wb, "1_コースシラバス", "1. コースシラバス（16 ページ）",
          ["ファイル", "ナビゲーション名", "ページタイトル", "ページ内の小見出し（h2）", "スクリーンショット数", "自作図の数"],
          rows, [16, 12, 30, 70, 8, 10],
          note="スクリーンショット数 = そのページが参照する実際の画面数（同じ画像を複数回参照すると重複カウント）。自作図数 = そのページのフロー図/構造図/マインドマップの数。")

    # 2_学習WBS
    wbs = [
        ("A. 概念", "concept", "SD が何を管理し、FI/MM/PP/CO とどう役割分担するかを言える", "5 大伝票のチェーンを描き、3 つの概念レイヤを言える", 60),
        ("A. 概念", "concept", "12 のよくある誤解を覚える（面接/試験でよく問われる）", "5 つ選んで自分の言葉で言い直す", 30),
        ("B 組織", "org", "企業構造/販売構造/出荷構造を理解する", "組織図を描き、割当関係を説明できる", 60),
        ("B 組織", "org", "販売エリア＝3 つのキーの組み合わせ。例を挙げられる", "本システムの販売エリアを言える（2 つ以上）", 30),
        ("C マスタ", "master", "得意先マスタの 3 層＋4 つのパートナ役割", "4 つの役割を言い、それぞれが何を決定するかを説明する", 40),
        ("C マスタ", "master", "品目マスタの販売ビューの重要項目", "明細カテゴリグループ/税分類/勘定割当グループがどこにあるか指摘する", 40),
        ("C マスタ", "master", "条件レコードと価格の関係", "VK13 で PR00 の条件レコードを照会し、金額と有効期間を読み取る", 40),
        ("D 価格設定", "pricing", "条件技術の4階層構造", "4 つの層を暗記し、各層の役割を説明できる", 50),
        ("D 価格設定", "pricing", "計算スキーマ決定の 3 つのキー", "3 つのキーを言え、どこで設定するかも分かる", 30),
        ("D 価格設定", "pricing", "勘定設定：収益勘定の決め方", "勘定キー + 2 つの勘定割当グループを言える", 40),
        ("E プロセス", "flow", "O2C のエンドツーエンドプロセスと伝票フロー", "白紙にフロー図を書く（T-code 含む）", 60),
        ("E プロセス", "order", "見積 VA21 → 受注伝票 VA01 参照作成", "見積と受注伝票を独立して作成し、伝票番号を記録する", 60),
        ("E プロセス", "delivery", "納入 VL01N + ピッキング + 出庫過転記 601", "出庫過転記を 1 回完了し、在庫の変化を記録", 60),
        ("E プロセス", "billing", "請求書 VF01 ＋ リリース VF02 ＋ 会計伝票", "請求とリリースを完了し、会計伝票を確認", 60),
        ("E プロセス", "analysis", "伝票フロー／VA05／MCTA の使い方", "伝票フローで「この伝票はどこまで進んだか」に答える", 40),
        ("F 設定", "config", "48 個の設定タスクのグループとパス", "3つのタスクに対応するカスタマイジングメニューを指摘する", 60),
        ("F 設定", "config", "どの設定が自作必須で、どれが標準を使えるかを知っている", "自システムに存在する設定／不足している設定を一覧にする", 40),
        ("G 実習", "practice", "5 つの実習タスクをすべて完了", "完成基準を 1 つずつチェック（3_実習記録を参照）", 180),
        ("H まとめ", "quiz", "30 問のセルフチェックテスト（≥75%）", "得点と誤答の振り返り", 45),
    ]
    rows = []
    for i, (phase, page, what, done, mins) in enumerate(wbs, 1):
        rows.append([i, phase, common.NAV_LABEL.get(page, page) if hasattr(common, "NAV_LABEL") else page,
                     what, done, "", "", mins])
    ws, hrow = sheet(wb, "2_学習WBS", "2. 学習WBS（進捗をチェック可能）",
                     ["#", "セクション", "コースページ", "何を学ぶか", "完成基準（自分で検証できる）", "自分で判定する", "メモ / 疑問", "所要時間（分）"],
                     rows, [5, 10, 12, 40, 46, 10, 34, 10],
                     note="「自己判定」に ○ / △ / × を記入します（セルにはドロップダウンを設定済み）。進捗の集計は本表の下にあります。")
    last = hrow + len(rows)
    for r in range(hrow + 1, last + 1):
        ws.cell(row=r, column=6).alignment = CENTER
    from openpyxl.worksheet.datavalidation import DataValidation
    dv = DataValidation(type="list", formula1='"○,△,×"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add("F%d:F%d" % (hrow + 1, last))
    ws.cell(row=last + 2, column=4, value="合計／達成率").font = Font(name="Microsoft YaHei", size=10, bold=True)
    ws.cell(row=last + 2, column=5, value="=COUNTA(E%d:E%d)&\" 件\"" % (hrow + 1, last)).font = CELL_FONT
    ws.cell(row=last + 3, column=4, value="完了（○）").font = Font(name="Microsoft YaHei", size=10, bold=True)
    ws.cell(row=last + 3, column=5, value='=COUNTIF(F%d:F%d,"○")&" / "&COUNTA($D$%d:$D$%d)' % (hrow + 1, last, hrow + 1, last)).font = CELL_FONT
    ws.cell(row=last + 4, column=4, value="予定総所要時間（分）").font = Font(name="Microsoft YaHei", size=10, bold=True)
    ws.cell(row=last + 4, column=5, value="=SUM(H%d:H%d)" % (hrow + 1, last)).font = CELL_FONT

    # 3_実習記録
    prac = [
        ["1", "組織構造を理解する", "2〜3 の販売エリアの 3 キーの組み合わせを記録する。プラント→販売組織の割当を見つける", "", "", "", "", ""],
        ["2", "見積 → 受注伝票", "VA21 で見積を登録 → 後続機能で受注伝票（OR）を登録；納入日の確定と正味価額を記録", "", "", "", "", ""],
        ["3", "納入と出庫過転記", "VL01N で納入を登録 → VL02N でピッキング → 出庫過転記（601）；在庫の前後の数量を記録", "", "", "", "", ""],
        ["4", "請求と転記", "VF01 請求（F2）→ VF02 リリース；請求書番号、正味価額、会計伝票の借方/貸方を記録", "", "", "", "", ""],
        ["5", "追跡とレポート", "VA03 伝票フロー → VA05 受注一覧 → VL06O / VF04；3 つの伝票番号をチェーンとして記録", "", "", "", "", ""],
    ]
    sheet(wb, "3_実習記録", "3. 実習記録（印刷して実習室に持ち込める）",
          ["タスク", "タスク名", "何をするか", "伝票番号／キー値", "日付", "ステータス", "金額 / 数量", "つまずいたときの症状とエラー"],
          prac, [6, 18, 46, 24, 12, 16, 16, 40],
          note="進め方と完成基準はサイトの practice.html を参照してください。A4 横向きでの印刷を推奨します。")

    # 4_スクリーンショット索引
    rows = []
    idx = 0
    for f, label, tip in common.NAV:
        for p in pages[f]["shots"]:
            idx += 1
            rel = p.replace("assets/img/", "")
            task = re.match(r"(sd|prep)/t(\d+)/", rel)
            rows.append([idx, f, label, rel, ("タスク %s" % task.group(2)) if task else "準備の章",
                         rel.split("/")[-1], p])
    sheet(wb, "4_スクリーンショット索引", "4. スクリーンショット索引（実際の SAP GUI 画面）",
          ["#", "掲載ページ", "ナビゲーション名", "assets 内のパス", "教材タスク", "元ファイル名", "ページ参照"],
          rows, [5, 14, 10, 34, 12, 26, 34],
          note="元ファイル名 = 教材ドキュメント S4.docx に埋め込まれた画像の元の名前で、Word 原稿と 1 つずつ照合できます。")

    # 5_用語集
    rows = [[zh, en, code, desc] for zh, en, code, desc in p_admin.TERMS]
    sheet(wb, "5_用語集", "5. 用語集（中英対照）", ["中国語", "英語", "コード", "説明"], rows, [26, 40, 12, 60])

    # 6_Tcode
    rows = [[tc, desc, grp, src] for tc, desc, grp, src in p_admin.TCODES]
    sheet(wb, "6_Tcodeクイックリファレンス", "6. よく使う T-code", ["T-code", "使用目的", "段階", "教材タスク（タスク番号）"], rows, [22, 46, 10, 16])

    # 7_自作図一覧
    dias = {}
    for f, label, _t in common.NAV:
        for d in pages[f]["dias"]:
            dias.setdefault(d, []).append(label)
    rows = [[i, d.split("/")[-1], "、".join(v), d] for i, (d, v) in enumerate(sorted(dias.items()), 1)]
    sheet(wb, "7_自作図一覧", "7. 自作のフロー図 / 構造図 / マインドマップ",
          ["#", "ファイル", "どのページで使うか", "パス"], rows, [5, 24, 40, 40],
          note="すべて本コースの自作 SVG です（ベクターなので投影しても拡大してもぼやけません）。ページ上でクリックすると 4× まで拡大できます。")

    wb.save(OUT)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
