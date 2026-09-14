/* ============================================================
   SAP S/4HANA トレーニングコースサイト（S4CN）— サイトスクリプト
   - 実機スクリーンショットのライトボックス（クリックで拡大、1x/2x/3x、ESC で閉じる）— 外部依存なし、file:// で直接利用可能
   - タスク索引ページのローカル絞り込み（ネット接続なし、fetch 不使用）
   ============================================================ */
(function () {
  "use strict";

  /* ---------------- ライトボックス ---------------- */
  var lb = null, lbImg = null, lbBar = null, zoom = 1, natW = 0, natH = 0;

  function build() {
    lb = document.createElement("div");
    lb.id = "sd-lightbox";
    lbImg = document.createElement("img");
    lbBar = document.createElement("div");
    lbBar.className = "lb-bar";
    lb.appendChild(lbImg);
    lb.appendChild(lbBar);
    document.body.appendChild(lb);
    lb.addEventListener("click", function (e) {
      if (e.target === lb) close();
    });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("show")) return;
      if (e.key === "Escape") close();
      if (e.key === "+" || e.key === "=") setZoom(zoom + 1);
      if (e.key === "-") setZoom(zoom - 1);
    });
  }

  function setZoom(z) {
    zoom = Math.min(4, Math.max(1, z));
    lbImg.style.width = Math.round(natW * zoom) + "px";
    lbImg.style.maxWidth = "none";
    lbImg.style.maxHeight = "none";
    renderBar();
  }

  function renderBar() {
    var pct = Math.round(zoom * 100) + "%";
    lbBar.innerHTML =
      '<span class="dim">' + lbImg.getAttribute("data-file") + "</span>" +
      '<span>' + (lbImg.getAttribute("data-cap") || "") + "</span>" +
      '<span style="flex:1 1 auto"></span>' +
      '<span class="dim">' + natW + "×" + natH + "</span>" +
      '<button class="zoombtn" data-z="1">1×</button>' +
      '<button class="zoombtn" data-z="2">2×</button>' +
      '<button class="zoombtn" data-z="3">3×</button>' +
      '<span class="dim">現在' + pct + "</span>" +
      '<button class="zoombtn" data-close="1">閉じる (ESC)</button>';
    var btns = lbBar.querySelectorAll(".zoombtn");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function (e) {
        e.stopPropagation();
        if (this.getAttribute("data-close")) { close(); return; }
        setZoom(parseInt(this.getAttribute("data-z"), 10));
      });
    }
  }

  function open(a) {
    if (!lb) build();
    var img = a.querySelector("img");
    if (!img) return;
    natW = img.naturalWidth || img.width;
    natH = img.naturalHeight || img.height;
    var fig = a.closest("figure.shot");
    var cap = "";
    if (fig) {
      var c = fig.querySelector("figcaption");
      if (c) cap = (c.querySelector(".cap") ? c.querySelector(".cap").textContent : c.textContent) || "";
    }
    var src = img.getAttribute("src");
    lbImg.setAttribute("src", src);
    lbImg.setAttribute("data-file", src.split("/").pop());
    lbImg.setAttribute("data-cap", cap.slice(0, 90));
    lb.classList.add("show");
    zoom = 1;
    lbImg.style.width = "auto";
    lbImg.style.maxWidth = "96vw";
    lbImg.style.maxHeight = "88vh";
    renderBar();
  }

  function close() {
    if (lb) lb.classList.remove("show");
    if (lbImg) lbImg.removeAttribute("src");
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("figure.shot a.zoom") : null;
    if (!a) return;
    e.preventDefault();
    open(a);
  });

  /* ---------------- タスク索引の絞り込み ---------------- */
  function initFilter() {
    var box = document.getElementById("taskfilter");
    var tbl = document.getElementById("idxtable");
    if (!box || !tbl) return;
    var rows = [].slice.call(tbl.querySelectorAll("tbody tr"));
    var count = document.getElementById("hitcount");
    var mod = "all";
    var chips = [].slice.call(document.querySelectorAll(".filterbar .chip"));
    function apply() {
      var q = box.value.trim().toLowerCase();
      var n = 0;
      rows.forEach(function (tr) {
        var okm = mod === "all" || tr.getAttribute("data-mod") === mod;
        var okt = !q || (tr.getAttribute("data-key") || "").toLowerCase().indexOf(q) >= 0;
        var show = okm && okt;
        tr.style.display = show ? "" : "none";
        if (show) n++;
      });
      if (count) count.textContent = "表示 " + n + " / " + rows.length + " 件";
    }
    box.addEventListener("input", apply);
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        mod = this.getAttribute("data-mod");
        chips.forEach(function (x) { x.classList.remove("on"); });
        this.classList.add("on");
        apply();
      });
    });
    apply();
  }

  /* ---------------- 画面表示サイズ（投影用） ---------------- */
  function initSizer() {
    var figs = document.querySelectorAll("figure.shot");
    if (!figs.length) return;
    var key = "sd-shot-scale";
    var scale = parseFloat(localStorage.getItem(key) || "1");
    if (!(scale > 0)) scale = 1;
    var bar = document.createElement("div");
    bar.className = "filterbar";
    bar.id = "shot-scale-bar";
    bar.innerHTML = '<span class="dim">画面表示サイズ：</span>' +
      '<span class="chip" data-s="1">1×</span>' +
      '<span class="chip" data-s="1.5">1.5×</span>' +
      '<span class="chip" data-s="2">2×</span>' +
      '<span class="dim">（投影／教室では 1.5×〜2× を推奨。画面自体をクリックすると 4× まで拡大）</span>';
    var host = document.querySelector("main.page article");
    if (!host) return;
    host.insertBefore(bar, host.firstChild);
    var chips = [].slice.call(bar.querySelectorAll(".chip"));

    function apply() {
      chips.forEach(function (c) {
        c.classList.toggle("on", parseFloat(c.getAttribute("data-s")) === scale);
      });
      var list = document.querySelectorAll("figure.shot img");
      for (var i = 0; i < list.length; i++) {
        var img = list[i];
        if (scale === 1) { img.style.width = ""; img.style.maxWidth = ""; continue; }
        var nat = img.naturalWidth || parseInt(img.getAttribute("width"), 10) || 0;
        if (!nat) continue;
        var holder = img.parentElement || img;
        var cap = holder.clientWidth || 900;
        var want = Math.round(nat * scale);
        img.style.maxWidth = "none";
        img.style.width = Math.min(want, cap) + "px";
      }
    }
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        scale = parseFloat(this.getAttribute("data-s"));
        try { localStorage.setItem(key, String(scale)); } catch (e) {}
        apply();
      });
    });
    window.addEventListener("load", apply);
    apply();
  }

  /* ---------------- パス行のワンクリックコピー ---------------- */
  function initPathCopy() {
    var ps = document.querySelectorAll(".pathline[data-copy]");
    for (var i = 0; i < ps.length; i++) {
      (function (el) {
        el.style.cursor = "copy";
        el.title = "クリックしてパスをコピー";
        el.addEventListener("click", function () {
          var t = el.getAttribute("data-copy");
          var done = function () {
            var old = el.style.outline;
            el.style.outline = "2px solid #177245";
            setTimeout(function () { el.style.outline = old; }, 500);
          };
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(t).then(done, done);
          } else {
            var ta = document.createElement("textarea");
            ta.value = t; document.body.appendChild(ta); ta.select();
            try { document.execCommand("copy"); } catch (e) {}
            document.body.removeChild(ta); done();
          }
        });
      })(ps[i]);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initFilter();
    initPathCopy();
    initSizer();
  });
})();
