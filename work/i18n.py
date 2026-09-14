# -*- coding: utf-8 -*-
"""结构保存型 i18n 工具（sap_jp_sd 用）: collect → batches → merge → check → apply

- 翻訳対象は「文字列リテラルの中身」だけ。コード・HTML タグ・T-code・ファイル名は触らない。
- 各アトムは 1 行（マルチラインのリテラルは行単位に分割）→ 重複排除が効く。
- タグ / 実体参照 / エスケープ / %s 書式 は ⟦n⟧ マーカーに置換して子エージェントに渡す。
  戻すとき「各マーカーがちょうど 1 回」を検証するので、マークアップは壊れない。

    python3 work/i18n.py stats
    python3 work/i18n.py collect all
    python3 work/i18n.py batches 4200
    #   （子エージェントが work/ja/out/<kind>_NN.json を書く）
    python3 work/i18n.py merge
    python3 work/i18n.py check
    python3 work/i18n.py apply all
"""
import argparse
import glob
import hashlib
import io
import json
import os
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
JA = os.path.join(HERE, "ja")
OUT = os.path.join(JA, "out")
BATCH = os.path.join(JA, "batch")

CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

# ⟦n⟧ に退避する「翻訳してはいけない」要素
TOKEN_RE = re.compile(
    r"("
    r"<[^<>]*>"                                  # HTML タグ
    r"|&[a-zA-Z#0-9]{1,8};"                      # 実体参照
    r'|\\(?:[0-9]{1,3}|[a-zA-Z"\'/\\])'          # バックスラッシュエスケープ
    r"|%(?:\([^)]*\))?[-#0-9.+]*[sdrfFeEgGxX%]"  # %s / %(name)s / %%
    r"|\{[^{}]{0,40}\}"                          # {placeholder}
    r")"
)


def md5(b):
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hashlib.md5(b).hexdigest()


def mark(s):
    toks = []

    def rep(m):
        toks.append(m.group(0))
        return "\u27e6%d\u27e7" % (len(toks) - 1)

    return TOKEN_RE.sub(rep, s), toks


def unmark(s, toks):
    seen = [int(x) for x in re.findall(r"\u27e6(\d+)\u27e7", s)]
    if sorted(seen) != list(range(len(toks))):
        return None
    return re.sub(r"\u27e6(\d+)\u27e7", lambda m: toks[int(m.group(1))], s)


# ---------------------------------------------------------------- literals (py)
def line_offsets(text):
    offs, pos = [0], 0
    for ln in text.split("\n"):
        pos += len(ln) + 1
        offs.append(pos)
    return offs


def py_literals(path):
    """[(inner_start, inner_end)] を返す（絶対オフセット）。f-string は除外。"""
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8")
    offs = line_offsets(text)
    spans = []
    try:
        toks = list(tokenize.tokenize(io.BytesIO(data).readline))
    except tokenize.TokenError:
        return None
    for t in toks:
        if t.type != tokenize.STRING:
            continue
        s = t.string
        m = re.match(r"^([A-Za-z]*)", s)
        if m is None:
            continue
        prefix = m.group(1)
        body = s[len(prefix):]
        if not body or body[0] not in "\"'":
            continue
        if "f" in prefix.lower() and "{" in body:
            continue
        q = body[:3] if body[:3] in ('"""', "'''") else body[0]
        if len(body) < 2 * len(q):
            continue
        start = offs[t.start[0] - 1] + t.start[1] + len(prefix) + len(q)
        inner = body[len(q):-len(q)]
        spans.append((start, start + len(inner)))
    return spans


# ---------------------------------------------------------------- literals (js)
JS_STR = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`', re.S)


def js_literals(path):
    text = open(path, encoding="utf-8").read()
    spans = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            i = text.find("\n", i)
            if i < 0:
                break
        elif c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "\"'`":
            m = JS_STR.match(text, i)
            if not m:
                i += 1
                continue
            spans.append((i + 1, m.end() - 1))
            i = m.end()
        else:
            i += 1
    return spans


# ---------------------------------------------------------------- kinds
KINDS = {
    "py": {
        "files": lambda: sorted(glob.glob(os.path.join(ROOT, "tools", "*.py"))
                                + glob.glob(os.path.join(ROOT, "tools", "sitegen", "*.py"))),
        "lit": py_literals,
    },
    "js": {
        "files": lambda: sorted(glob.glob(os.path.join(ROOT, "assets", "*.js"))),
        "lit": js_literals,
    },
    "model": {
        "files": lambda: [os.path.join(ROOT, "work", "sd_source.json")],
        "lit": None,   # JSON は全 string 値
    },
}


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def read_text(p):
    return open(p, encoding="utf-8").read()


