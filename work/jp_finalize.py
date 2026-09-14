# -*- coding: utf-8 -*-
"""i18n apply の後に行う構造パッチ（sap_jp_sd 専用）。

    python3 work/jp_finalize.py

思想: **追記だけで済むものは追記する**。既存関数を消して書き換えるより、
モジュール末尾で再定義したほうが壊れる確率が低い（common.py の末尾で
scap/spath/src_ref/pathline を日本語版として再定義する）。

対象:
  1. tools/sitegen/common.py   … lang="ja" / 日本語モデル読み込み / 原文併記ヘルパを追記
  2. tools/build_pages.py      … 用語集ページを p_jp.page_glossary に差し替え
  3. tools/make_course_xlsx.py … 出力ファイル名（日本語）
  4. assets/sd.js              … 用語集の件数表示を中立な文言に
  5. 旧 Excel（中国語名）を削除
"""
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

COMMON_TAIL = '''

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
    return esc(t).replace("\\n", "<br>")


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
    m = re.match(r"^(解説|説明|注意)\\s*[：:]\\s*(.*)$", c, re.S)
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
'''


def patch_common():
    p = os.path.join(ROOT, "tools", "sitegen", "common.py")
    s = io.open(p, encoding="utf-8").read()
    if "日本語版の追加物" in s:
        print("common.py: 追加済み（スキップ）")
        return
    n = s.count('lang="zh-CN"')
    s = s.replace('lang="zh-CN"', 'lang="ja"')
    if re.search(r"^import re$", s, re.M) is None:
        s = s.replace("import os\n", "import os\nimport re\n", 1)
    s = s.rstrip("\n") + "\n" + COMMON_TAIL
    io.open(p, "w", encoding="utf-8").write(s)
    print("common.py: lang=%d 箇所を ja に / 日本語版ヘルパを追記" % n)


def patch_build_pages():
    p = os.path.join(ROOT, "tools", "build_pages.py")
    s = io.open(p, encoding="utf-8").read()
    if "p_jp" in s:
        print("build_pages.py: 追加済み（スキップ）")
        return
    s = s.replace("import p_admin as P3  # noqa: E402",
                  "import p_admin as P3  # noqa: E402\nimport p_jp  # noqa: E402")
    # 用語集ページを日本語版モジュールに差し替え（行の末尾は問わない）
    s2 = re.sub(r'(\(\s*"glossary\.html",[^)]*?)P3\.page_glossary', r"\1p_jp.page_glossary", s)
    if s2 == s:
        s2 = s.replace("P3.page_glossary", "p_jp.page_glossary")
    io.open(p, "w", encoding="utf-8").write(s2)
    print("build_pages.py: p_jp を import / glossary を差し替え%s"
          % ("" if s2 != s else "  ← 差し替え失敗の可能性あり（要確認）"))


def patch_xlsx():
    p = os.path.join(ROOT, "tools", "make_course_xlsx.py")
    s = io.open(p, encoding="utf-8").read()
    s2 = re.sub(r'OUT = os\.path\.join\(ROOT, "[^"]+\.xlsx"\)',
                'OUT = os.path.join(ROOT, "SAPSD_学習WBS.xlsx")', s)
    s2 = s2.replace("../sap_cn/index.html", "index.html")
    s2 = s2.replace("微软雅黑", "Yu Gothic")
    if s2 != s:
        io.open(p, "w", encoding="utf-8").write(s2)
    print("make_course_xlsx.py: OUT を SAPSD_学習WBS.xlsx に / 参照パスとフォントを修正")
    old = os.path.join(ROOT, "SAPSD_课程大纲_学习WBS.xlsx")
    if os.path.exists(old):
        os.remove(old)
        print("旧 Excel を削除: %s" % os.path.basename(old))


