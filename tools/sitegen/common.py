# -*- coding: utf-8 -*-
"""SAP SD トレーニングコースサイト — 共通の骨組みとコンポーネント（共有デザインシステム style.css を再利用し、追記のみで上書きしない）。

設計方針は他のトレーニングサイトと共通です：
- 純粋な静的 HTML、外部依存なし、file:// で直接開ける
- 実際のスクリーンショットは教材ドキュメント由来（元のファイル名は figcaption に残しており、Word 原稿で確認可能）
- 生成した図（フロー図/構造図/マインドマップ）は assets/diagrams/*.svg にあり、ページ上で「自作図」と明示
"""
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# --------------------------------------------------------------------------
# サイトのメタ情報
# --------------------------------------------------------------------------
SITE = {
    "title": "SAP SD トレーニングコース",
    "subtitle": "販売管理：概念からプロセスへ、全体から部分へ",
    "brand_logo": "SD",
    "brand_txt": "トレーニングコース",
    "desc": "SAP SD（販売管理）トレーニングコース：概念 → 組織構造 → マスタ → 価格設定 → エンドツーエンドプロセス（引合・見積・受注・納入・出荷・請求・入金）→ 設定 → 分析。"
            "各段階に実際の SAP GUI システムのスクリーンショット（中国語インターフェース）と自作図のフロー図、構造図、マインドマップを用意します。",
}

# ナビゲーション（順序 = 教学順：概念 → 全体 → 部分 → 管理 → 実習）
NAV = [
    ("index.html", "ホーム", "コースマップと学習ルート"),
    ("concept.html", "基本概念", "SD とは何か、3 つの概念レイヤ、5 大伝票"),
    ("org.html", "組織", "企業構造 / 販売構造 / 出荷構造"),
    ("master.html", "マスタ", "得意先マスタ / 品目の販売ビュー / 条件レコード"),
    ("pricing.html", "価格設定", "条件技術の4要素と計算スキーマ決定"),
    ("flow.html", "プロセス", "エンドツーエンド O2C のフロー図と伝票フロー"),
    ("order.html", "受注伝票", "引合 · 見積 · 受注伝票（部分的な詳細解説）"),
    ("delivery.html", "納入", "出荷伝票 · ピッキング · 出庫過転記"),
    ("billing.html", "請求", "請求書 · FI への転記 · 入金"),
    ("analysis.html", "データ分析", "伝票フロー／受注一覧／販売分析"),
    ("config.html", "設定", "SPRO 設定ルート（48 タスク）"),
    ("practice.html", "実習", "実習タスクと完成基準"),
    ("instructor.html", "講師", "採点ポイント / 必ず問う質問 / 解答"),
    ("worksheet.html", "受講者", "記入表（印刷可能）"),
    ("quiz.html", "セルフチェックテスト", "30 問のセルフチェック（合格 75%）"),
    ("glossary.html", "用語", "中国語・英語対照 / T-code クイックリファレンス"),
]

IMG_MANIFEST = json.load(open(os.path.join(ROOT, "work", "img_manifest.json"), encoding="utf-8"))
CAPTURE = {
    "sd": "教材《S4.docx》SD モジュール",
    "prep": "教材《S4.docx》準備章",
}

# 教材原文の 48 個の SD タスク（タイトル / IMG パス / 手順 / スクリーンショット）—— ページ内のパスとスクリーンショットはすべてここから取り、
# ファイル名の手書き写し間違いを防ぎ、「サイトに書いたパス = 教材のパス」も保証する。
SD_SOURCE = json.load(open(os.path.join(ROOT, "work", "sd_source.json"), encoding="utf-8"))
TASK = {t["no"]: t for t in SD_SOURCE}


def simg(task, step=1, k=0):
    """教材の task 番目のタスク、step 番目のステップ、k 枚目のスクリーンショットのパスを返す。なければ None を返す。"""
    steps = TASK[task]["steps"]
    if not steps:
        return None
    imgs = steps[min(step, len(steps)) - 1].get("imgs") or []
    if not imgs:
        return None
    return imgs[min(k, len(imgs) - 1)]


def scap(task, step=1):
    steps = TASK[task]["steps"]
    if not steps:
        return ""
    return steps[min(step, len(steps)) - 1].get("caption", "")


