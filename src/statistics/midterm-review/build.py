#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 questions.json 注入 template.html，產生單一檔案的複習網站。

輸出位置依本腳本自己的位置自動推算：

    src/<課程>/<單元>/build.py   →   docs/<課程>/<單元>/index.html

所以之後要新增章節，整個資料夾複製一份改名即可，這支腳本不必修改。

兩種輸出格式：

  --standalone（預設）  docs/<課程>/<單元>/index.html
      完整 HTML 文件，含 <!doctype>、<head>、<body> 與最小重置樣式。
      這是 GitHub Pages 提供服務、以及用瀏覽器直接開啟的版本。

  --artifact            dist/<單元>-artifact.html
      只有 <title>、<style>、頁面內容與 <script>，沒有文件外殼。
      Claude Artifact 發布時會自行包上外殼，用這個版本才不會重複。

用法（在本資料夾內執行）：
    python3 build_bank.py   # 產生 questions.json，含 121 項驗證
    python3 build.py     # 產生網站
"""

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "template.html"
QUESTIONS = HERE / "questions.json"

MARK = "/*__QUESTIONS__*/"


def find_root(start: pathlib.Path) -> pathlib.Path:
    """往上找到 src/ 的上一層，當作 repository 根目錄。"""
    for p in start.parents:
        if p.name == "src":
            return p.parent
    sys.exit("找不到 repository 根目錄：本腳本必須放在 src/<課程>/<單元>/ 底下")


ROOT = find_root(HERE)
REL = HERE.relative_to(ROOT / "src")      # 例如 statistics/ch5-discrete-distributions

# Claude Artifact 發布時會注入的最小重置樣式。做成獨立檔案時要自己補上，
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
    """切成「進 <head> 的部分」與「進 <body> 的部分」。

    模板結構是 <title> / <meta> / <link> / <style>…</style> 之後才是頁面內容，
    所以用最後一個 </style> 當分界點。
    """
    i = tpl.rfind("</style>")
    if i == -1:
        sys.exit("模板裡找不到 </style>，無法切分 head 與 body")
    cut = i + len("</style>")
    return tpl[:cut], tpl[cut:]


def main():
    ap = argparse.ArgumentParser(description="建置複習網站")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--standalone", action="store_true", help="完整 HTML 文件（預設）")
    g.add_argument("--artifact", action="store_true",
                   help="無文件外殼，供 Claude Artifact 發布")
    ap.add_argument("-o", "--out", help="自訂輸出路徑")
    args = ap.parse_args()

    if not QUESTIONS.exists():
        sys.exit(f"找不到 {QUESTIONS.name}，請先執行：python3 build_bank.py")

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
        out = (pathlib.Path(args.out) if args.out
               else ROOT / "dist" / f"{HERE.name}-artifact.html")
        html = tpl.replace(MARK, payload)
    else:
        out = pathlib.Path(args.out) if args.out else ROOT / "docs" / REL / "index.html"
        head, body = split_template(tpl.replace(MARK, payload))
        html = SKELETON_HEAD + head + SKELETON_MID + body + SKELETON_TAIL

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    m = data["meta"]
    rel = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"已產生 {rel}　{len(html.encode('utf-8'))/1024:.0f} KB")
    print(f"  選擇題 {m['n_mc']} 題　計算／簡答 {m['n_calc']} 大題（{m['n_parts']} 小題）")
    print(f"  講義相似範例佔比 {m['lecture_ratio']*100:.1f}%")


if __name__ == "__main__":
    main()
