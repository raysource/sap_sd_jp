# -*- coding: utf-8 -*-
"""コース用のフロー図 / 構造図 / マインドマップを生成します（純 Python → SVG。外部依存なし、オフラインで利用可能）。

なぜ手書き SVG か：サイトは file:// で直接開けること、ネット接続不要、CDN フォント不要が要件だからです；同時に
文字幅は CJK 全角 1.0em で見積もる必要があります。そうしないと中国語が枠からあふれます（これは別のサイトでつまずいた点）。

使い方:  python3 tools/make_diagrams.py            # assets/diagrams/*.svg
python3 tools/make_diagrams.py --check     # XML が合法か + 文字が溢れていないかだけをチェック
"""
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "assets", "diagrams")

BLUE, BLUE_D, BLUE_L = "#0a6ed1", "#0854a0", "#e3f0fa"
TEAL, TEAL_B = "#007272", "#e6f2f2"
AMBER, AMBER_B = "#8d6e00", "#fdf3d7"
GREEN, GREEN_B = "#177245", "#e6f2ec"
RED, RED_B = "#b3261e", "#fdeae9"
INK, INK2, MUTED, LINE = "#1d2d3e", "#354a5f", "#6b7a8d", "#d9e1e8"
FONT = "'PingFang SC','Hiragino Sans GB','Noto Sans CJK SC','Microsoft YaHei',sans-serif"
MONO = "'SF Mono',Menlo,Consolas,monospace"


# --------------------------------------------------------------------------
# テキストの幅の見積もり（CJK 全角 1.0em / 半角は約 0.55em）—— 他のサイトと共通の教訓
# --------------------------------------------------------------------------
def char_w(ch):
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 1.0
    if ch in "iljI.,:;'|! ":
        return 0.32
    if ch in "mMW@":
        return 0.9
    return 0.575


def text_w(s, size):
    return sum(char_w(c) for c in s) * size


def wrap(s, size, maxw, max_lines=None):
    """表示幅で折り返す（CJK は任意の位置で折り返し可、ASCII の語はまとめて移動）。"\n" は強制改行として扱う。"""
    if "\n" in s:
        out = []
        for part in s.split("\n"):
            out.extend(wrap(part, size, maxw))
        if max_lines and len(out) > max_lines:
            out = out[:max_lines]
            out[-1] = out[-1][: max(1, len(out[-1]) - 1)] + "…"
        return out
    words, cur, lines = [], "", []
    for ch in s:
        if ch == " ":
            words.append(cur)
            words.append(" ")
            cur = ""
        else:
            cur += ch
    words.append(cur)
    line = ""
    for w in words:
        if text_w(line + w, size) <= maxw:
            line += w
        else:
            if line:
                lines.append(line.rstrip())
            while text_w(w, size) > maxw and len(w) > 1:
                k = 1
                while k < len(w) and text_w(w[: k + 1], size) <= maxw:
                    k += 1
                lines.append(w[:k])
                w = w[k:]
            line = w
    if line.strip():
        lines.append(line.rstrip())
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: max(1, len(lines[-1]) - 1)] + "…"
    return lines


# --------------------------------------------------------------------------
# SVG の基本部品
# --------------------------------------------------------------------------
def svg_open(w, h, title):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
        'role="img" aria-label="%s" font-family="%s">\n'
        '<title>%s</title>\n'
        '<defs>'
        '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
        '<marker id="ar2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
        '<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#ffffff"/></marker>'
        '</defs>\n<rect width="%d" height="%d" fill="#ffffff"/>\n'
    ) % (w, h, w, h, title, FONT, title, BLUE, TEAL, w, h)


def t(x, y, s, size=13.0, fill=INK, anchor="start", weight="400", family=None, opacity=None):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    fam = " font-family=\"%s\"" % family if family else ""
    op = ' opacity="%s"' % opacity if opacity else ""
    return '<text x="%.1f" y="%.1f" font-size="%s" fill="%s" text-anchor="%s" font-weight="%s"%s%s>%s</text>\n' % (
        x, y, size, fill, anchor, weight, fam, op, s)


def rect(x, y, w, h, fill="#ffffff", stroke=LINE, rx=8, sw=1.4, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" stroke="%s" stroke-width="%s"%s/>\n' % (
        x, y, w, h, rx, fill, stroke, sw, d)


