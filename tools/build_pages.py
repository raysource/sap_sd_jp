# -*- coding: utf-8 -*-
"""SAP SD トレーニングコースサイトの全ページを生成します（冪等）。

    python3 tools/build_pages.py

統計数値（ページ数 / スクリーンショット数 / 自作図の数）はすべて生成結果から数え出します。手書きしません。
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitegen"))
import common  # noqa: E402
import p_overview as P1  # noqa: E402
import p_process as P2  # noqa: E402
import p_admin as P3  # noqa: E402
import p_jp  # noqa: E402

ROOT = common.ROOT

PAGES = [
    ("index.html", "ホーム · コースマップと学習ルート", "ホーム", P1.page_index),
    ("concept.html", "概念と位置づけ", "概念と位置づけ：SD は結局何を管理するのか", P1.page_concept),
    ("org.html", "組織構造", "組織構造：まずデータに座標を与える", P1.page_org),
    ("master.html", "マスタ", "マスタ：得意先、品目、価格", P1.page_master),
    ("pricing.html", "価格設定と条件技術", "価格設定：条件技術の 4 層構造", P1.page_pricing),
    ("flow.html", "エンドツーエンドプロセス", "エンドツーエンドプロセス：引合から入金まで", P2.page_flow),
    ("order.html", "受注伝票処理", "プロセス① 受注伝票の処理", P2.page_order),
    ("delivery.html", "納入と出庫過転記", "プロセス② 出荷伝票と出庫過転記", P2.page_delivery),
    ("billing.html", "請求と財務転記", "プロセス③ 請求と財務への転記", P2.page_billing),
    ("analysis.html", "分析とモニタリング", "分析とモニタリング：プロセスを管理する", P2.page_analysis),
    ("config.html", "設定ルート（48 タスク）", "設定ルート：48 タスクの完全な索引", P3.page_config),
    ("practice.html", "実習タスク", "実習：5 つの実習タスク", P3.page_practice),
    ("instructor.html", "講師用", "講師用：授業での進め方と評価方法", P3.page_instructor),
    ("worksheet.html", "受講者用（記入表）", "受講者用：記入表（印刷可）", P3.page_worksheet),
    ("quiz.html", "セルフチェックテスト（30 問）", "セルフチェックテスト：30 問", P3.page_quiz),
    ("glossary.html", "用語と T-code のクイックリファレンス", "用語と T-code のクイックリファレンス", p_jp.page_glossary),
]


def main():
    # まず本文に依存しない統計量を先に算出する
    stats = {"pages": len(PAGES), "tasks": len(common.SD_SOURCE),
             "shots": 0, "diagrams": 0, "steps": sum(len(t["steps"]) for t in common.SD_SOURCE)}
    bodies, meta = {}, {}
    for fn, title, kicker, func in PAGES:
        if fn == "index.html":
            continue
        body = func(stats)
        bodies[fn] = "\n".join(body)
        meta[fn] = (title, kicker)
    all_html = "\n".join(bodies.values())
    stats["shots"] = len(re.findall(r'<figure class="shot', all_html))
    stats["uniqueshots"] = len(set(re.findall(r'src="(assets/img/[^"]+)"', all_html)))
    stats["diagrams"] = len(re.findall(r'<figure class="dia', all_html))

    # トップページ（実際の統計数値を使用）。トップページ自体は自作図（マインドマップ）を 1 枚、スクリーンショットは 0 枚だけ使い、
    # 生成後にもう一度数え直してこの前提を確認する（記憶に頼らない）。
    body = "\n".join(P1.page_index(dict(stats, diagrams=stats["diagrams"] + 1)))
    bodies["index.html"] = body
    meta["index.html"] = ("ホーム · コースマップと学習ルート", "ホーム")
    final = "\n".join(bodies.values())
    n_shot2 = len(re.findall(r'<figure class="shot', final))
    n_dia2 = len(re.findall(r'<figure class="dia', final))
    if n_shot2 != stats["shots"] or n_dia2 != stats["diagrams"] + 1:
        print("WARN: トップページの統計の前提が成立しない（shot %d→%d / dia %d→%d）、実数でトップページを書き直す"
              % (stats["shots"], n_shot2, stats["diagrams"], n_dia2))
        stats["shots"], stats["diagrams"] = n_shot2, n_dia2
        bodies["index.html"] = "\n".join(P1.page_index(stats))
    else:
        stats["diagrams"] += 1

    written = []
    for fn, title, kicker, _f in PAGES:
        html = common.shell(fn, title, kicker, bodies[fn])
        path = os.path.join(ROOT, fn)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append((fn, len(html)))

    # サイトの自己申告統計（トレーニングサイト索引ページ hub 用）
    hub = {"n_pages": stats["pages"], "n_steps": stats["steps"], "figs": stats["shots"],
           "n_cfg": len(common.SD_SOURCE), "has_wbs": True,
           "note": "SAP SD トレーニングコースサイト（実際のスクリーンショット + 自作のフロー図/構造図/マインドマップ）"}
    with open(os.path.join(ROOT, "tools", "hub_stats.json"), "w", encoding="utf-8") as f:
        json.dump(hub, f, ensure_ascii=False, indent=1)

    print("pages: %d   スクリーンショット参照: %d（重複除去 %d）  自作図: %d   設定タスク: %d"
          % (stats["pages"], stats["shots"], stats["uniqueshots"], stats["diagrams"], stats["tasks"]))
    for fn, sz in written:
        print("  %-16s %7d bytes" % (fn, sz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
