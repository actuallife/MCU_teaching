#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""題庫共用工具：各章模組都從這裡取用 mc()、calc() 與計算函式。

設計原則
  1. 所有答案與詳解中的數字一律由程式計算，不手動輸入。
  2. lecture=True 代表「課堂講義相似範例」（換情境、換數字，解法結構相同）。
  3. 每題都帶章別，網站才能做跨章節的出卷與弱點分析。
"""

from math import comb, exp, factorial, sqrt   # noqa: F401  （各章模組會用到）

# ───────────────────────────────── 章別

CHAPTERS = {
    1: "統計概論與資料",
    2: "敘述統計：表格與圖形",
    3: "敘述統計：數值量數",
    4: "機率基礎概念",
    5: "離散機率分配",
}

_ctx = {"ch": None}


def chapter(n):
    """各章模組在最上方呼叫一次，之後該模組新增的題目都歸這一章。"""
    assert n in CHAPTERS, n
    _ctx["ch"] = n


# ───────────────────────────────── 題目登錄

MC, CALC = [], []


def mc(id_, topic, src, lecture, q, opts, ans, exp_, table=None):
    """新增一題選擇題。ans 是正解在 opts 裡的索引（0 起算）。"""
    ch = _ctx["ch"]
    assert ch, f"{id_}：模組最上方忘了呼叫 chapter()"
    assert len(opts) == 4, f"{id_} 需要四個選項"
    assert len(set(opts)) == 4, f"{id_} 選項重複"
    assert 0 <= ans < 4, f"{id_} 正解索引不合法"
    MC.append({"id": id_, "ch": ch, "chapter": CHAPTERS[ch], "topic": topic,
               "src": src, "lecture": lecture, "q": q, "table": table,
               "opts": opts, "ans": ans, "exp": exp_})


def calc(id_, topic, src, lecture, stem, parts, table=None, note=None):
    """新增一題計算／簡答大題。parts 是小題清單。

    數值小題　{"label","type":"num","q","ans","tol","sol","unit"?,"wide"?}
    簡答小題　{"label","type":"text","q","ref","rubric":[...]}
    """
    ch = _ctx["ch"]
    assert ch, f"{id_}：模組最上方忘了呼叫 chapter()"
    for p in parts:
        if p["type"] == "num":
            assert "ans" in p and "tol" in p, (id_, p["label"])
            assert p.get("sol", "").strip(), (id_, p["label"], "缺解題步驟")
        else:
            assert p.get("ref", "").strip(), (id_, p["label"], "缺參考答案")
            assert len(p.get("rubric", [])) >= 2, (id_, p["label"], "評分要點不足")
    CALC.append({"id": id_, "ch": ch, "chapter": CHAPTERS[ch], "topic": topic,
                 "src": src, "lecture": lecture, "stem": stem, "table": table,
                 "parts": parts, "note": note})


# ───────────────────────────────── 格式化

def r(v, k=4):
    return round(v + 0.0, k)


def fmt(v, k=4):
    """去掉無意義的尾端 0，讓詳解裡的數字好讀。"""
    s = f"{v:.{k}f}".rstrip("0").rstrip(".")
    return s if s else "0"


def th(v):
    """千分位，給金額用。"""
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"


# ───────────────────────────────── 敘述統計

def mean(xs):
    return sum(xs) / len(xs)


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def lp(xs, p):
    """課本第 15 版百分位數：L = (p/100)(n+1)，非整數時線性內插。

    回傳 (位置 L, 數值)。
    """
    s = sorted(xs)
    n = len(s)
    L = p / 100 * (n + 1)
    lo = int(L)
    frac = round(L - lo, 10)
    if frac == 0:
        return L, float(s[lo - 1])
    return L, s[lo - 1] + frac * (s[lo] - s[lo - 1])


def svar(xs):
    """樣本變異數，分母 n − 1。"""
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def ssd(xs):
    return sqrt(svar(xs))


def cv(xs):
    """變異係數，百分比。"""
    return ssd(xs) / mean(xs) * 100


def zscore(x, xs):
    return (x - mean(xs)) / ssd(xs)


def five_num(xs):
    """五數彙總 (min, Q1, Q2, Q3, max)，四分位數用課本 Lp 公式。"""
    s = sorted(xs)
    return (float(s[0]), lp(s, 25)[1], lp(s, 50)[1], lp(s, 75)[1], float(s[-1]))


def fences(xs):
    """1.5 × IQR 的內圍界限 (下界, 上界)。"""
    _, q1, _, q3, _ = five_num(xs)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def outliers(xs):
    lo, hi = fences(xs)
    return [x for x in sorted(xs) if x < lo or x > hi]


def scov(xs, ys):
    """樣本共變異數，分母 n − 1。"""
    mx, my = mean(xs), mean(ys)
    return sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (len(xs) - 1)


def corr(xs, ys):
    return scov(xs, ys) / (ssd(xs) * ssd(ys))


def wmean(xs, ws):
    return sum(w * x for x, w in zip(xs, ws)) / sum(ws)


# ───────────────────────────────── 機率

def binom(n, p, x):
    return comb(n, x) * p ** x * (1 - p) ** (n - x)


def pois(mu, x):
    return mu ** x * exp(-mu) / factorial(x)


def dist_stats(xs, fs):
    """由離散機率分配算 (μ, E(X²), σ², σ)。"""
    assert abs(sum(fs) - 1) < 1e-12, f"機率總和 = {sum(fs)}"
    assert all(f >= 0 for f in fs)
    mu = sum(x * f for x, f in zip(xs, fs))
    ex2 = sum(x * x * f for x, f in zip(xs, fs))
    var = ex2 - mu * mu
    return mu, ex2, var, sqrt(var)