def line(x1, y1, x2, y2, stroke=MUTED, sw=1.4, dash=None, marker=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#%s)"' % marker if marker else ""
    return '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"%s%s/>\n' % (
        x1, y1, x2, y2, stroke, sw, d, m)


def path(d, stroke=MUTED, sw=1.6, fill="none", dash=None, marker=None):
    da = ' stroke-dasharray="%s"' % dash if dash else ""
    m = ' marker-end="url(#%s)"' % marker if marker else ""
    return '<path d="%s" fill="%s" stroke="%s" stroke-width="%s"%s%s/>\n' % (d, fill, stroke, sw, da, m)


def badge(cx, cy, label, fill=BLUE, r=11, size=12, tcolor="#ffffff"):
    return ('<circle cx="%.1f" cy="%.1f" r="%s" fill="%s"/>' % (cx, cy, r, fill)
            + t(cx, cy + 4.3, label, size, tcolor, "middle", "700"))


def node(x, y, w, h, title, lines, accent=BLUE, bg="#ffffff", badge_txt=None,
         title_size=14.5, body_size=12, mono_lines=()):
    """標準ボックス：タイトル + 本文行。幅に応じて自動で折り返し、高さも自動調整します。"""
    pad = 12
    out = [rect(x, y, w, h, bg, accent, 9)]
    out.append(rect(x, y, 4.5, h, accent, accent, rx=2))
    ty = y + 22
    out.append(t(x + pad, ty, title, title_size, accent if bg == "#ffffff" else accent,
                 weight="700"))
    cy = ty + 19
    for ln in lines:
        for seg in wrap(ln, body_size, w - 2 * pad, 3):
            out.append(t(x + pad, cy, seg, body_size, INK2))
            cy += body_size + 5.5
    for ln in mono_lines:
        out.append(t(x + pad, cy, ln, 11, MUTED, family=MONO))
        cy += 16
    if badge_txt:
        out.append(badge(x + w - 14, y + 14, badge_txt, accent, r=11))
    return "".join(out), cy


def arrow(x1, y1, x2, y2, color=BLUE, sw=1.8, dash=None, marker="ar"):
    return line(x1, y1, x2, y2, color, sw, dash, marker)


def chain(x, y, items, color=BLUE, avail=460, size=11, rowh=44):
    """横方向のプロセスチェーン。使用可能な幅を超えたら自動的に次の行へ折り返します。戻り値は (svg, 占有高さ)。

矢印は同じ行の隣り合う 2 項目の間だけに引きます。改行部分には折り返しの小さな矢印を 1 つ描き、次のような状態を避けます
「空白を指す」矢印。
    """
    widths = [text_w(it, size) + 22 for it in items]
    # まずレイアウトを決める（各要素が何行目に来るか、x 位置）
    pos, cx_, cy_, rows = [], x, y, 1
    for i, w in enumerate(widths):
        if cx_ + w > x + avail and cx_ > x:
            cx_, cy_, rows = x, cy_ + rowh, rows + 1
        pos.append((cx_, cy_, w))
        cx_ += w + 18
    out = []
    for i, ((px, py, w), it) in enumerate(zip(pos, items)):
        out.append(rect(px, py, w, 34, "#ffffff", color, 8, 1.2))
        out.append(t(px + 11, py + 22, it, size, INK2))
        if i < len(items) - 1:
            nx, ny, _nw = pos[i + 1]
            if ny == py:                       # 同じ行：まっすぐな矢印
                out.append(arrow(px + w + 1, py + 17, nx - 3, py + 17, color, 1.3))
            else:                              # 改行時：次の行の先頭のボックスへ折り返す（矢印が空白を指さないように）
                sx = px + w + 1
                d = "M %.0f %.0f h 10 v %d h %.0f h 12" % (sx, py + 17, rowh, -(sx + 10 - (x - 14)))
                out.append(path(d, stroke=color, sw=1.3, marker="ar"))
    return "".join(out), rows * rowh + 6


def arrow_lr(x1, y1, x2, y2, color=BLUE, sw=1.8, dash=None):
    """水平の両方向矢印（統合関係用）。"""
    return line(x1, y1, x2, y2, color, sw, dash, "ar")


def note_bar(x, y, w, text, fill=BLUE_L, stroke=BLUE, size=12.5):
    lines = wrap(text, size, w - 24)
    h = 14 + len(lines) * (size + 6)
    out = [rect(x, y, w, h, fill, stroke, 8, 1.2)]
    cy = y + 20
    for ln in lines:
        out.append(t(x + 12, cy, ln, size, BLUE_D if stroke == BLUE else INK2))
        cy += size + 6
    return "".join(out), y + h


def title_bar(x, y, w, main, sub=None, size=20):
    out = [t(x, y, main, size, INK, weight="700")]
    if sub:
        out.append(t(x, y + 22, sub, 13, MUTED))
    return "".join(out)


# --------------------------------------------------------------------------
# 1. マインドマップ — コース知識マップ（全体 → 部分）
# --------------------------------------------------------------------------
def mindmap():
    W, H = 1420, 1240
    s = [svg_open(W, H, "SAP SD 知識マップ（マインドマップ）")]
    s.append(t(40, 46, "SAP SD 知識マップ — 全体から部分へ", 22, INK, weight="700"))
    s.append(t(40, 70, "6 つのセクション：① 概念 ② 組織 ③ マスタ ④ 価格設定 ⑤ プロセス ⑥ 設定と分析。葉ノード = コースの要点（当サイト自作 SVG）", 12.5, MUTED))

    cx, cy = 710, 660
    CW = 240
    s.append(rect(cx - CW / 2, cy - 75, CW, 150, BLUE_D, BLUE_D, 16))
    s.append(t(cx, cy - 22, "SAP SD", 32, "#ffffff", "middle", "700"))
    s.append(t(cx, cy + 10, "販売管理", 18, "#dbeafd", "middle"))
    s.append(t(cx, cy + 36, "Sales & Distribution", 12, "#a9cdf3", "middle", family=MONO))
    s.append(t(cx, cy + 60, "地図 → プロセス → 設定", 11.5, "#a9cdf3", "middle"))

    branches = [
        # (タイトル, 色, 方向, 葉ノード)
        ("① 概念と位置づけ", BLUE, "L", [
            "SD が担う範囲：何を売るか · 誰に売るか · どう価格設定するか · どう出荷するか · どう請求するか",
            "FI / MM / PP / CO との境界：SD は「販売伝票」を出し、隣接モジュールが在庫と会計伝票を出します",
            "3 つの概念層：組織構造 → マスタ → 伝票（設定の順序も同じです）",
            "5 大伝票：引合 · 見積 · 受注伝票 · 納入 · 請求書",
            "中核となる組織キー：販売エリア = 販売組織 + 流通チャネル + 製品部門",
        ]),
        ("② 組織構造", TEAL, "L", [
            "企業構造：会社コード / 販売組織 / プラント",
            "販売構造：流通チャネル / 製品部門 / 販売事務所 / 販売グループ",
            "出荷構造：出荷ポイント / 積込ポイント / ピッキング保管場所 / 輸送条件",
            "割当関係は多くが多対多です（1 つのプラントは複数の販売組織に対応でき、1 つの出荷ポイントは複数のプラントにサービスできます）",
            "組織データが決めること：マスタの作り方、伝票の流れ方、在庫の出所、収益の計上方法",
        ]),
        ("③ マスタ", GREEN, "L", [
            "得意先マスタの 3 層：一般データ／会社コードデータ／販売エリアデータ",
            "4 つのパートナ役割：受注先 · 出荷先 · 請求先 · 支払先（同一得意先の別番号を指すことも可能）",
            "品目マスタ：販売ビュー（販売エリアレベル）+ プラントレベルビュー（MRP など）",
            "条件レコード：販売価格 PR00 / 割引 / 売上税 MWST など（VK11 で登録）",
            "得意先-品目情報レコード · 品目決定（リストと除外）· 得意先勘定グループ",
        ]),
        ("④ 価格設定と条件技術", AMBER, "R", [
            "4 層構造：条件テーブル → アクセス順序 → 条件タイプ → 計算スキーマ",
            "条件タイプ PR00（価格）/ MWST（売上税）/ 割引と追加料金（教材は RVAA01 標準スキーマを使用）",
            "アクセス順序は「まず専用価格を探し、見つからなければ一般価格を探す」という検索の優先順位を決定します",
            "計算スキーマ決定の 3 つのキー：販売エリア＋得意先計算スキーマ＋伝票計算スキーマ",
            "勘定設定：勘定キー + 品目/得意先の勘定割当グループ → 収益勘定（VKOA）",
        ]),
        ("⑤ 業務プロセス O2C", RED, "R", [
            "販売前：引合 VA11 → 見積 VA21（参照して登録可能）",
            "受注：受注伝票 VA01 —— 価格設定 + 所要量確認 ATP → 納入日の確定",
            "納入：出荷伝票 VL01N → ピッキング → 出庫過転記 VL02N（移動タイプ 601 で初めて実際に出庫）",
            "請求：請求書 VF01 → 転記 VF02 → 会計伝票 → 入金 F-28 消込",
            "モニタリング：伝票フロー（VA03 → 環境）/ 受注一覧 VA05 / 販売分析 MCTA",
        ]),
        ("⑥ 設定と分析", "#5b3fa8", "R", [
            "SPRO ルート：組織 → 出荷 → マスタデータ → 価格設定 → 勘定設定 → 更新グループ",
            "伝票制御オブジェクト：販売伝票タイプ／明細カテゴリ／納入日程行カテゴリ（VOV4／VOV5／VOV7）",
            "チェックとルール：不完全性チェック OVA2、与信管理、パートナ決定",
            "出力決定：受注確認 / 納入伝票 / 請求書の出力と印刷",
            "分析：VC/2 販売集計、VA05 受注一覧、MCTA 販売分析、貸借対照表",
        ]),
    ]
    left = [b for b in branches if b[2] == "L"]
    right = [b for b in branches if b[2] == "R"]
    LEAF_W = 480
    LEAF_H = 46
    HEAD_W = 200
    HEAD_H = 42
    LEFT_X = 40                      # 左側のブランチ：葉ノードもブランチ見出しも左寄せ、ブランチ見出しは右端を INNER_L に揃える
    INNER_L = LEFT_X + LEAF_W        # 520
    HEAD_X_L = INNER_L - HEAD_W      # 320
    RIGHT_X = 900                    # 右側のブランチ：葉ノードもブランチ見出しも右寄せ
    band_top = 108
    band_h = (H - band_top - 40) / 3.0

    def draw_branch(idx, title, color, direction, leaves):
        y0 = band_top + idx * band_h
        hy = y0
        lx = LEFT_X if direction == "L" else RIGHT_X
        hx = HEAD_X_L if direction == "L" else RIGHT_X
        # ブランチ見出し（色付きのカプセル）
        s.append(rect(hx, hy, HEAD_W, HEAD_H, color, color, 12))
        s.append(t(hx + HEAD_W / 2, hy + 28, title, 16, "#ffffff", "middle", "700"))
        # 中心 → ブランチ見出し：中央のすき間だけを通し、葉ノードのボックスを横切らないようにする
        y1 = cy - 48 + idx * 24
        if direction == "L":
            x0, x1 = cx - CW / 2, hx + HEAD_W
            c1, c2 = x0 - 46, x1 + 46
        else:
            x0, x1 = cx + CW / 2, hx
            c1, c2 = x0 + 46, x1 - 46
        s.append(path("M %.0f %.0f C %.0f %.0f %.0f %.0f %.0f %.0f"
                      % (x0, y1, c1, y1, c2, hy + HEAD_H / 2, x1, hy + HEAD_H / 2),
                      stroke=color, sw=2.6))
        # 葉ノード（ブランチ見出しとは短い折れ線でつなぐ）
        n = len(leaves)
        total = n * LEAF_H + (n - 1) * 9
        ly = y0 + HEAD_H + 12
        for leaf in leaves:
            s.append(rect(lx, ly, LEAF_W, LEAF_H, "#ffffff", color, 8, 1.2))
            lines = wrap(leaf, 12.5, LEAF_W - 24, 2)
            for i, seg in enumerate(lines):
                s.append(t(lx + 12, ly + (29 if len(lines) == 1 else 20 + i * 16), seg, 12.5, INK2))
            if direction == "L":
                s.append(line(lx + LEAF_W, ly + LEAF_H / 2, hx + HEAD_W / 2, hy + HEAD_H, color, 1.2))
            else:
                s.append(line(lx, ly + LEAF_H / 2, hx + HEAD_W / 2, hy + HEAD_H, color, 1.2))
            ly += LEAF_H + 9

    for i, b in enumerate(left):
        draw_branch(i, b[0], b[1], "L", b[3])
    for i, b in enumerate(right):
        draw_branch(i, b[0], b[1], "R", b[3])
    s.append("</svg>\n")
    return "mindmap.svg", "".join(s)


# --------------------------------------------------------------------------
# 2. 組織構造図（構造図）
# --------------------------------------------------------------------------
def org_structure():
    W, H = 1360, 820
    s = [svg_open(W, H, "SAP SD 組織図")]
    s.append(title_bar(40, 48, W - 80, "SD 組織構造（企業構造 → 販売構造 → 出荷構造）",
                       "同じ組織データが、マスタの作り方、伝票の流れ方、在庫の出所、収益の記帳方法を同時に決定します（当サイトの自作図）"))

    def box(x, y, w, h, title, sub="", color=BLUE, bg="#ffffff", mono=None):
        s.append(rect(x, y, w, h, bg, color, 9))
        s.append(rect(x, y, 4.5, h, color, color, rx=2))
        s.append(t(x + 12, y + 22, title, 14, color, weight="700"))
        yy = y + 40
        for ln in wrap(sub, 11.5, w - 24, 3):
            s.append(t(x + 12, yy, ln, 11.5, INK2))
            yy += 16
        if mono:
            s.append(t(x + 12, yy + 2, mono, 10.5, MUTED, family=MONO))
        return yy

    # A 会社構造
    s.append(t(60, 110, "A. 企業構造（Enterprise Structure）", 15, BLUE_D, weight="700"))
    box(60, 122, 300, 74, "会社コード / 会社", "財務諸表と会計の最小単位", BLUE_D, BLUE_L)
    box(60, 216, 300, 74, "販売組織 (Sales Organization)", "販売を担当する法的単位：製品責任、販売統計", BLUE, "#ffffff")
    box(60, 310, 300, 74, "プラント (Plant)", "生産/保管場所が属する組織単位（出荷はここから発生する）", TEAL, "#ffffff")
    box(60, 404, 300, 74, "購買組織 / 出荷ポイントの調整", "モジュール横断で共用：SD はプラントと在庫だけを気にする", MUTED, "#f7fafc")

    # A→B の接続線
    s.append(path("M 210 196 L 210 216", BLUE))
    s.append(path("M 210 290 L 210 310", TEAL))
    s.append(path("M 210 384 L 210 404", MUTED))
    s.append(arrow(360, 160, 470, 160, BLUE))
    s.append(path("M 360 253 L 470 253", BLUE))

    # B 販売構造
    s.append(t(480, 110, "B. 販売構造（Sales Structure）", 15, TEAL))
    box(480, 122, 250, 74, "流通チャネル", "製品が得意先にどう届くか：直販 / 卸売 / 小売", TEAL, "#ffffff")
    box(480, 216, 250, 74, "製品部門", "製品をライン別にグループ化：完成品 / スペアパーツ / サービス", TEAL, "#ffffff")
    box(480, 310, 250, 74, "販売事務所", "地理的／責任範囲（地域で区分された販売組織）", TEAL, "#ffffff")
    box(480, 404, 250, 74, "販売グループ", "販売事務所の中の担当者グループ（責任分担）", TEAL, "#ffffff")
    s.append(path("M 605 290 L 605 310", TEAL))
    s.append(arrow(730, 160, 830, 160, TEAL))
    s.append(path("M 730 253 L 830 253", TEAL))
    s.append(path("M 730 347 L 830 347", TEAL))

    # C 販売エリア = 3 つのキーの組み合わせ
    s.append(t(840, 110, "C. 販売エリア = 販売組織 + 流通チャネル + 製品部門", 15, "#5b3fa8"))
    s.append(rect(840, 122, 460, 116, "#f4f0ff", "#5b3fa8", 10))
    s.append(t(856, 148, "販売エリア（Sales Area）", 15, "#5b3fa8", weight="700"))
    for i, ln in enumerate(wrap("業務上の意味：ある販売組織が「ある流通チャネルを通じて」「ある製品部門」を扱う、ということです。"
                                "得意先マスタ、品目マスタ（販売ビュー）、条件レコード、すべての販売伝票の組織キーを決定します。"
                                "計算スキーマ決定、勘定設定の入力にもなります。", 11.5, 430, 4)):
        s.append(t(856, 168 + i * 16, ln, 11.5, INK2))
    s.append(rect(840, 250, 460, 84, GREEN_B, GREEN, 10))
    s.append(t(856, 274, "例（教材シナリオ 颐宁）", 13, GREEN, weight="700"))
    for i, ln in enumerate(wrap("1 つの販売組織 × 2 つの流通チャネル（直販 / 卸売）× 2 つの製品部門 → 4 つの販売エリアを、1 つずつ設定します。",
                                11.5, 430, 2)):
        s.append(t(856, 294 + i * 16, ln, 11.5, INK2))
    s.append(rect(840, 346, 460, 84, BLUE_L, BLUE, 10))
    s.append(t(856, 370, "販売事務所 / 販売グループ", 13, BLUE_D, weight="700"))
    for i, ln in enumerate(wrap("販売エリアへの割当（カスタマイジング）：統計と権限に使用され、単価の決定には影響しません。", 11.5, 430, 2)):
        s.append(t(856, 390 + i * 16, ln, 11.5, INK2))

    # D 出荷構造
    s.append(t(60, 520, "D. 出荷構造（Shipping）", 15, TEAL))
    shp = [
        (60, "出荷ポイント", "出荷の起点（プラントと多対多）\n教材例：Z999 颐宁出荷ポイント"),
        (290, "積込ポイント", "積み込みの具体的な位置（出荷ポイントごとに割当）"),
        (520, "ピッキング保管場所", "どの保管場所からピッキングするか（出荷ポイント + プラント + 保管条件で決定）"),
        (750, "輸送条件", "納入の輸送方式と時間（品目 / プラントとともに出荷ポイントを決定）"),
        (980, "積込グループ", "品目マスタと共同で積込ポイントを決定"),
    ]
    for x, ti, sub in shp:
        s.append(rect(x, 532, 210, 96, "#ffffff", TEAL, 9))
        s.append(rect(x, 532, 4.5, 96, TEAL, TEAL, rx=2))
        s.append(t(x + 12, 554, ti, 14, TEAL, weight="700"))
        yy = 572
        for ln in sub.split("\n"):
            for seg in wrap(ln, 11.5, 186, 2):
                s.append(t(x + 12, yy, seg, 11.5, INK2))
                yy += 15
    s.append(arrow(255, 580, 290, 580, TEAL))
    s.append(arrow(485, 580, 520, 580, TEAL))
    s.append(arrow(715, 580, 750, 580, TEAL))
    s.append(arrow(945, 580, 980, 580, TEAL))

    # 派生チェーン（下部）
    s.append(rect(60, 656, 1240, 124, "#f7fafc", LINE, 10))
    s.append(t(76, 682, "システムがこれらの組織データをどう自動的に見つけるか（自動決定のチェーン）", 14, INK, weight="700"))
    chain = [
        "得意先マスタ（販売エリア層の得意先）", "販売伝票タイプ（例：OR 標準受注）", "品目の品目マスタを入力する",
        "プラント / 出荷ポイント", "ピッキング保管場所",
    ]
    x = 76
    for i, c in enumerate(chain):
        w = text_w(c, 11.5) + 22
        s.append(rect(x, 700, w, 34, "#ffffff", BLUE, 8, 1.2))
        s.append(t(x + 11, 722, c, 11.5, INK2))
        x += w + 6
        if i < len(chain) - 1:
            # 矢印はボックスの外側 6px から描き始め、「線の端がボックスの内側から出ている」ように見えるのを避ける
            s.append(arrow(x + 2, 717, x + 14, 717, BLUE, 1.6))
            x += 20
    for i, ln in enumerate(wrap("要点：組織データは「毎回手入力」するものではありません。伝票ヘッダ/明細の販売エリアは得意先マスタから引き継がれ、"
                                "プラントは品目マスタと輸送条件から導出され、保管場所はカスタマイジングの設定で決まります。設定を誤ると、伝票が流れないか、誤った在庫に流れてしまいます。",
                                12, 1200, 2)):
        s.append(t(76, 752 + i * 18, ln, 12, INK2))
    s.append("</svg>\n")
    return "org-structure.svg", "".join(s)


# --------------------------------------------------------------------------
# 3. SD と他モジュールの統合（構造図）
# --------------------------------------------------------------------------
def integration():
    W, H = 1300, 660
    s = [svg_open(W, H, "SD と FI / MM / PP / CO の統合を示す構造図")]
    s.append(title_bar(40, 48, W - 80, "SD と他モジュールの統合（データがどこへ流れるかを 1 枚の図で）",
                       "SD が担うのは「販売」だけ。実際に在庫を引き当て、収益を計上し、生産を動かすのは隣接モジュールです（当サイトの自作図）"))
    # 中心
    s.append(rect(500, 300, 300, 150, BLUE_D, BLUE_D, 14))
    s.append(t(650, 348, "SD 販売管理", 22, "#ffffff", "middle", "700"))
    s.append(t(650, 376, "受注伝票 · 納入 · 請求書", 13.5, "#dbeafd", "middle"))
    s.append(t(650, 400, "VA01 / VL01N / VF01", 12, "#a9cdf3", "middle", family=MONO))
    s.append(t(650, 424, "駆動されるのは SD 自身の伝票だけです", 11.5, "#a9cdf3", "middle"))

    def mod(x, y, w, h, title, sub, tcodes, color, lines, side):
        s.append(rect(x, y, w, h, "#ffffff", color, 11))
        s.append(rect(x, y, 4.5, h, color, color, rx=2))
        s.append(t(x + 14, y + 26, title, 16, color, weight="700"))
        s.append(t(x + 14, y + 46, sub, 11.5, MUTED))
        yy = y + 68
        for ln in lines:
            for seg in wrap(ln, 11.5, w - 28, 2):
                s.append(t(x + 14, yy, seg, 11.5, INK2))
                yy += 16
        s.append(t(x + 14, y + h - 12, tcodes, 11, color, family=MONO))
        # 矢印
        if side == "left":
            s.append(line(x + w, y + h / 2, 500, 375, color, 2.0, None, "ar"))
            s.append(line(500, 400, x + w, y + h / 2 + 22, color, 1.6, "4 3", "ar"))
        else:
            s.append(line(x, y + h / 2, 800, 375, color, 2.0, None, "ar"))
            s.append(line(800, 400, x, y + h / 2 + 22, color, 1.6, "4 3", "ar"))

    mod(60, 140, 380, 140, "MM 資材管理", "在庫と購買", "MB1C / MIGO / MB52 / MD04", TEAL,
        ["出庫過転記 601 で初めて在庫が減ります（SD は納入するだけで在庫を減らしません）",
         "在庫なし → 納入伝票を作成できない（教材では MB1C 501 で期首在庫を入力して解決）",
         "購買入庫 101 は有効在庫を増やし、受注伝票の所要量確認の結果に影響します"], "left")
    mod(60, 420, 380, 140, "FI 財務会計", "売掛金 / 収益 / 税", "FS00 / VKOA / F-28 / FBL5N", "#5b3fa8",
        ["請求書の転記（VF02）で会計伝票を生成：借方 得意先売掛金／貸方 収益＋売上税",
         "勘定は VKOA「勘定設定」+ 品目/得意先の勘定割当グループで導出される",
         "入金 F-28 で売掛金を消し込み、FBL5N で得意先未消込項目を確認できます"], "left")
    mod(860, 140, 380, 140, "PP 生産計画", "所要量伝達と供給", "MD04 / MD01N / CO01 / MD61", AMBER,
        ["受注明細の所要量タイプ/所要量カテゴリが所要量を MRP（MD04）へ伝達する",
         "MTO シナリオ：所要量は「個別得意先在庫」に入り、自由在庫には入りません",
         "MTS シナリオ：まず計画独立所要量（MD61）があり、受注伝票は予測を消費するだけ"], "right")
    mod(860, 420, 380, 140, "CO 管理会計", "収益と原価対象", "KKA2 / CJ88 / VA88 / KO88", GREEN,
        ["収益は勘定設定に従って CO-PA 利益分析（収益エレメント）に入ります",
         "ETO/プロジェクトシナリオ：収益は WBS に、決済は CJ88 など",
         "原価対象が限界利益の計算方法を決定"], "right")

    s.append(rect(470, 470, 360, 118, "#f7fafc", LINE, 10))
    s.append(t(488, 496, "共通の「技術基盤」", 14, INK, weight="700"))
    for i, ln in enumerate(wrap("組織データ（会社コード / プラント / 販売組織）、マスタ（得意先 / 品目）、"
                                "番号範囲、伝票フロー——SD と隣接モジュールは同じデータを読むため、設定の順序は"
                                "「まず組織、次にマスタ、最後に伝票」。", 11.5, 324, 4)):
        s.append(t(488, 516 + i * 16, ln, 11.5, INK2))
    s.append("</svg>\n")
    return "integration.svg", "".join(s)


# --------------------------------------------------------------------------
# 4. 価格設定条件技術（構造図）
# --------------------------------------------------------------------------
def pricing_chain():
    W, H = 1340, 900
    s = [svg_open(W, H, "条件技術と計算スキーマ決定（構造図）")]
    s.append(title_bar(40, 48, W - 80, "価格設定の 4 層構造：条件テーブル → アクセス順序 → 条件タイプ → 計算スキーマ",
                       "「価格はどこから来るのか」は SD で最もよく聞かれる質問です。この 4 層がそれに答え、5 番目のステップが「どのスキーマを使うか」を決めます（当サイト自作図）"))

    # 4 つの層
    layers = [
        (1, "条件テーブル Condition Table", BLUE, "「具体的な価格」を保存します。行 = キーの組み合わせ（得意先／品目／販売組織…）、値 = 金額またはパーセント。",
         "教材シナリオ：PR00 のアクセス順序には「承認ステータスを持つ品目」などのステップが含まれます"),
        (2, "アクセス順序 Access Sequence", TEAL, "複数の条件テーブルを優先順位順に並べます。システムは最初のステップから検索し、見つかった時点で停止します（見つからない場合のみ次へ進みます）。",
         "意味：まずその得意先専用の価格を探し、次にその品目の一般価格を探す → …"),
        (3, "条件タイプ Condition Type", AMBER, "価格、割引、運賃、税…はいずれも条件タイプです。条件タイプがアクセス順序、計算ルール、勘定キーを導きます。",
         "PR00 = 販売価格 / MWST = 売上税 / K004 系の割引と追加料金"),
        (4, "計算スキーマ Pricing Procedure", "#5b3fa8", "条件タイプをステップ順に1つの表に並べます：ステップ → 条件タイプ → 計算タイプ → 勘定キー → 小計。",
         "教材のシナリオ：RVAA01「標準」はシステムの定義済み設定で、コースで使用する計算スキーマ"),
    ]
    y = 108
    for n, title, color, desc, ex in layers:
        s.append(rect(60, y, 560, 118, "#ffffff", color, 10))
        s.append(rect(60, y, 4.5, 118, color, color, rx=2))
        s.append(badge(84, y + 24, str(n), color, 12))
        s.append(t(106, y + 29, title, 16, color, weight="700"))
        yy = y + 52
        for ln in wrap(desc, 12, 520, 3):
            s.append(t(78, yy, ln, 12, INK2))
            yy += 17
        s.append(t(78, y + 106, ex, 11, MUTED))
        y += 134
    # 右向きの矢印
    for i in range(3):
        s.append(arrow(620, 167 + i * 134, 660, 167 + i * 134, MUTED, 1.6))
    s.append(t(668, 140, "階層ごとの参照：条件タイプはアクセス順序を参照し、", 12, MUTED))
    s.append(t(668, 158, "計算スキーマは条件タイプを参照", 12, MUTED))
    s.append(t(668, 274, "アクセス順序は条件テーブルを参照", 12, MUTED))
    s.append(t(668, 408, "スキーマに勘定キーがある → 転記勘定を決定する", 12, MUTED))

    # 右側：計算スキーマ決定 + 勘定設定
    s.append(rect(660, 108, 620, 250, BLUE_L, BLUE, 11))
    s.append(t(680, 136, "第 5 層：計算スキーマ決定（「どのスキーマを使うか」を決定）", 15, BLUE_D, weight="700"))
    det = [("販売エリア", "販売組織 + 流通チャネル + 製品部門"),
           ("得意先計算スキーマ", "得意先マスタの「販売ビュー → 価格設定」にある項目（例：1 標準）"),
           ("伝票計算スキーマ", "販売伝票タイプの価格設定項目（例：A 標準受注）")]
    yy = 164
    for k, v in det:
        s.append(rect(680, yy, 200, 34, "#ffffff", BLUE, 8, 1.2))
        s.append(t(692, yy + 22, k, 12.5, BLUE_D, weight="700"))
        for j, seg in enumerate(wrap(v, 11.5, 370, 2)):
            s.append(t(896, yy + 15 + j * 15, seg, 11.5, INK2))
        yy += 46
    s.append(t(680, yy + 8, "3 つのキー → 唯一の計算スキーマ（RVAA01）を決定 → システムはそれに従い明細ごとに価格を計算して転記します", 11.5, BLUE_D))
    s.append(t(680, yy + 30, "IMG：販売管理 → 基本機能 → 価格設定 → 価格設定管理 → 計算スキーマの定義と割当", 11, MUTED, family=MONO))

    s.append(rect(660, 376, 620, 232, GREEN_B, GREEN, 11))
    s.append(t(680, 404, "関連：勘定設定（収益をどの勘定に記録するか）", 15, GREEN, weight="700"))
    for i, ln in enumerate(wrap("請求書の転記時には会計伝票を生成します。販売収益勘定は固定ではなく、3 つのキーによるテーブル検索（VKOA）で導出します：", 12, 580, 2)):
        s.append(t(680, 428 + i * 17, ln, 12, INK2))
    keys = [("勘定キー Account Key", "計算スキーマの各ステップの勘定キー。たとえば ERL = 収益"),
            ("品目の勘定割当グループ", "品目マスタの販売ビューの項目（教材の例：M1 自製品 / M2 取引商品）"),
            ("得意先勘定割当グループ", "得意先マスタの項目（教材の例：01 国内収益）")]
    yy = 470
    for k, v in keys:
        s.append(rect(680, yy, 190, 36, "#ffffff", GREEN, 8, 1.2))
        s.append(t(690, yy + 23, k, 12, GREEN, weight="700"))
        for j, seg in enumerate(wrap(v, 11.5, 400, 2)):
            s.append(t(886, yy + 16 + j * 15, seg, 11.5, INK2))
        yy += 44
    s.append(t(680, yy + 14, "IMG：販売管理 → 基本機能 → 勘定割当/原価 → 収益勘定設定", 11, MUTED, family=MONO))

    # 下部の計算例
    s.append(rect(60, 640, 1220, 140, "#f7fafc", LINE, 10))
    s.append(t(78, 668, "コースシナリオの価格計算例（教材：铸钢泵 170-230 を 30〜120 個）", 14, INK, weight="700"))
    calc = [("品目 F999-100（铸钢泵 170-230）", ""), ("数量：120 PC", ""), ("PR00 単価 8,000.00", "条件タイプ：価格"),
            ("正味価額 960,000.00 RMB", "条件タイプ：小計"), ("MWST 売上税", "税分類 + 税コードで計算"),
            ("請求書 F2 90000000", "転記後に会計伝票を生成")]
    x = 78
    for i, (v, sub) in enumerate(calc):
        w = max(text_w(v, 12), text_w(sub, 10.5)) + 28
        s.append(rect(x, 686, w, 44, "#ffffff", AMBER if i in (2, 3) else BLUE, 8, 1.2))
        s.append(t(x + 13, 706, v, 12, INK))
        s.append(t(x + 13, 722, sub, 10.5, MUTED))
        x += w + 4
        if i < len(calc) - 1:
            s.append(arrow(x - 2, 708, x + 2, 708, MUTED, 1.4))
            x += 8
    s.append(t(78, 760, "注：単価と税率はコースシナリオの例示です。実際の金額は「条件レコード + 計算スキーマ + 税コード」が各システムで算出し、"
                         "自システムで VA03 → 明細 → 条件タブ により照合してください。", 11.5, MUTED))
    s.append("</svg>\n")
    return "pricing-chain.svg", "".join(s)


# --------------------------------------------------------------------------
# 5. エンドツーエンドフロー図 O2C（スイムレーン）
# --------------------------------------------------------------------------
def o2c_flow():
    W, H = 1420, 900
    s = [svg_open(W, H, "SD エンドツーエンドフロー図（Order to Cash）")]
    s.append(title_bar(40, 48, W - 80, "エンドツーエンドのフロー図：引合から入金まで（Order to Cash）",
                       "上段 = SD のアクション、中段 = 在庫/出荷で実際に起きること、下段 = 財務がトリガされる時点（当サイト自作図）"))
    lanes = [("SD 販売管理", 118, BLUE, BLUE_L),
             ("MM 在庫と出荷", 372, TEAL, TEAL_B),
             ("FI 財務会計", 626, "#5b3fa8", "#f4f0ff")]
    for name, y, color, bg in lanes:
        s.append(rect(40, y - 40, 1340, 240, bg, color, 12, 1.0))
        s.append(t(56, y - 16, name, 14, color, weight="700"))

    steps_sd = [
        ("引合 VA11", ["得意先の引合：何を、どれだけ"], "引合伝票"),
        ("見積 VA21", ["正式な見積。有効期間を含められる"], "見積伝票"),
        ("受注伝票 VA01", ["見積を参照して OR 受注伝票を登録", "価格設定＋所要量確認"], "受注伝票"),
        ("出荷伝票 VL01N", ["受注伝票を基準に納入伝票を作成", "出荷ポイント/保管場所を決定"], "納入伝票"),
        ("請求書 VF01", ["納入を参照して請求"], "請求書 F2"),
    ]
    steps_mm = [("利用可能在庫", ["受注伝票が ATP をチェック：在庫が足りるか", "不足 → 利用可能在庫なしと表示"]),
                ("ピッキング + 出庫過転記 VL02N", ["移動タイプ 601：実際の出庫", "この時点で初めて品目伝票が生成される"]),
                (None, None)]
    x = 70
    w = 240
    for i, (title, lines, doc) in enumerate(steps_sd):
        s.append(rect(x, 130, w, 108, "#ffffff", BLUE, 10))
        s.append(rect(x, 130, 4.5, 108, BLUE, BLUE, rx=2))
        s.append(badge(x + 22, 152, str(i + 1), BLUE, 12))
        s.append(t(x + 42, 157, title, 14.5, BLUE_D, weight="700"))
        yy = 180
        for ln in lines:
            for seg in wrap(ln, 11.5, w - 30, 2):
                s.append(t(x + 16, yy, seg, 11.5, INK2))
                yy += 15
        s.append(t(x + 16, 226, "アウトプット：" + doc, 11, MUTED, family=MONO))
        x += w + 32
        if i < len(steps_sd) - 1:
            s.append(arrow(x - 28, 184, x - 4, 184, BLUE, 2.0))

    # MM スイムレーン
    s.append(rect(310, 384, 240, 108, "#ffffff", TEAL, 10))
    s.append(rect(310, 384, 4.5, 108, TEAL, TEAL, rx=2))
    s.append(t(326, 410, "所要量確認（ATP）", 14, TEAL, weight="700"))
    s.append(t(326, 432, "受注保存時 / 納入作成時にチェック", 11.5, INK2))
    s.append(t(326, 452, "確認日 = 最も早く対応できる日付", 11.5, INK2))
    s.append(t(326, 478, "在庫不足でも保存可（ブロック時を除く）", 11, MUTED))
    s.append(rect(582, 384, 300, 108, "#ffffff", TEAL, 10))
    s.append(rect(582, 384, 4.5, 108, TEAL, TEAL, rx=2))
    s.append(t(598, 410, "ピッキング Picking", 14, TEAL, weight="700"))
    s.append(t(598, 432, "決定して保管場所から出庫する（ピッキング数量）", 11.5, INK2))
    s.append(t(598, 452, "次に「出庫過転記」：移動タイプ 601", 11.5, INK2))
    s.append(t(598, 478, "→ 品目伝票＋在庫減（MB1C 501 で期首在庫補充）", 11, MUTED))
    s.append(rect(914, 384, 300, 108, "#ffffff", TEAL, 10))
    s.append(rect(914, 384, 4.5, 108, TEAL, TEAL, rx=2))
    s.append(t(930, 410, "出庫過転記の後続処理", 14, TEAL, weight="700"))
    s.append(t(930, 432, "在庫数量と金額が同時に減少（出庫）", 11.5, INK2))
    s.append(t(930, 452, "納入ステータスが「完了」になり、請求可能", 11.5, INK2))
    s.append(t(930, 478, "原価は CO 側で表現（売上原価）", 11, MUTED))
    s.append(path("M 430 238 L 430 384", TEAL, 1.8, None, "4 4", "ar"))
    s.append(path("M 732 238 L 732 384", TEAL, 1.8, None, "4 4", "ar"))
    s.append(arrow(550, 438, 582, 438, TEAL, 1.8))
    s.append(arrow(882, 438, 914, 438, TEAL, 1.8))
    s.append(path("M 1064 384 L 1064 300 L 990 300", TEAL, 1.8, None, "4 4", "ar"))
    s.append(t(1000, 292, "出荷が完了して初めて請求できます", 11.5, TEAL))

    # FI スイムレーン
    s.append(rect(640, 638, 340, 108, "#ffffff", "#5b3fa8", 10))
    s.append(rect(640, 638, 4.5, 108, "#5b3fa8", "#5b3fa8", rx=2))
    s.append(t(656, 664, "請求書の転記（リリース）VF02", 14, "#5b3fa8", weight="700"))
    s.append(t(656, 686, "「保存 / リリース」→「転記に送信されました」", 11.5, INK2))
    s.append(t(656, 706, "会計伝票を生成：借方 得意先未収 / 貸方 収益 + 売上税", 11.5, INK2))
    s.append(t(656, 732, "勘定は VKOA + 勘定割当グループで導出される", 11, MUTED))
    s.append(rect(1020, 638, 340, 108, "#ffffff", "#5b3fa8", 10))
    s.append(rect(1020, 638, 4.5, 108, "#5b3fa8", "#5b3fa8", rx=2))
    s.append(t(1036, 664, "入金と消込", 14, "#5b3fa8", weight="700"))
    s.append(t(1036, 686, "入金 → F-28 で消込（FBL5N で未消込を確認）", 11.5, INK2))
    s.append(t(1036, 706, "プロセスのクローズドループ：現金が戻ってくる", 11.5, INK2))
    s.append(t(1036, 732, "当サイトのプロセスは教材シナリオに準拠：納入 → 請求 → 転記", 11, MUTED))
    s.append(path("M 900 238 L 900 560 L 810 560 L 810 638", "#5b3fa8", 1.8, None, "4 4", "ar"))
    s.append(arrow(980, 692, 1020, 692, "#5b3fa8", 1.8))

    # 伝票フローバー
    s.append(rect(40, 776, 1340, 96, "#f7fafc", LINE, 10))
    s.append(t(56, 802, "伝票フロー（Document Flow）：各下流伝票は上流伝票を「参照」して登録され、1 本のチェーンになります", 14, INK, weight="700"))
    docs = ["引合伝票", "見積伝票", "受注伝票", "納入伝票", "請求書", "会計伝票"]
    x = 56
    for i, d in enumerate(docs):
        w = text_w(d, 12.5) + 30
        s.append(rect(x, 816, w, 36, "#ffffff", BLUE if i < 5 else "#5b3fa8", 8, 1.3))
        s.append(t(x + 15, 840, d, 12.5, INK))
        x += w
        if i < len(docs) - 1:
            s.append(arrow(x + 2, 834, x + 20, 834, MUTED, 1.6))
            x += 24
    s.append(t(56, 868, "照合方法：VA03（受注）→ 環境 → 伝票フローの照会。または VF03（請求）→ ヘッダ → 原始凭证をクリックし、"
                         "受注伝票までたどって戻れます。「この 3 つの段階が 1 本のチェーンでつながっている」ことを確認してください。", 11.5, MUTED))
    s.append("</svg>\n")
    return "o2c-flow.svg", "".join(s)


# --------------------------------------------------------------------------
# 6. 伝票フロー構造図（参照関係 + ステータス）
# --------------------------------------------------------------------------
def doc_flow():
    W, H = 1340, 620
    s = [svg_open(W, H, "伝票フローと参照関係（構造図）")]
    s.append(title_bar(40, 48, W - 80, "伝票フロー構造図：どれがどれを参照するか、各伝票がどんなステータスを持つか",
                       "「参照による登録」はデータの一貫性を保証します：数量・価格・得意先が上流から引き継がれます（当サイト自作図）"))
    stages = [
        ("引合伝票", "VA11", "IN", ["得意先の意向", "価格拘束なし"], BLUE),
        ("見積伝票", "VA21", "QT", ["有効期間", "引合を参照して登録"], BLUE),
        ("受注伝票", "VA01", "OR", ["価格設定の決定", "所要量確認", "納入日", "不完全性チェック"], BLUE_D),
        ("納入伝票", "VL01N", "LF", ["ピッキング", "出庫過転記 601", "納入ステータス"], TEAL),
        ("請求書", "VF01", "F2", ["請求", "転記で FI 伝票を生成"], "#5b3fa8"),
    ]
    x = 60
    w = 222
    for i, (name, tc, tp, lines, color) in enumerate(stages):
        s.append(rect(x, 140, w, 190, "#ffffff", color, 12))
        s.append(rect(x, 140, w, 40, color, color, 12))
        s.append(t(x + 16, 167, name, 16, "#ffffff", weight="700"))
        s.append(t(x + w - 16, 167, tc, 12.5, "#eaf4ff", "end", family=MONO))
        s.append(t(x + 16, 206, "伝票タイプ／カテゴリ：" + tp, 11.5, MUTED, family=MONO))
        yy = 230
        for ln in lines:
            for seg in wrap(ln, 12, w - 32, 2):
                s.append(t(x + 16, yy, "· " + seg, 12, INK2))
                yy += 17
        s.append(rect(x + 16, 288, w - 32, 28, "#f7fafc", LINE, 7, 1))
        s.append(t(x + 26, 307, ["全体ステータス", "全体ステータス", "全体ステータス / 拒否理由", "出庫ステータス", "請求ステータス"][i], 11.5, INK2))
        x += w + 36
        if i < len(stages) - 1:
            s.append(arrow(x - 32, 235, x - 4, 235, color, 2.2))
            s.append(t(x - 40, 222, "参照元", 11.5, MUTED))
    s.append(rect(60, 366, 1220, 96, TEAL_B, TEAL, 10))
    s.append(t(78, 394, "なぜ新規に伝票を入力し直すのではなく「参照」するのか？", 14, TEAL, weight="700"))
    for i, ln in enumerate(wrap("① データの一貫性：数量・単価・条件は上流から引き継がれ、二重入力によるミスを防ぎます；"
                                "② 追跡可能性：どの請求書からも、その納入伝票と受注伝票へたどれる（元伝票ボタン）；"
                                "③ ステータスの連動：納入が完了すると受注明細の納入ステータスが更新され、請求書を転記すると請求ステータスが更新されます——"
                                "ステータスは「この伝票がどこまで進んだか」の答えです。", 12, 1180, 3)):
        s.append(t(78, 414 + i * 17, ln, 12, INK2))
    s.append(rect(60, 478, 600, 108, "#ffffff", AMBER, 10))
    s.append(t(78, 506, "変更と再決定（もう一度理解しましょう）", 14, AMBER, weight="700"))
    for i, ln in enumerate(wrap("得意先や品目を変更すると、システムは品目決定、価格設定、税、所要量を再決定します。\n"
                                "教材では得意先を変更すると Information: New pricing carried out（価格設定の再実行）が表示されます。", 12, 560, 3)):
        s.append(t(78, 528 + i * 17, ln, 12, INK2))
    s.append(rect(680, 478, 600, 108, "#ffffff", RED, 10))
    s.append(t(698, 506, "ステップは飛ばせない（最もよくあるエラー）", 14, RED, weight="700"))
    for i, ln in enumerate(wrap("納入がなければ（または出庫過転記をしていなければ）請求できません。在庫がなければ納入伝票を作成できません（教材が示す対処：MB1C 501 で期首在庫を入力）。"
                                "順序が違うのは Bug ではなく、業務プロセスの順序要件です。", 12, 560, 3)):
        s.append(t(698, 528 + i * 17, ln, 12, INK2))
    s.append("</svg>\n")
    return "doc-flow.svg", "".join(s)


# --------------------------------------------------------------------------
# 7. 受注伝票の内部処理フロー図（部分）
# --------------------------------------------------------------------------
def order_internal():
    W, H = 1340, 880
    s = [svg_open(W, H, "受注伝票の内部処理フロー図")]
    s.append(title_bar(40, 48, W - 80, "受注伝票の内部処理：1 枚の図で「自動決定」を理解する",
                       "VA01 では数行の情報を入力しただけですが、システムは裏でこれだけのことをしています（当サイトの自作図）"))
    blocks = [
        ("① ヘッダの入力", BLUE, ["受注タイプ（教材：OR 標準受注）", "受注先／出荷先／請求先／支払先",
                              "受注日、購買発注番号（得意先 PO）", "販売エリア：得意先マスタから引き継がれます"]),
        ("② 明細の入力", BLUE, ["品目 + 数量 + 納入日", "プラント（品目マスタ / 輸送条件から導出）",
                              "価格は条件レコードから「探し出」される"], ),
        ("③ 自動決定", TEAL, ["明細カテゴリ（TAN など）：伝票タイプ + 品目 → 価格設定／納入／請求の可否を決定",
                              "計算スキーマ：販売エリア＋得意先計算スキーマ＋伝票計算スキーマ → 行ごとに価格計算",
                              "税分類 + 税コード → 売上税", "パートナ：得意先マスタから受注先などの役割を導出"]),
        ("④ チェック", AMBER, ["所要量確認 ATP：納入日を確定（不足でも伝票は保存可能。ブロックを設定した場合を除く）",
                           "不完全性チェック：必須項目が未入力だと保存できない（保存できても伝票フローでは赤くマークされます）",
                           "与信管理（有効な場合）：超過すると自動で納入ブロックが設定されます"]),
        ("⑤ 保存と後続への影響", GREEN, ["受注伝票番号が生成され、伝票フローに入る", "所要量は MRP / 計画へ伝達（MD04 で確認可能）",
                                 "出力決定：受注確認書を印刷/メール送信できる", "ステータス項目が更新され、VA05 や後続の段階で使用される"]),
    ]
    y = 116
    for title, color, lines in blocks:
        h = 58 + 12 * len(lines) + 16 * max(0, len(lines) - 2)
        h = 62 + len(lines) * 20
        s.append(rect(60, y, 700, h, "#ffffff", color, 10))
        s.append(rect(60, y, 4.5, h, color, color, rx=2))
        s.append(t(78, y + 28, title, 15.5, color, weight="700"))
        yy = y + 50
        for ln in lines:
            for seg in wrap(ln, 12, 660, 2):
                s.append(t(78, yy, "· " + seg, 12, INK2))
                yy += 17
        y += h + 12
    # 右側：3 つの決定チェーン（パネルの高さは内容から算出し、大きな空白や内容の切れを防ぐ）
    AVAIL = 460

    def panel(y, title, bg, color, items, texts):
        chain_svg, ch = chain(818, y + 44, items, color, AVAIL) if items else ("", 6)
        ls = []
        for tx in texts:
            ls.extend(wrap(tx, 11.5, AVAIL, 4))
        h = 44 + ch + 8 + len(ls) * 17 + 10
        out = [rect(800, y, 500, h, bg, color, 11),
               t(818, y + 28, title, 14.5, color, weight="700"), chain_svg]
        yy = y + 44 + ch + 8 + 12
        for ln in ls:
            out.append(t(818, yy, ln, 11.5, INK2))
            yy += 17
        return "".join(out), h

    y = 116
    svg, h = panel(y, "決定チェーン 1：明細カテゴリ（Item Category）", BLUE_L, BLUE,
                   ["販売伝票タイプ", "品目マスタ（明細カテゴリグループ）", "用途（用途項目）", "上位明細（空値もキー）"],
                   ["「この明細をどう処理するか」を決定します。価格設定を行うか、納入するか、請求するか、在庫をどこから出すか（特別在庫 E など）。"
                    "教材のツール：VOV4 / VOV7。"])
    s.append(svg)
    y += h + 16
    svg, h = panel(y, "決定チェーン 2：計算スキーマ（Pricing Procedure）", TEAL_B, TEAL,
                   ["販売エリア", "得意先計算スキーマ", "伝票計算スキーマ"],
                   ["3 つのキーで唯一のスキーマ（教材では RVAA01）が決まり、スキーマ内にステップごとに条件タイプが並びます。"
                    "IMG：販売管理 → 基本機能 → 価格設定 → 価格設定管理 → 計算スキーマの定義と割当。"])
    s.append(svg)
    y += h + 16
    svg, h = panel(y, "決定チェーン 3：勘定設定（記帳勘定）", GREEN_B, GREEN, [],
                   ["請求書の転記時：勘定キー（ERL など、計算スキーマから）＋品目の勘定割当グループ＋得意先の勘定割当グループ → テーブル検索（VKOA）→ 収益勘定。",
                    "つまり「収益をどの勘定に記録するか」は、プログラムに固定されているわけでも手入力するわけでもありません。"])
    s.append(svg)
    s.append("</svg>\n")
    return "order-internal.svg", "".join(s)


DIAGRAMS = [mindmap, org_structure, integration, pricing_chain, o2c_flow, doc_flow, order_internal]


def main():
    os.makedirs(OUT, exist_ok=True)
    files = []
    for fn in DIAGRAMS:
        name, svg = fn()
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        # XML の妥当性
        try:
            ET.fromstring(svg)
        except ET.ParseError as e:
            print("XML ERROR", name, e)
            return 1
        files.append((name, len(svg)))
    for n, sz in files:
        print("%-22s %6d bytes" % (n, sz))
    print("diagrams: %d" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
