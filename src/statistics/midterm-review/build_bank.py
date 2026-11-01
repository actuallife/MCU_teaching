#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""匯總 bank/ 底下各章題庫，執行全域驗證，輸出 questions.json。

用法（在本資料夾內執行）：
    python3 build_bank.py
    python3 build_bank.py --check 舊題庫.csv     # 另外檢查題號是否與既有題庫衝突
"""

import argparse
import csv
import json
import pathlib
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "bank"))

import common                                   # noqa: E402
import ch1, ch2, ch3, ch4, ch5                  # noqa: E402,F401

MC, CALC = common.MC, common.CALC
CHAPTERS = common.CHAPTERS

# ───────────────────────────────── 驗證

checks = []


def chk(label, cond, detail=""):
    checks.append((label, bool(cond), detail))


ids = [q["id"] for q in MC] + [q["id"] for q in CALC]
chk("題號 ID 無重複", len(ids) == len(set(ids)),
    f"共 {len(ids)} 題" + ("" if len(ids) == len(set(ids))
                          else "；重複：" + "、".join(
                              i for i, c in Counter(ids).items() if c > 1)))

chk("每題選擇題都有四個相異選項",
    all(len(q["opts"]) == 4 and len(set(q["opts"])) == 4 for q in MC))
chk("選擇題正解索引合法", all(0 <= q["ans"] < 4 for q in MC))
chk("選擇題都有詳解", all(q["exp"].strip() for q in MC))
chk("選擇題都有出處", all(q["src"].strip() for q in MC))

n_parts = sum(len(q["parts"]) for q in CALC)
n_num = sum(1 for q in CALC for p in q["parts"] if p["type"] == "num")
n_text = n_parts - n_num
chk("數值小題都有容許誤差",
    all(p["tol"] >= 0 for q in CALC for p in q["parts"] if p["type"] == "num"))
chk("數值小題都有解題步驟",
    all(p.get("sol", "").strip() for q in CALC for p in q["parts"] if p["type"] == "num"))
chk("簡答小題都有參考答案與至少兩項評分要點",
    all(p.get("ref", "").strip() and len(p.get("rubric", [])) >= 2
        for q in CALC for p in q["parts"] if p["type"] == "text"))
chk("每大題至少一個數值小題或兩個簡答小題",
    all(any(p["type"] == "num" for p in q["parts"]) or len(q["parts"]) >= 2
        for q in CALC))

lec = sum(1 for q in MC if q["lecture"]) + sum(1 for q in CALC if q["lecture"])
ratio = lec / len(ids)
chk("講義相似範例佔比 ≥ 70%", ratio >= 0.70, f"{lec}/{len(ids)} = {ratio*100:.1f}%")

chk("五個章節都有題目",
    {q["ch"] for q in MC} == set(CHAPTERS) and {q["ch"] for q in CALC} == set(CHAPTERS))

for c in sorted(CHAPTERS):
    m = sum(1 for q in MC if q["ch"] == c)
    k = sum(1 for q in CALC if q["ch"] == c)
    chk(f"第 {c} 章題數足夠出卷", m >= 8 and k >= 2, f"選擇 {m}　計算 {k}")

# 表格欄數一致
for q in MC + CALC:
    t = q.get("table")
    if t:
        chk(f"{q['id']} 表格欄數一致",
            all(len(row) == len(t["head"]) for row in t["rows"]))
for q in CALC:
    for p in q["parts"]:
        w = p.get("wide")
        if w:
            chk(f"{q['id']} {p['label']} 寬表欄數一致",
                all(len(row) == len(w["head"]) for row in w["rows"]))

# 數值答案必須是數字且容許誤差合理
for q in CALC:
    for p in q["parts"]:
        if p["type"] == "num":
            ok = isinstance(p["ans"], (int, float)) and p["tol"] >= 0
            if p["ans"] != 0:
                ok = ok and p["tol"] <= max(abs(p["ans"]) * 0.2, 1e-6)
            chk(f"{q['id']} {p['label']} 答案與容許誤差合理", ok,
                f"ans={p['ans']} tol={p['tol']}")

topics = sorted({q["topic"] for q in MC} | {q["topic"] for q in CALC})
chk("主題數量合理", len(topics) >= 15, f"{len(topics)} 個主題")

all_ok = all(ok for _, ok, _ in checks)

# ───────────────────────────────── 輸出

out = {
    "meta": {
        "course": "統計學（一）",
        "scope": "期中考範圍　第 1 – 5 章",
        "chapters": [{"ch": c, "name": CHAPTERS[c],
                      "n_mc": sum(1 for q in MC if q["ch"] == c),
                      "n_calc": sum(1 for q in CALC if q["ch"] == c)}
                     for c in sorted(CHAPTERS)],
        "n_mc": len(MC), "n_calc": len(CALC), "n_parts": n_parts,
        "n_num": n_num, "n_text": n_text,
        "lecture_ratio": round(ratio, 4),
        "topics": topics,
    },
    "mc": MC, "calc": CALC,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", metavar="舊題庫.csv", help="檢查題號是否與既有題庫衝突")
    args = ap.parse_args()

    print(f"選擇題 {len(MC)} 題　計算／簡答題 {len(CALC)} 大題"
          f"（{n_parts} 小題：數值 {n_num}、簡答 {n_text}）")
    print(f"講義相似範例：{lec}/{len(ids)} = {ratio*100:.1f}%\n")

    print(f"{'章':<4}{'章名':<22}{'選擇':>6}{'計算':>6}{'講義題':>8}")
    print("─" * 48)
    for c in sorted(CHAPTERS):
        m = [q for q in MC if q["ch"] == c]
        k = [q for q in CALC if q["ch"] == c]
        l_ = sum(1 for q in m + k if q["lecture"])
        print(f"{c:<4}{CHAPTERS[c]:<22}{len(m):>6}{len(k):>6}{l_:>8}")

    print("\n驗證")
    bad = 0
    for label, ok, detail in checks:
        if not ok:
            bad += 1
            print(f"  [✗] {label}" + (f"　{detail}" if detail else ""))
    if bad == 0:
        print(f"  全部 {len(checks)} 項檢查通過")
    else:
        print(f"\n★ {bad} 項未通過，未輸出 questions.json ★")
        sys.exit(1)

    if args.check:
        old = set()
        with open(args.check, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                v = row.get("題號ID") or row.get("id")
                if v:
                    old.add(v.strip())
        clash = sorted(set(ids) & old)
        print(f"\n題號衝突檢查：既有 {len(old)} 題，"
              + (f"衝突 {len(clash)} 題 → {'、'.join(clash)}" if clash else "無衝突"))

    dst = HERE / "questions.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n已輸出 {dst.name}　{dst.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
