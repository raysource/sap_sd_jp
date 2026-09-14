# -*- coding: utf-8 -*-
"""子エージェント用の自前チェック（1 バッチ単位）。

    python3 work/ja/check_batch.py work/ja/out/py_01.json

検査内容（すべて満たさないと FAIL）:
  - 純粋な JSON（dict）で、キー集合 == 入力バッチの id 集合
  - 値が空でない / 改行を含まない
  - ⟦n⟧ マーカーが入力とちょうど同じ個数・同じ番号
  - 原文のまま（未訳）になっていない / 簡体字中国語がそのまま残っていない

注意: 日本語の漢字（販売組織・定義・受注伝票 …）は中国語の漢字と同じ Unicode なので、
「漢字があるから中国語」という判定はしない。簡体字専用の文字セットだけで判定する
（漢字・かな・カタカナ・T-code・固有名詞は自由に使ってよい）。
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(SITE, "work"))
sys.path.insert(0, HERE)
import i18n  # noqa: E402
from simp import SIMP  # noqa: E402  （簡体字専用文字セット。日本語の漢字は入っていない）

# 「これは翻訳しなければならない中国語」の目印。簡体字専用字＋漢語の助詞・動詞。
# 固有名詞だけの行（例: 「⟦0⟧P999⟦1⟧ 颐宁机械工厂」「⟦0⟧画面」）を「未訳」と誤判定しないため、
# 「2 文字以上」当てはまったときだけ未訳とみなす。
MUST_ZH = set(SIMP) | set("的了是在与请点按行过开为什么这")

HIRA_KATA = re.compile(r"[\u3041-\u309f\u30a0-\u30ff]")


def main():
    if len(sys.argv) < 2:
        print("usage: python3 work/ja/check_batch.py work/ja/out/<name>.json")
        return 2
    out_path = sys.argv[1]
    if not os.path.isabs(out_path):
        out_path = os.path.join(os.getcwd(), out_path)
    name = os.path.basename(out_path)
    in_path = os.path.join(SITE, "work", "ja", "batch", name)
    if not os.path.exists(in_path):
        print("入力バッチが無い: %s" % in_path)
        return 2
    ja = json.load(open(out_path, encoding="utf-8"))
    src = json.load(open(in_path, encoding="utf-8"))
    ids = [it["id"] for it in src["items"]]
    zh = {it["id"]: it["zh"] for it in src["items"]}

    problems = []
    if not isinstance(ja, dict):
        problems.append("トップレベルが object ではない")
        ja = {}
    extra = [k for k in ja if k not in zh]
    miss = [k for k in ids if k not in ja]
    if extra:
        problems.append("入力にないキー: %s" % extra[:5])
    if miss:
        problems.append("訳が無いキー: %d 件 %s" % (len(miss), miss[:5]))

    n_marker = n_simp = n_same = 0
    for k, v in ja.items():
        if k not in zh:
            continue
        if not isinstance(v, str):
            problems.append("%s: 文字列ではない" % k)
            continue
        if not v.strip():
            problems.append("%s: 空" % k)
        if "\n" in v or "\r" in v:
            problems.append("%s: 改行が入っている" % k)
        a = sorted(re.findall(r"\u27e6(\d+)\u27e7", zh[k]))
        b = sorted(re.findall(r"\u27e6(\d+)\u27e7", v))
        if a != b:
            n_marker += 1
            if n_marker <= 3:
                problems.append("%s: マーカー不一致 in=%s out=%s" % (k, a, b))
        body = re.sub(r"\u27e6\d+\u27e7", "", v)
        hit = sorted(set(body) & SIMP)
        if len(hit) >= 2 and not HIRA_KATA.search(body):
            # 簡体字専用字を 2 種以上含み、かなも無い＝中国語の文が残っている
            n_simp += 1
            if n_simp <= 3:
                problems.append("%s: 簡体字が残っている? %r (hit=%s)" % (k, v[:60], "".join(hit[:8])))
        src_body = re.sub(r"\u27e6\d+\u27e7", "", zh[k]).strip()
        if body.strip() == src_body and len(set(body) & MUST_ZH) >= 2:
            # 原文と同一で、かつ中国語の言い回しに必ず出る字を 2 つ以上含む＝未訳
            # （固有名詞だけの行は 0〜1 個なので誤判定しない）
            n_same += 1
            if n_same <= 3:
                problems.append("%s: 原文のまま（未訳） %r" % (k, v[:60]))

    print("batch %s: keys=%d translated=%d" % (name, len(ids), len(ja)))
    print("problems %d" % len(problems))
    for p in problems[:20]:
        print("  - %s" % p)
    print("RESULT: %s" % ("PASS" if not problems else "FAIL"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