def spath(task):
    return TASK[task].get("path") or ""


def stc(task):
    return TASK[task].get("tcodes") or []


def src_ref(task):
    return "教材《S4.docx》· SD タスク %02d %s" % (task, TASK[task]["title"])


# --------------------------------------------------------------------------
# 小さな部品
# --------------------------------------------------------------------------
def esc(s):
    return html.escape(str(s), quote=False)


def href(file, anchor=None):
    return file + ("#" + anchor if anchor else "")


def _img_attrs(path):
    m = IMG_MANIFEST.get(path)
    if not m:
        raise KeyError("スクリーンショットが manifest にありません（assets/img/%s）" % path)
    return m["w"], m["h"], m["orig"]


def shot(path, no=None, cap="", src="", cls="", alt=None):
    """実際のシステムのスクリーンショット（教材ドキュメントの原図）。path は assets/img/ からの相対パス。"""
    w, h, orig = _img_attrs(path)
    cap = cap or ""
    # 実際のスクリーンショット（教材ドキュメント由来）。「画面イメージ（＝生成した図）」とは書かない。
    tag = "画面 %s" % no if no else "画面"
    srctxt = src or ("%s · %s" % (CAPTURE.get(path.split("/")[0], "教材（テキスト）"), orig))
    narrow = " narrow" if h <= 160 else ""
    return (
        '<figure class="shot%s%s">'
        '<a class="zoom" href="assets/img/%s" title="クリックで拡大（1×〜4×、ESC で閉じる）">'
        '<img src="assets/img/%s" width="%d" height="%d" alt="%s" loading="lazy"></a>'
        '<figcaption><span class="n">%s</span><span class="cap">%s</span>'
        '<span class="src">%s</span></figcaption></figure>'
    ) % (narrow, (" " + cls if cls else ""), path, path, w, h,
         esc(alt or cap or "SAP GUI 実機スクリーンショット"), tag, cap, srctxt)


def shot_grid(items, cls=""):
    """items = [(path, cap, no)] -> 並べた小さい図。連続した画面に適しています。"""
    inner = "".join(shot(p, no=n, cap=c) for p, c, n in items)
    return '<div class="shot-grid%s">%s</div>' % (" " + cls if cls else "", inner)


def diagram(name, alt, cap="", kind="フロー図"):
    return (
        '<figure class="dia"><a class="zoom" href="assets/diagrams/%s.svg">'
        '<img src="assets/diagrams/%s.svg" alt="%s" loading="lazy"></a>'
        '<figcaption><span class="n">%s</span><span class="cap">%s</span>'
        '<span class="src">当サイト自作の SVG</span></figcaption></figure>'
    ) % (name, name, esc(alt), kind, cap)


def note(kind, title, text):
    return '<div class="note %s"><span class="t">%s</span>%s</div>' % (kind, esc(title), text)


def box(kind, title, inner):
    return '<div class="box %s"><b class="t">%s</b>%s</div>' % (kind, esc(title), inner)


def pathline(label, path, copyable=True):
    attr = ' data-copy="%s"' % esc(path) if copyable else ""
    return '<div class="pathline"%s><b>%s</b>%s</div>' % (attr, esc(label), esc(path))


def tbl(headers, rows, cls="tbl", first_mono=False, row_attrs=None, tid=None):
    th = "".join("<th>%s</th>" % h for h in headers)
    trs = []
    for i, r in enumerate(rows):
        tds = []
        for c in r:
            if isinstance(c, tuple):
                c, klass = c
            else:
                klass = ""
            tds.append('<td%s>%s</td>' % (' class="%s"' % klass if klass else "", c))
        ra = ""
        if row_attrs is not None and i < len(row_attrs) and row_attrs[i]:
            ra = " " + row_attrs[i]
        trs.append("<tr%s>%s</tr>" % (ra, "".join(tds)))
    klass = cls + (" idx" if first_mono else "")
    idattr = ' id="%s"' % tid if tid else ""
    return ('<div class="tblwrap"><table class="%s"%s><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>') % (klass, idattr, th, "".join(trs))


