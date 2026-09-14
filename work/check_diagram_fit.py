# -*- coding: utf-8 -*-
"""自作 SVG の文字はみ出しチェック（sap_jp_sd / 日本語に置き換えた図の検算）。

考え方:
  - <text> の bbox を推定する（CJK は全角 1.0em、半角 0.52em、等幅 0.6em — 生成器と同じ式）。
  - その文字が「乗っている」矩形（<rect>）を y と x で探す。矩形の内側に収まっていなければ
    はみ出しとして報告する。矩形が無ければ「キャンバス外」だけを見る。
  - 中国語版と日本語版の両方に掛けて、**日本語版で新たに増えたはみ出しだけ**を問題視する。

    python3 work/check_diagram_fit.py <site-dir> [<site-dir> …]
"""
import os
import re
import sys
import unicodedata

TEXT = re.compile(r'<text x="([-\d.]+)" y="([-\d.]+)"([^>]*)>(.*?)</text>', re.S)
RECT = re.compile(r'<rect x="([-\d.]+)" y="([-\d.]+)" width="([\d.]+)" height="([\d.]+)"')
VIEW = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')
MONO = re.compile(r'font-family="([^"]*)"')


def char_w(ch):
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 1.0
    if ch in "iljI.,:;'|! ":
        return 0.32
    if ch in "mMW@":
        return 0.9
    return 0.575


def text_w(s, size, mono=False):
    if mono:
        return len(s) * 0.6 * size
    return sum(char_w(c) for c in s) * size


def unesc(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))


def check(path):
    src = open(path, encoding="utf-8").read()
    m = VIEW.search(src)
    W, H = (float(m.group(1)), float(m.group(2))) if m else (0, 0)
    rects = [(float(a), float(b), float(c), float(d)) for a, b, c, d in RECT.findall(src)]
    bad = []
    for x, y, attrs, body in TEXT.findall(src):
        x, y = float(x), float(y)
        txt = unesc(re.sub(r"<[^>]+>", "", body)).strip()
        if not txt:
            continue
        size = float(re.search(r'font-size="([\d.]+)"', attrs).group(1)) if "font-size=" in attrs else 13.0
        mono = "mono" in (re.search(MONO, attrs).group(1).lower() if MONO.search(attrs) else "")
        w = text_w(txt, size, mono)
        anchor = "start"
        if 'text-anchor="middle"' in attrs:
            anchor = "middle"
        elif 'text-anchor="end"' in attrs:
            anchor = "end"
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        x1 = x0 + w
        # 乗っている矩形（y が矩形の上下に入り、中心が横に入る）
        host = None
        for rx, ry, rw, rh in rects:
            if ry - 0.5 <= y <= ry + rh + 0.5 and rx - 2 <= (x0 + x1) / 2 <= rx + rw + 2:
                if host is None or rw * rh < host[2] * host[3]:
                    host = (rx, ry, rw, rh)
        if host is None:
            if W and (x0 < -1 or x1 > W + 1):
                bad.append(("キャンバス外", txt[:40], round(x0), round(x1)))
            continue
        rx, ry, rw, rh = host
        over_l = rx + 2 - x0
        over_r = x1 - (rx + rw - 2)
        if over_l > 1 or over_r > 1:
            bad.append(("矩形からはみ出し(%d/%d)" % (round(over_l), round(over_r)), txt[:40],
                        round(x0), round(x1)))
    return bad


def main():
    dirs = sys.argv[1:]
    total = {}
    for d in dirs:
        dp = os.path.join(d, "assets", "diagrams")
        if not os.path.isdir(dp):
            continue
        print("=== %s" % d)
        for f in sorted(os.listdir(dp)):
            if not f.endswith(".svg"):
                continue
            bad = check(os.path.join(dp, f))
            key = (d, f)
            total[key] = bad
            print("   %-22s はみ出し=%d" % (f, len(bad)))
            for kind, txt, a, b in bad[:6]:
                print("        %s  %r  x=%s..%s" % (kind, txt, a, b))
    if len(dirs) > 1:
        print("=== 差分（日本語版で新たに増えたもの）")
        for f in sorted({k[1] for k in total}):
            cn = len(total.get((dirs[0], f), []))
            jp = len(total.get((dirs[1], f), []))
            flag = "  ← 増加" if jp > cn else ""
            print("   %-22s cn=%-3d jp=%-3d%s" % (f, cn, jp, flag))
    return 0


if __name__ == "__main__":
    sys.exit(main())