def patch_js():
    p = os.path.join(ROOT, "assets", "sd.js")
    s = io.open(p, encoding="utf-8").read()
    m = re.search(r'if \(count\) count\.textContent = [^;]+;', s)
    if not m:
        print("sd.js: 件数表示の行が見つからない（スキップ）")
        return
    new = 'if (count) count.textContent = "表示 " + n + " / " + rows.length + " 件";'
    if m.group(0) == new:
        print("sd.js: 変更済み（スキップ）")
        return
    s = s[:m.start()] + new + s[m.end():]
    io.open(p, "w", encoding="utf-8").write(s)
    print("sd.js: 件数表示を中立な文言に（%s）" % m.group(0)[:48])


def patch_p_admin():
    p = os.path.join(ROOT, "tools", "sitegen", "p_admin.py")
    s = io.open(p, encoding="utf-8").read()
    n_imp = 0
    if "step_items" not in s:
        s2, n_imp = re.subn(r"from common import \(TASK, ",
                            "from common import (TASK, TASK_JA, step_items, ", s, count=1)
        s = s2
    # 設定ページのタスク参照を日本語モデルに
    s, n_task = re.subn(r"(?m)^(\s*)t = TASK\[n\]$", r"\1t = TASK_JA[n]", s)
    # 手順要点の <li> 生成を共通ヘルパに差し替え（原文の折りたたみを併記）
    old = re.compile(
        r'(?m)^([ \t]*)caps = \[s\.get\("caption", ""\) for s in t\["steps"\]\]\n'
        r'[ \t]*items = \[\(c,[^\n]*\) for c in caps if c\]\n')
    s, n_items = old.subn(r'\1items = step_items(n, t["steps"], TASK[n]["steps"])\n', s)
    io.open(p, "w", encoding="utf-8").write(s)
    print("p_admin.py: import=%d 個追加 / t=TASK_JA %d 箇所 / 手順要点の差し替え %d 箇所"
          % (n_imp, n_task, n_items))
    if n_task == 0 or n_items == 0:
        print("p_admin.py: WARN 置換できなかった（アンカー不一致）— 手で確認が必要")


def patch_p_overview():
    p = os.path.join(ROOT, "tools", "sitegen", "p_overview.py")
    s = io.open(p, encoding="utf-8").read()
    s, n = re.subn(r'common\.TASK\[n\]\["title"\]', 'common.TASK_JA[n]["title"]', s)
    # 日本語版であることの説明をホーム冒頭に足す（p_overview の page_index は body = [] で始まる）
    head = "def page_index(stats):\n    body = []\n"
    if "このサイトについて（日本語版）" not in s and head in s:
        note_html = (
            "    body.append('<div class=\"box info\"><b class=\"t\">このサイトについて（日本語版）</b>'\n"
            "                '<p>このサイトは中国語版コース <code>sap_cn</code>（SAP SD トレーニングコース）を'\n"
            "                '<b>日本語にしたもの</b>です。掲載している画面は原教材 <code>S4.docx</code> の'\n"
            "                '<b>中国語インターフェース</b>の実機スクリーンショットをそのまま使っているため、'\n"
            "                '本文の日本語と画面の中国語が食い違って見える箇所があります。その対応表が'\n"
            "                '<a href=\"glossary.html\">用語集</a>（日本語 ⇔ 画面の中国語 ⇔ 英語 / IMG パス対照）です。'\n"
            "                '設定手順（<a href=\"config.html\">設定</a>）では、各タスクの原文（中国語）を折りたたみで併記しています。</p></div>')\n")
        s = s.replace(head, head + note_html, 1)
    if "このサイトについて（日本語版）" not in s:
        print("p_overview.py: WARN ホームの説明を挿入できなかった（アンカー不一致）")
    # 用語集の見出し・ナビは p_jp 側で作るので、ここでは何もしない
    io.open(p, "w", encoding="utf-8").write(s)
    print("p_overview.py: TASK_JA %d 箇所 / ホームに日本語版の説明を追加" % n)


def main():
    patch_common()
    patch_build_pages()
    patch_xlsx()
    patch_js()
    patch_p_admin()
    patch_p_overview()
    return 0


if __name__ == "__main__":
    sys.exit(main())
