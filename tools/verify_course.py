# -*- coding: utf-8 -*-
"""当サイト専用の検証ツール（SAP SD トレーニングコースサイト）。

チェック：
① 各ページの構造（DOCTYPE / article は 1 つ / article は footer より前 / タグの対応）
② ナビゲーション：各ページの href リストが完全に一致、active はちょうど 1 つ
③ リンク：サイト内の .html と #アンカー がどちらも解決できる；各ページの id が重複しない
④ リソース：assets/img/…（実際のスクリーンショット）と assets/diagrams/…（自作図）がどちらも存在
⑤ 図キャプション：figure.shot には「画面」番号 + 出典文字列が必須、figure.dia にはタイプのラベルが必須
⑥ セルフチェックテスト：30 問、data-answer は必ずいずれかの選択肢の data-key
⑦ カウントが tools/hub_stats.json と一致
⑧ テキストの健全性：残留 Markdown（**…**）なし、プレースホルダ TODO/lorem なし
終了コード 0 = PASS。
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sitegen"))
import common  # noqa: E402

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}
PAGES = [f for f, _l, _t in common.NAV]

errs, warns = [], []


def err(msg):
    errs.append(msg)


def warn(msg):
    warns.append(msg)


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.bad, self.ids = [], [], []
        self.article_open = self.article_close = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.append(d["id"])
        if tag == "article":
            self.article_open += 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "article":
            self.article_close += 1
        if tag in VOID:
            return
        if not self.stack:
            self.bad.append("余分な </%s>" % tag)
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        else:
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.bad.append("</%s> が未クローズ（期待 </%s>）" % (self.stack[-1], tag))
                    self.stack.pop()
                if self.stack:
                    self.stack.pop()
            else:
                self.bad.append("孤立した </%s>" % tag)


def main():
    htmls = {}
    for f in PAGES:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            err("欠落ページ：%s" % f)
            continue
        htmls[f] = open(p, encoding="utf-8").read()
    if not htmls:
        print("RESULT: FAIL\n" + "\n".join(errs))
        return 1

    ids_by_page = {}
    for f, s in htmls.items():
        # ① 構造
        if not s.startswith("<!DOCTYPE html>"):
            err("%s: DOCTYPE がない" % f)
        for need in ("<html", "</html>", "<head>", "</head>", "<body>", "</body>", "<footer"):
            if need not in s:
                err("%s: %s がない" % (f, need))
        bp = Balance()
        bp.feed(s)
        ids_by_page[f] = bp.ids
        if bp.bad:
            err("%s: タブの問題 %s" % (f, "; ".join(bp.bad[:4])))
        if bp.stack:
            err("%s: 閉じられていないタグ %s" % (f, bp.stack[:6]))
        if bp.article_open != 1 or bp.article_close != 1:
            err("%s: article 開=%d 閉=%d（1/1 であるべき）" % (f, bp.article_open, bp.article_close))
        i_a, i_f = s.find("</article>"), s.find("<footer")
        if i_a < 0 or i_f < 0 or i_a > i_f:
            err("%s: </article> が <footer> より前にない" % f)
        dup = [x for x in set(ids_by_page[f]) if ids_by_page[f].count(x) > 1]
        if dup:
            err("%s: id が重複 %s" % (f, dup[:5]))

        # ② ナビゲーション
        nav = re.search(r'<nav class="main">(.*?)</nav>', s, re.S)
        if not nav:
            err("%s: nav.main が見つからない" % f)
        else:
            hrefs = re.findall(r'href="([^"]+)"', nav.group(1))
            act = re.findall(r'<a class="active" href="([^"]+)"', nav.group(1))
            htmls[f] = (s, hrefs, act)

    nav_ref = None
    for f, v in htmls.items():
        if isinstance(v, tuple):
            s, hrefs, act = v
            htmls[f] = s
            if nav_ref is None:
                nav_ref = (f, hrefs)
            elif hrefs != nav_ref[1]:
                err("%s: ナビゲーションが %s と不一致" % (f, nav_ref[0]))
            if len(act) != 1:
                err("%s: active 件数=%d（1 であるべき）" % (f, len(act)))
            elif act[0] != f:
                err("%s: active の参照先 %s" % (f, act[0]))

    # ③④⑤ リンク / リソース / 図キャプション
    shot_refs, dia_refs = [], []
    for f, s in htmls.items():
        for href in re.findall(r'href="([^"]+)"', s):
            if href.startswith(("http", "mailto", "#")):
                if href.startswith("#"):
                    if href[1:] not in ids_by_page.get(f, []):
                        err("%s: ページ内アンカー %s が存在しない" % (f, href))
                continue
            target, _, anchor = href.partition("#")
            if target.endswith(".html"):
                if target not in htmls:
                    err("%s: リンク切れ %s" % (f, target))
                elif anchor and anchor not in ids_by_page.get(target, []):
                    err("%s: アンカー %s が %s に存在しない" % (f, anchor, target))
            elif not os.path.exists(os.path.join(ROOT, target)):
                err("%s: ファイル欠落 %s" % (f, target))
        for src in re.findall(r'src="(assets/(?:img|diagrams)/[^"]+)"', s):
            if not os.path.exists(os.path.join(ROOT, src)):
                err("%s: 画像欠落 %s" % (f, src))
            (dia_refs if "/diagrams/" in src else shot_refs).append((f, src))
        for m in re.finditer(r'<figure class="shot[^"]*">(.*?)</figure>', s, re.S):
            blk = m.group(1)
            if "figcaption" not in blk:
                err("%s: figure.shot に figcaption がない" % f)
            elif "<span class=\"n\">画面" not in blk:
                err("%s: figure.shot に「画面」番号がない" % f)
            if "<span class=\"src\">" not in blk:
                err("%s: figure.shot に出典表記がない" % f)
            if "alt=" not in blk:
                err("%s: 画像に alt がない" % f)
        for m in re.finditer(r'<figure class="dia">(.*?)</figure>', s, re.S):
            blk = m.group(1)
            for need, label in (('class="n"', "タイプタブ"), ('class="src"', "自作図の注記"), ("alt=", "alt")):
                if need not in blk:
                    err("%s: figure.dia に%sがない" % (f, label))

    # ⑥ セルフチェックテスト（quiz-q 単位で区切り、入れ子の div は見ない）
    qhtml = htmls.get("quiz.html", "")
    blocks = qhtml.split('<div class="quiz-q"')[1:]
    qs = []
    for blk in blocks:
        m = re.match(r' data-answer="([A-D])"', blk)
        if not m:
            err("quiz.html: ある問題の data-answer が A〜D ではない")
            continue
        qs.append((m.group(1), blk))
    if len(qs) != 30:
        err("quiz.html: 問題数 %d（30 であるべき）" % len(qs))
    for ans, blk in qs:
        blk = blk.split('<div class="quiz-q"')[0]
        keys = re.findall(r'<div class="opt" data-key="([A-D])">', blk)
        if keys != ["A", "B", "C", "D"]:
            err("quiz.html: ある問題の選択肢キーが %s" % keys)
        if 'class="explain"' not in blk:
            err("quiz.html: ある問題に解説がない")
        if ans not in keys:
            err("quiz.html: 正解 %s が選択肢にない" % ans)

    # ⑦ カウント
    n_shot = sum(1 for _ in shot_refs)
    n_uniq = len(set(x[1] for x in shot_refs))
    n_dia = len(set(x[1] for x in dia_refs))
    hub = json.load(open(os.path.join(ROOT, "tools", "hub_stats.json"), encoding="utf-8"))
    if hub["n_pages"] != len(htmls):
        err("hub_stats.n_pages=%s とページ数 %d が不一致" % (hub["n_pages"], len(htmls)))
    if hub["figs"] != n_shot:
        err("hub_stats.figs=%s とスクリーンショット参照 %d が不一致" % (hub["figs"], n_shot))

    # ⑧ テキストの健全性
    for f, s in htmls.items():
        for pat, why in ((r"\*\*[^*\n]{2,}\*\*", "残存する Markdown の太字"),
                         (r"lorem ipsum", "プレースホルダテキスト"),
                         (r"TODO|FIXME", "TODO マーク"),
                         (r"\{[a-z_]+\}", "未置換のテンプレート変数")):
            for m in re.finditer(pat, s, re.I):
                err("%s: %s → %r" % (f, why, s[max(0, m.start() - 30):m.end() + 20]))

    # レポート
    on_disk = len([1 for r, _d, fs in os.walk(os.path.join(ROOT, "assets", "img")) for _x in fs])
    print("pages=%d  figure.shot=%d（重複除去 %d / ディスク %d）  figure.dia=%d（重複除去 %d）  quiz=%d"
          % (len(htmls), n_shot, n_uniq, on_disk, len(dia_refs), n_dia, len(qs)))
    for w in warns:
        print("WARN:", w)
    if errs:
        print("RESULT: FAIL (%d)" % len(errs))
        for e in errs[:40]:
            print("  -", e)
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
