"""
5分・10分ごとに、加速(x1)・減速(x2)と心拍の変化の関係を式にする（1回ごとの加速・減速で測る版）

■ 1回の加速・減速
  加速度が A_ON 以上の状態が続いた区間 = 1回の加速（始点〜終点）
  加速度が −A_ON 以下の状態が続いた区間 = 1回の減速
  1回ごとに:  時間 d = 終点 − 始点 [秒]
              変化量 Δv = 終点の速度 − 始点の速度 [m/s]（減速は大きさ |Δv|）
  区間（0〜5分 など）をまたぐ加速・減速は、始まった区間に数える。

■ x1（加速）・x2（減速）の3通りの作り方
  ① 時間だけ   : x1 = Σ d（加速）          x2 = Σ d（減速）
  ② 変化量だけ : x1 = Σ Δv（加速）         x2 = Σ |Δv|（減速）
  ③ 時間×変化量: x1 = Σ (Δv × d)（加速）  x2 = Σ (|Δv| × d)（減速）

■ 式（①〜③それぞれ）
  終点心拍 = 出発心拍 + k1·x1 + k2·x2
  k1, k2 は1つの区間の値だけでは決まらないため、同じ試合の全区間から最小二乗法で求める。
  区間ごとに、その区間の x1, x2 を入れた式と、実際の終点心拍との差（残差）を出す。
  R²（決定係数）で①〜③のどれが心拍の変化をよく表すか比べられる。
  ※ 1試合分のデータから作る式なので、その試合の記述であり、予測式ではない。

入力: RAWデータ/ の CSV（読み込みと加速度の計算は hr_accel_line.py と同じ）
出力: output/hr_bouts/<ファイル名>_<5|10>min.csv  … 区間ごとの x1, x2（①〜③）と心拍
      output/hr_bouts/<ファイル名>_formulas.txt  … ①〜③の k1, k2, R² と区間ごとの式

使い方:
  python analysis/hr_window_bouts.py                                  # 心拍が残っている5ファイル（HR_OK_FILES）
  python analysis/hr_window_bouts.py "RAWデータ/Player_B_250712.csv"
  --speed-unit kmh|ms|auto
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from hr_accel_line import ROOT, load

A_ON = 0.5          # m/s²。加速度がこれ以上 = 加速中、−これ以下 = 減速中
MIN_BOUT_SEC = 1    # これより短い加速・減速は数えない
HR_EDGE_SEC = 5     # 出発・終点の心拍は、区間の最初・最後の5秒の平均
WINDOWS_MIN = (5, 10)

# 心拍がしっかり残っているデータだけを使う
HR_OK_FILES = ["Player_A_250628", "Player_B_250712", "Player_B_250802", "Player_B_250917", "Player_B_251015"]

MODELS = {
    "①時間だけ": ("x1_時間_秒", "x2_時間_秒"),
    "②変化量だけ": ("x1_変化量_m/s", "x2_変化量_m/s"),
    "③時間×変化量": ("x1_時間x変化量", "x2_時間x変化量"),
}


def find_bouts(s: pd.DataFrame) -> pd.DataFrame:
    """加速・減速を1回ずつ取り出す（始点時刻, 種類, 時間, 変化量）"""
    acc = s["acc"].to_numpy()
    v = s["speed"].to_numpy()
    rows = []
    for kind, mask in (("加速", acc >= A_ON), ("減速", acc <= -A_ON)):
        m = np.r_[False, mask, False].astype(int)
        starts = np.flatnonzero(np.diff(m) == 1)
        ends = np.flatnonzero(np.diff(m) == -1)      # 終わった次の位置
        for a, b in zip(starts, ends):
            d = b - a                                 # 1秒刻みなので個数 = 秒数
            if d < MIN_BOUT_SEC:
                continue
            v0 = v[a - 1] if a > 0 else v[a]          # 始点 = 加速（減速）が始まる直前の速度
            v1 = v[b - 1]                             # 終点 = 最後の1秒の速度
            dv = abs(v1 - v0)
            if np.isnan(dv):
                continue
            rows.append({"t": s.index[a], "種類": kind, "時間_秒": d, "変化量_m/s": dv})
    return pd.DataFrame(rows, columns=["t", "種類", "時間_秒", "変化量_m/s"])


def window_table(s: pd.DataFrame, bouts: pd.DataFrame, minutes: int) -> pd.DataFrame:
    t0 = s.index[0]
    rel_min = (s.index - t0).total_seconds() / 60
    b_min = (bouts["t"] - t0).dt.total_seconds() / 60 if len(bouts) else pd.Series(dtype=float)
    rows = []
    for start in range(0, int(np.ceil(rel_min.max() / minutes)) * minutes, minutes):
        w = s[(rel_min >= start) & (rel_min < start + minutes)]
        if len(w) < 2 * HR_EDGE_SEC:
            continue
        bw = bouts[(b_min >= start) & (b_min < start + minutes)]
        row = {"区間": f"{start}-{start + minutes}分"}
        for kind, x in (("加速", "x1"), ("減速", "x2")):
            k = bw[bw["種類"] == kind]
            row[f"{x}_回数"] = len(k)
            row[f"{x}_時間_秒"] = float(k["時間_秒"].sum())
            row[f"{x}_変化量_m/s"] = float(k["変化量_m/s"].sum())
            row[f"{x}_時間x変化量"] = float((k["時間_秒"] * k["変化量_m/s"]).sum())
        row["出発心拍_bpm"] = float(w["hr"].iloc[:HR_EDGE_SEC].mean())
        row["終点心拍_bpm"] = float(w["hr"].iloc[-HR_EDGE_SEC:].mean())
        row["心拍の変化_bpm"] = row["終点心拍_bpm"] - row["出発心拍_bpm"]
        rows.append(row)
    return pd.DataFrame(rows)


def fit(tab: pd.DataFrame, c1: str, c2: str):
    """ΔHR = k1·x1 + k2·x2 を全区間で最小二乗。区間が2つ未満なら求めない"""
    d = tab.dropna(subset=["心拍の変化_bpm"])
    if len(d) < 2:
        return np.nan, np.nan, np.nan
    X, y = d[[c1, c2]].to_numpy(), d["心拍の変化_bpm"].to_numpy()
    (k1, k2), *_ = np.linalg.lstsq(X, y, rcond=None)
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ((y - X @ np.array([k1, k2])) ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    return k1, k2, r2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="*", help="RAW CSV。省略すると HR_OK_FILES の5ファイル")
    ap.add_argument("--speed-unit", choices=["auto", "kmh", "ms"], default="auto")
    ap.add_argument("--out", default=str(ROOT / "output" / "hr_bouts"))
    args = ap.parse_args()

    files = [Path(p) for p in args.raw] or [ROOT / "RAWデータ" / f"{n}.csv" for n in HR_OK_FILES]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        print(f"== {f.name}")
        s = load(f, args.speed_unit)
        bouts = find_bouts(s)
        text = [f"{f.stem}（0分 = 記録の開始）", ""]
        for m in WINDOWS_MIN:
            tab = window_table(s, bouts, m)
            text.append(f"[{m}分ごと]  終点心拍 = 出発心拍 + k1·x1 + k2·x2")
            for name, (c1, c2) in MODELS.items():
                k1, k2, r2 = fit(tab, c1, c2)
                text.append(f" {name}: x1 = {c1}, x2 = {c2}")
                if np.isnan(k1):
                    text.append("   区間が足りないため k1, k2 を求められません")
                    continue
                text.append(f"   この試合の係数: k1 = {k1:.4f}, k2 = {k2:.4f}, R² = {r2:.2f}")
                pred = tab["出発心拍_bpm"] + k1 * tab[c1] + k2 * tab[c2]
                tab[f"{name}_式による終点心拍"] = pred
                tab[f"{name}_残差"] = tab["終点心拍_bpm"] - pred
                for (_, r), p in zip(tab.iterrows(), pred):
                    if np.isnan(r["心拍の変化_bpm"]):
                        text.append(f"   {r['区間']:>9}: 心拍欠測のため式なし")
                        continue
                    text.append(
                        f"   {r['区間']:>9}: {r['出発心拍_bpm']:.0f} + {k1:.4f}×{r[c1]:.1f}"
                        f" + {k2:.4f}×{r[c2]:.1f} = {p:.0f}"
                        f"  （実際 {r['終点心拍_bpm']:.0f}, 残差 {r['終点心拍_bpm'] - p:+.0f}）")
            text.append("")
            tab.to_csv(out_dir / f"{f.stem}_{m}min.csv", index=False, encoding="utf-8-sig")
        (out_dir / f"{f.stem}_formulas.txt").write_text("\n".join(text), encoding="utf-8")
        print(f"  出力: {out_dir / (f.stem + '_formulas.txt')} ほか")


if __name__ == "__main__":
    main()