# ---------------------------------------------------------------- collect
def collect(kind):
    spec = KINDS[kind]
    files, atoms = {}, {}
    if kind == "model":
        for p in spec["files"]():
            src = read_text(p)
            files[rel(p)] = md5(src)
            data = json.loads(src)

            def walk(o, path):
                if isinstance(o, dict):
                    for k, v in o.items():
                        walk(v, path + [k])
                elif isinstance(o, list):
                    for i, v in enumerate(o):
                        walk(v, path + [i])
                elif isinstance(o, str) and CJK.search(o):
                    a = atoms.setdefault(md5(o)[:10], {"text": o, "occs": []})
                    a["occs"].append([rel(p), path])
            walk(data, [])
    else:
        for p in spec["files"]():
            if not os.path.exists(p):
                continue
            src = read_text(p)
            spans = spec["lit"](p)
            if spans is None:
                print("WARN: 解析不能（スキップ）: %s" % rel(p))
                continue
            files[rel(p)] = md5(src)
            for li, (s, e) in enumerate(spans):
                inner = src[s:e]
                if not CJK.search(inner):
                    continue
                for li_line, line in enumerate(inner.split("\n")):
                    if not CJK.search(line):
                        continue
                    a = atoms.setdefault(md5(line)[:10], {"text": line, "occs": []})
                    a["occs"].append([rel(p), li, li_line])
    json.dump({"kind": kind, "files": files, "atoms": atoms},
              open(os.path.join(JA, "%s_atoms.json" % kind), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    tot = sum(len(a["text"]) for a in atoms.values())
    print("collect %-6s files=%-3d atoms=%-5d chars=%d" % (kind, len(files), len(atoms), tot))
    return atoms


# ---------------------------------------------------------------- batches
def batches(limit):
    os.makedirs(BATCH, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    for kind in ("model", "py", "js"):
        f = os.path.join(JA, "%s_atoms.json" % kind)
        if not os.path.exists(f):
            continue
        atoms = json.load(open(f, encoding="utf-8"))["atoms"]
        items = []
        for key, a in sorted(atoms.items(), key=lambda kv: -kv[1]["text"].count("\n")):
            masked, _ = mark(a["text"])
            items.append({"id": key, "zh": masked})
        items.sort(key=lambda it: (it["zh"][:1].lower(), it["id"]))
        cur, size, n = [], 0, 0
        for it in items:
            if cur and size + len(it["zh"]) > limit:
                n += 1
                json.dump({"kind": kind, "batch": n, "items": cur},
                          open(os.path.join(BATCH, "%s_%02d.json" % (kind, n)), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                cur, size = [], 0
            cur.append(it)
            size += len(it["zh"])
        if cur:
            n += 1
            json.dump({"kind": kind, "batch": n, "items": cur},
                      open(os.path.join(BATCH, "%s_%02d.json" % (kind, n)), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
        print("%-6s -> %d batch(es)" % (kind, n))


# ---------------------------------------------------------------- merge / check
def merge():
    maps = {}
    for kind in ("model", "py", "js"):
        f = os.path.join(JA, "%s_atoms.json" % kind)
        if not os.path.exists(f):
            continue
        atoms = json.load(open(f, encoding="utf-8"))["atoms"]
        out, missing, bad = {}, [], []
        for p in sorted(glob.glob(os.path.join(OUT, "%s_*.json" % kind))):
            d = json.load(open(p, encoding="utf-8"))
            if isinstance(d, dict) and "items" in d:
                d = {it["id"]: it.get("ja") or it.get("out") for it in d["items"]}
            for k, v in d.items():
                if k in atoms and isinstance(v, str) and v.strip():
                    out[k] = v.strip()
        for k, a in atoms.items():
            if k not in out:
                missing.append(k)
                continue
            _, toks = mark(a["text"])
            if unmark(out[k], toks) is None:
                bad.append(k)
        maps[kind] = out
        json.dump(out, open(os.path.join(JA, "%s_map.json" % kind), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, sort_keys=True)
        print("merge %-6s atoms=%-5d translated=%-5d missing=%-4d marker-fail=%d"
              % (kind, len(atoms), len(out), len(missing), len(bad)))
        if missing[:5]:
            print("   missing sample: %s" % missing[:5])
        if bad[:5]:
            print("   marker-fail sample: %s" % bad[:5])
    return maps


def check():
    ok = True
    for kind in ("model", "py", "js"):
        fa = os.path.join(JA, "%s_atoms.json" % kind)
        fm = os.path.join(JA, "%s_map.json" % kind)
        if not os.path.exists(fa):
            continue
        atoms = json.load(open(fa, encoding="utf-8"))["atoms"]
        ja = json.load(open(fm, encoding="utf-8"))
        miss, bad, nl, left = [], [], [], []
        for k, a in atoms.items():
            v = ja.get(k)
            if not v:
                miss.append(k)
                continue
            if "\n" in v:
                nl.append(k)
            _, toks = mark(a["text"])
            if unmark(v, toks) is None:
                bad.append(k)
            if CJK.search(v) and v == a["text"]:
                left.append(k)
        print("check %-6s atoms=%-5d missing=%-4d marker-fail=%-4d newline=%-3d untranslated=%d"
              % (kind, len(atoms), len(miss), len(bad), len(nl), len(left)))
        if miss or bad or nl:
            ok = False
            print("   sample: %s %s %s" % (miss[:3], bad[:3], nl[:3]))
    print("RESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ---------------------------------------------------------------- apply
def apply_kind(kind):
    fa = os.path.join(JA, "%s_atoms.json" % kind)
    if not os.path.exists(fa):
        return
    blob = json.load(open(fa, encoding="utf-8"))
    ja = json.load(open(os.path.join(JA, "%s_map.json" % kind), encoding="utf-8"))
    files, atoms = blob["files"], blob["atoms"]
    if kind == "model":
        for f, h in files.items():
            p = os.path.join(ROOT, f)
            src = read_text(p)
            if md5(src) != h:
                print("SKIP (変更あり): %s" % f)
                continue
            data = json.loads(src)
            done = [0]

            def walk(o):
                if isinstance(o, dict):
                    return {k: walk(v) for k, v in o.items()}
                if isinstance(o, list):
                    return [walk(v) for v in o]
                if isinstance(o, str) and CJK.search(o):
                    v = ja.get(md5(o)[:10])
                    if v:
                        _, toks = mark(o)
                        back = unmark(v, toks)
                        if back is None:
                            print("!! marker mismatch in %s: %r" % (f, o[:40]))
                            return o
                        done[0] += 1
                        return back
                return o

            out = walk(data)
            tgt = os.path.join(ROOT, "work", "sd_source_ja.json")
            json.dump(out, open(tgt, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("apply model -> work/sd_source_ja.json (%d values)" % done[0])
        return

    for f, h in sorted(files.items()):
        p = os.path.join(ROOT, f)
        src = read_text(p)
        if md5(src) != h:
            print("SKIP (変更あり): %s" % f)
            continue
        spans = KINDS[kind]["lit"](p)
        edits = []
        n = 0
        for li, (s, e) in enumerate(spans):
            inner = src[s:e]
            if not CJK.search(inner):
                continue
            lines = inner.split("\n")
            for idx, line in enumerate(lines):
                if not CJK.search(line):
                    continue
                v = ja.get(md5(line)[:10])
                if not v:
                    continue
                _, toks = mark(line)
                back = unmark(v, toks)
                if back is None:
                    print("!! marker mismatch in %s: %r" % (f, line[:60]))
                    continue
                lines[idx] = back
                n += 1
            new = "\n".join(lines)
            if new != inner:
                edits.append((s, e, new))
        if not edits:
            print("  変更なし: %s" % f)
            continue
        for s, e, new in reversed(edits):
            src = src[:s] + new + src[e:]
        open(p, "w", encoding="utf-8").write(src)
        print("apply %-6s %-40s %d 行" % (kind, f, n))


def apply_all(which):
    for kind in ("model", "py", "js"):
        if which in ("all", kind):
            apply_kind(kind)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["stats", "collect", "batches", "merge", "check", "apply"])
    ap.add_argument("arg", nargs="?", default="all")
    a = ap.parse_args()
    os.makedirs(JA, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    if a.cmd == "stats":
        for kind in ("py", "js", "model"):
            collect(kind)
            fl = os.path.join(JA, "%s_atoms.json" % kind)
            d = json.load(open(fl, encoding="utf-8"))["atoms"]
            print("      → %d atoms / %d chars (masked %d)"
                  % (len(d), sum(len(v["text"]) for v in d.values()),
                     sum(len(mark(v["text"])[0]) for v in d.values())))
    elif a.cmd == "collect":
        for kind in (("py", "js", "model") if a.arg == "all" else (a.arg,)):
            collect(kind)
    elif a.cmd == "batches":
        batches(int(a.arg))
    elif a.cmd == "merge":
        merge()
    elif a.cmd == "check":
        return check()
    elif a.cmd == "apply":
        apply_all(a.arg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