def oplist(items, start=1):
    """items = [(html, kind)] ; kind in ''|note"""
    lis = []
    for it in items:
        if isinstance(it, tuple):
            txt, kind = it
        else:
            txt, kind = it, ""
        lis.append('<li class="%s">%s</li>' % ("is-note" if kind == "note" else "", txt))
    return '<ol class="oplist" start="%d">%s</ol>' % (start, "".join(lis))


def steps_list(items):
    return '<ol class="steps">%s</ol>' % "".join("<li>%s</li>" % x for x in items)


def steph(no, title, tags=None, anchor=None):
    t = "".join('<span class="%s">%s</span>' % (k, esc(v)) for k, v in (tags or []))
    return '<div class="steph" id="%s"><span class="no">%s</span><h3>%s</h3>%s</div>' % (
        anchor or ("s" + str(no)), esc(no), esc(title), t)


def toc(items):
    return '<div class="toc">%s</div>' % "".join(
        '<a href="#%s">%s</a>' % (a, esc(t)) for t, a in items)


def cards(items):
    inner = "".join('<div class="card"><b>%s</b><span>%s</span></div>' % (b, s) for b, s in items)
    return '<div class="grid cards">%s</div>' % inner


def stat_cards(items):
    """[(数値, 単位, 説明)] -> 3 列の統計カード"""
    inner = ""
    for n, unit, desc in items:
        inner += '<div class="card"><b>%s</b><span>%s</span><small>%s</small></div>' % (n, unit, desc)
    return '<div class="grid cards stats">%s</div>' % inner


# --------------------------------------------------------------------------
# ページの骨組み（完全な文書の骨組み。組み立て時に skeleton を落とすという昔の問題を避ける）
# --------------------------------------------------------------------------
def nav_html(active):
    out = []
    for f, label, _tip in NAV:
        cls = ' class="active"' if f == active else ""
        out.append('<a%s href="%s" title="%s">%s</a>' % (cls, f, esc(_tip), esc(label)))
    return "\n      ".join(out)


def shell(file, title, kicker, body, desc=None):
    desc = desc or SITE["desc"]
    return """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%(title)s · %(stitle)s</title>
<meta name="description" content="%(desc)s">
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/sd.css">
</head>
<body>
<header class="site">
  <div class="nav-wrap">
    <a class="brand" href="index.html"><span class="logo">%(logo)s</span><span class="txt">%(btxt)s</span></a>
    <nav class="main">
      %(nav)s
    </nav>
  </div>
</header>

<div class="wrap">
<main class="page">
<article>
%(body)s
</article>
</main>
</div>

<footer class="site">
  <div class="inner">
    <div class="cols">
      <div>
<h5>SAP SD トレーニングコース</h5>
<p>販売管理 · 概念からプロセスへ · 全体から部分へ</p>
      </div>
      <div>
<h5>コースセクション</h5>
<p><a href="concept.html">概念</a> · <a href="org.html">組織</a> · <a href="master.html">マスタ</a> ·
<a href="pricing.html">価格設定</a> · <a href="flow.html">プロセス</a> · <a href="config.html">設定</a></p>
      </div>
      <div>
<h5>授業用付属資料</h5>
<p><a href="practice.html">実習タスク</a> · <a href="instructor.html">講師用</a> ·
<a href="worksheet.html">受講者用</a> · <a href="quiz.html">セルフチェックテスト</a> ·
<a href="glossary.html">用語集</a></p>
      </div>
      <div>
<h5>ひと言の免責</h5>
<p>スクリーンショットは教材ドキュメントの実際の SAP GUI 画面（中国語インターフェース）。図と表は当サイトの自作です。
標準値はリリース/業界ソリューションによって異なります。ページに記載の確認方法をご自身のシステムで確認してください。</p>
      </div>
    </div>
<p class="copy">© <span data-year>2026</span> SAP SD トレーニングコース · 静的サイト、オフラインで利用可能</p>
  </div>
</footer>
<script src="assets/main.js"></script>
<script src="assets/quiz.js"></script>
<script src="assets/sd.js"></script>
</body>
</html>
""" % {"title": esc(title), "stitle": SITE["title"], "desc": esc(desc),
       "logo": SITE["brand_logo"], "btxt": SITE["brand_txt"],
       "nav": nav_html(file), "body": body}


