#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 data/questions.json 注入 src/template.html，產生單一檔案的複習網站。

兩種輸出格式：

  --standalone（預設）  docs/index.html
      完整的 HTML 文件，含 <!doctype>、<head>、<body> 與最小重置樣式。
      這是放到 GitHub Pages、或用瀏覽器直接開啟的版本。

  --artifact            dist/artifact.html
      只有 <title>、<style>、頁面內容與 <script>，沒有文件外殼。
      Claude Artifact 發布時會自行包上外殼，用這個版本才不會重複。

用法：
    python3 src/bank.py          # 先產生 data/questions.json（含 24 項驗證）
    python3 src/build.py         # 再產生 docs/index.html
"""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "template.html"
QUESTIONS = ROOT / "data" / "questions.json"

MARK = "/*__QUESTIONS__*/"

# Claude Artifact 在發布時注入的最小重置樣式。做成獨立檔案時要自己補上，
# 否則頁面會少掉 body 歸零、安全區內距與 [hidden] 規則。
SKELETON_HEAD = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root{color-scheme:light;
  padding-top:env(safe-area-inset-top,0px);
  padding-bottom:env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px system-ui,-apple-system,"Segoe UI",sans-serif}
img{max-width:100%}
[hidden]{display:none!important}
</style>
"""

SKELETON_MID = """</head>
<body>
"""

SKELETON_TAIL = """</body>
</html>
"""


def split_template(tpl: str):
    """把模板切成「進 <head> 的部分」與「進 <body> 的部分」。

    模板的結構是：<title> / <meta> / <link> / <style>…</style> 之後才是頁面內容，
    所以用最後一個 </style> 當分界點。
    """
    i = tpl.rfind("</style>")
    if i == -1:
        sys.exit("模板裡找不到 </style>，無法切分 head 與 body")
    cut = i + len("</style>")
    return tpl[:cut], tpl[cut:]


def main():
    ap = argparse.ArgumentParser(description="建置離散機率分配複習網站")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--standalone", action="store_true",
                   help="產生完整 HTML 文件到 docs/index.html（預設）")
    g.add_argument("--artifact", action="store_true",
                   help="產生無文件外殼的版本到 dist/artifact.html")
    ap.add_argument("-o", "--out", help="自訂輸出路徑")
    args = ap.parse_args()

    if not QUESTIONS.exists():
        sys.exit(f"找不到 {QUESTIONS}，請先執行：python3 src/bank.py")

    data = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    tpl = TEMPLATE.read_text(encoding="utf-8")
    if MARK not in tpl:
        sys.exit("模板缺少注入點 " + MARK)

    # ensure_ascii=False 保留中文可讀；把 < escape 成 \\u003c，
    # 避免題目內的 HTML 標籤（例如 </b>）提前把 <script> 關掉。
    payload = json.dumps(data, ensure_ascii=False,
                         separators=(",", ":")).replace("<", "\\u003c")
    assert "</script>" not in payload

    if args.artifact:
        out = pathlib.Path(args.out) if args.out else ROOT / "dist" / "artifact.html"
        html = tpl.replace(MARK, payload)
    else:
        out = pathlib.Path(args.out) if args.out else ROOT / "docs" / "index.html"
        head, body = split_template(tpl.replace(MARK, payload))
        html = SKELETON_HEAD + head + SKELETON_MID + body + SKELETON_TAIL

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    m = data["meta"]
    kb = len(html.encode("utf-8")) / 1024
    rel = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"已產生 {rel}　{kb:.0f} KB")
    print(f"  選擇題 {m['n_mc']} 題　計算／簡答 {m['n_calc']} 大題（{m['n_parts']} 小題）")
    print(f"  講義相似範例佔比 {m['lecture_ratio']*100:.1f}%")


if __name__ == "__main__":
    main()
