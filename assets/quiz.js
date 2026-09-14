/* ============================================================
   RAP トレーニングサイト - 理解度テストスクリプト
   自動採点: 選択肢をクリック -> 即時に採点 -> 解説を表示 -> 得点を集計
   ============================================================ */
(function () {
  "use strict";

  function scoreBox() {
    var sb = document.getElementById("quiz-score");
    if (sb) return sb;
    var div = document.createElement("div");
    div.id = "quiz-score";
    div.className = "panel";
    div.style.cssText = "position:sticky;top:76px;z-index:30;";
    div.innerHTML =
      '<b class="t">成績</b>' +
      '<div class="scorebar"><i id="quiz-bar" style="width:0%"></i></div>' +
      '<p id="quiz-text" style="margin:4px 0 0">未回答 / 全 0 問</p>';
    var wrap = document.querySelector("main.page .wrap article") ||
               document.querySelector("main.page") ||
               document.body;
    wrap.insertBefore(div, wrap.firstChild);
    return div;
  }

  function refresh() {
    var qs = document.querySelectorAll(".quiz-q");
    var total = qs.length;
    var done = 0, correct = 0;
    qs.forEach(function (q) {
      if (q.classList.contains("answered")) done++;
      if (q.classList.contains("right")) correct++;
    });
    var pct = total ? Math.round(correct / total * 100) : 0;
    var bar = document.getElementById("quiz-bar");
    if (bar) bar.style.width = pct + "%";
    var txt = document.getElementById("quiz-text");
    if (!txt) return;
    var grade = "";
    if (total && done === total) {
      grade = pct >= 90 ? "★★★ 優秀 (90% 以上)" :
              pct >= 75 ? "★★☆ 良好 (75% 以上)" :
              pct >= 60 ? "★☆☆ 合格 (60% 以上)" : "✗ 未達成 (<60%) —— 対応する手順編に戻って復習してください";
    }
    txt.innerHTML = "回答済み" + done + " / " + total +
      "· 正解" + correct + "· 正答率" + pct + "% " + grade;
  }

  document.addEventListener("click", function (e) {
    var opt = e.target.closest(".opt");
    if (!opt) return;
    var q = opt.closest(".quiz-q");
    if (!q || q.classList.contains("answered")) return;
    var answer = (q.getAttribute("data-answer") || "").trim().toUpperCase();
    var key = (opt.getAttribute("data-key") || "").trim().toUpperCase();
    q.classList.add("answered");
    if (key === answer) {
      q.classList.add("right");
      opt.classList.add("correct");
    } else {
      opt.classList.add("wrong");
      q.querySelectorAll(".opt").forEach(function (o) {
        if ((o.getAttribute("data-key") || "").trim().toUpperCase() === answer) {
          o.classList.add("correct");
        }
      });
    }
    q.classList.add("show-exp");
    refresh();
  });

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-reset]");
    if (!btn) return;
    document.querySelectorAll(".quiz-q").forEach(function (q) {
      q.classList.remove("answered", "right", "wrong", "show-exp");
      q.querySelectorAll(".opt").forEach(function (o) {
        o.classList.remove("correct", "wrong");
      });
    });
    refresh();
  });

  document.addEventListener("DOMContentLoaded", function () {
    if (document.querySelector(".quiz-q")) {
      scoreBox();
      refresh();
      var reset = document.createElement("button");
      reset.className = "copy-btn";
      reset.setAttribute("data-reset", "1");
      reset.textContent = "すべてやり直す ↺";
      reset.style.cssText = "margin:0 0 4px 8px;background:#2a4154;";
      var h = document.querySelector(".quiz-q .q-meta");
      var firstQ = document.querySelector(".quiz-q");
      if (firstQ) {
        var host = firstQ.parentNode;
        var p = document.createElement("p");
        p.appendChild(reset);
        host.insertBefore(p, firstQ);
      }
    }
  });
})();