# ==========================================================================
# 日本語版の追加物（sap_jp_sd）— 原教材（中国語）を併記するための道具
#   ・日本語テキストは work/sd_source_ja.json（i18n.py が生成）
#   ・中国語原文は work/sd_source.json（原教材そのまま、照合用）
#   ・既存のページ生成コードは scap/spath/src_ref/pathline をそのまま呼ぶだけで
#     日本語表示になる（同じ名前で再定義しているため）
# ==========================================================================
SD_JA = json.load(open(os.path.join(ROOT, "work", "sd_source_ja.json"), encoding="utf-8"))
TASK_JA = {t["no"]: t for t in SD_JA}


def tja(task):
    return TASK_JA[task]


def tzh(task):
    return TASK[task]


def stitle(task):
    return TASK_JA[task]["title"]


def scap(task, step=1):
    steps = TASK_JA[task]["steps"]
    if not steps:
        return ""
    return steps[min(step, len(steps)) - 1].get("caption", "")


def scap_zh(task, step=1):
    steps = TASK[task]["steps"]
    if not steps:
        return ""
    return steps[min(step, len(steps)) - 1].get("caption", "")


def spath(task):
    return TASK_JA[task].get("path") or ""


def spath_zh(task):
    return TASK[task].get("path") or ""


def src_ref(task):
    return "教材《S4.docx》・SD タスク %02d %s" % (task, stitle(task))


def txt(t):
    """改行を保持したままエスケープ（原文併記用）。"""
    return esc(t).replace("\n", "<br>")


def orig(text, label="原文（中国語）"):
    """原教材の中国語テキストを折りたたんで併記する（照合用）。"""
    if not (text or "").strip():
        return ""
    return ('<details class="orig"><summary>%s</summary><div class="zh">%s</div></details>'
            % (esc(label), txt(text)))


def cap_ja(text):
    """手順キャプション → HTML（「解説：」の導入語にマークを付ける）。"""
    c = (text or "").strip()
    if not c:
        return ""
    m = re.match(r"^(解説|説明|注意)\s*[：:]\s*(.*)$", c, re.S)
    if m:
        return '<span class="lead">%s</span> %s' % (esc(m.group(1)), txt(m.group(2)))
    return txt(c)


def step_items(task, ja_steps, zh_steps):
    """手順要点の <li> 用: 日本語キャプション ＋「原文（中国語）」の折りたたみ。

    ja_steps / zh_steps は同じ並び（インデックス一致）。画面が中国語なので、
    ステップ単位で原文を照合できるようにしておく（教材 Word との突き合わせ用）。
    """
    out = []
    for i, s in enumerate(ja_steps):
        cap = (s.get("caption") or "").strip()
        if not cap:
            continue
        zcap = (zh_steps[i].get("caption") or "").strip() if i < len(zh_steps) else ""
        html = cap_ja(cap)
        if zcap and zcap != cap:
            html += orig(zcap, "原文（中国語）")
        out.append((html, "note" if cap.startswith(("解説", "説明")) else ""))
    return out


# --- 中国語パスの逆引き（日本語パス → 原教材の中国語パス） -------------------
PATH_ZH = {}
for _n, _t in TASK_JA.items():
    _j, _z = (_t.get("path") or "").strip(), (TASK[_n].get("path") or "").strip()
    if _j and _z and _j != _z:
        PATH_ZH[_j] = _z


def _path_zh(path):
    p = (path or "").strip()
    if p in PATH_ZH:
        return PATH_ZH[p]
    if "｜" in p:
        parts = [x.strip() for x in p.split("｜")]
        zs = [PATH_ZH.get(x) for x in parts]
        if any(zs):
            return "　｜　".join(z if z else x for x, z in zip(parts, zs))
    return ""


def pathline(label, path, copyable=True):
    """IMG パス行（日本語）＋ 原教材の中国語パス行。コピーは中国語側を渡す。"""
    zh = _path_zh(path)
    attr = ' data-copy="%s"' % esc(zh or path) if copyable else ""
    out = '<div class="pathline"%s><b>%s</b>%s</div>' % (attr, esc(label), esc(path))
    if zh:
        out += ('<div class="pathzh"><b>原教材の中国語パス</b><code>%s</code></div>'
                % esc(zh))
    return out
