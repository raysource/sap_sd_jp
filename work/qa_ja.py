# -*- coding: utf-8 -*-
"""日本語版のテキスト衛生チェック（簡体字中国語の残留を数える）。

    python3 work/qa_ja.py [--ctx]

意図的に中国語を置いている領域は除外して数える:
  - <details class="orig">…</details>（原教材の原文）
  - <div class="pathzh">…</div>（原教材の中国語パス）
  - data-copy="…" / alt="…" / title="…"（コピー用の中国語パス・属性）
  - glossary.html の表（用語対照表 / IMG パス対照 = 中国語が列として必要）
  - 「…」で引用された画面上の中国語ラベル（例: 「新条目」）は**意図的な残置**なので
    別枠（引用）として数え、漏れ（引用の外にある中国語）と区別する。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "ja"))
from simp import SIMP  # noqa: E402

CHARS = "".join(sorted(SIMP))
QUOTED = re.compile(r"[「『“\"]([^」』”\"]{1,40})[」』”\"]")


def strip_intentional(s, page):
    s = re.sub(r'<details class="orig">.*?</details>', " ", s, flags=re.S)
    s = re.sub(r'<div class="pathzh">.*?</div>', " ", s, flags=re.S)
    s = re.sub(r'data-copy="[^"]*"', " ", s)
    s = re.sub(r'alt="[^"]*"', " ", s)
    s = re.sub(r'title="[^"]*"', " ", s)
    if page == "glossary.html":
        s = re.sub(r"<table.*?</table>", " ", s, flags=re.S)
    return s


def main():
    show_ctx = "--ctx" in sys.argv
    pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
    total = 0
    quoted_total = 0
    per_page = []
    for f in pages:
        s = io.open(os.path.join(ROOT, f), encoding="utf-8").read()
        body = strip_intentional(s, f)
        # 引用符の中の中国語（画面ラベル等）は意図的残置として分離
        quoted = set()
        for m in QUOTED.finditer(body):
            q = m.group(1)
            if set(q) & SIMP:
                quoted.add(m.group(0))
        body_free = QUOTED.sub(" ", body)
        quoted_total += len(quoted)
        hits = {}
        for m in re.finditer(r"[^\s<>]{0,28}[%s][^\s<>]{0,28}" % CHARS, body_free):
            for ch in m.group(0):
                if ch in SIMP:
                    hits.setdefault(ch, []).append(m.group(0).strip())
        n = sum(len(v) for v in hits.values())
        total += n
        if n or quoted:
            per_page.append((f, hits, len(quoted)))
        print("%-16s 中国語残留=%-4d 引用（意図的）=%-3d" % (f, n, len(quoted)))
    print("-" * 50)
    print("合計 中国語残留 %d 文字 / 引用の中国語ラベル %d 件" % (total, quoted_total))
    for f, hits, nq in per_page:
        if not hits:
            continue
        print("== %s" % f)
        for ch, ctx in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:12]:
            print("   %s ×%d  e.g. %s" % (ch, len(ctx), ctx[0][:56]))
    if show_ctx:
        for f, hits, _nq in per_page:
            for ch, ctx in hits.items():
                for c in ctx[:2]:
                    print("   [%s] %r" % (f, c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
