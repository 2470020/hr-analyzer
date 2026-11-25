"""
5分・10分ごとに、加速(x1)・減速(x2)と心拍の変化の関係を式にする

区間（0〜5分、5〜10分 … / 0〜10分、10〜20分 …）ごとに次を計算する:
  加速: ① 加速時間 [秒]  ② 平均加速度 [m/s²]
        x1 = ①×② = Σ(加速度 × 時間)  … 区間の最初の速度を0として、加速で積み上がった速度 [m/s]
  減速: ① 減速時間 [秒]  ② 平均減速度 [m/s²]（大きさ）
        x2 = ①×② = Σ(|減速度| × 時間) … 減速で失った速度の合計 [m/s]
  出発心拍 HR0 / 終点心拍 HR1、ΔHR = HR1 − HR0

式:  HR1 = HR0 + k1·x1 + k2·x2
  k1, k2 は「1つの区間の値だけ」では決まらない（式1本に未知数2つ）。
  そのため、同じ試合の全区間を使って最小二乗法で k1, k2 を求め、
  区間ごとにその区間の x1, x2 を入れた式と、実際の終点心拍との差（残差）を出す。
  ※ 1試合分のデータから作る式なので、その試合の記述であり、予測式ではない。

入力: RAWデータ/ の CSV（読み込みと加速度の計算は hr_accel_line.py と同じ）
出力: output/hr_x1x2/<ファイル名>_<5|10>min.csv   … 区間ごとの数値
      output/hr_x1x2/<ファイル名>_formulas.txt   … k1, k2 と区間ごとの式

使い方:
  python analysis/hr_window_x1x2.py                                  # 心拍が残っている5ファイル（HR_OK_FILES）
  python analysis/hr_window_x1x2.py "RAWデータ/Player_B_250712.csv"
  --speed-unit kmh|ms|auto
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from hr_accel_line import ROOT, load

A_ON = 0.5          # m/s²。加速度がこれ以上 = 加速、−これ以下 = 減速
HR_EDGE_SEC = 5     # 出発・終点の心拍は、区間の最初・最後の5秒の平均（1点だけだとブレるため）
WINDOWS_MIN = (5, 10)

# 心拍がしっかり残っているデータだけを使う
HR_OK_FILES = ["Player_A_250628", "Player_B_250712", "Player_B_250802", "Player_B_250917", "Player_B_251015"]


def window_table(s: pd.DataFrame, minutes: int) -> pd.DataFrame:
    rel_min = (s.index - s.index[0]).total_seconds() / 60
    rows = []
    for start in range(0, int(np.ceil(rel_min.max() / minutes)) * minutes, minutes):
        w = s[(rel_min >= start) & (rel_min < start + minutes)]
        if len(w) < 2 * HR_EDGE_SEC:
            continue
        acc = w["acc"]
        up, down = acc >= A_ON, acc <= -A_ON
        t1, t2 = int(up.sum()), int(down.sum())          # 1秒刻みなので個数 = 秒数
        x1 = float(acc[up].sum())                        # Σ a × 1秒
        x2 = float(-acc[down].sum())                     # Σ |a| × 1秒
        hr0 = float(w["hr"].iloc[:HR_EDGE_SEC].mean())
        hr1 = float(w["hr"].iloc[-HR_EDGE_SEC:].mean())
        rows.append({
            "区間": f"{start}-{start + minutes}分",
            "加速時間_秒": t1,
            "平均加速度_m/s2": x1 / t1 if t1 else 0.0,
            "x1_加速の変化量_m/s": x1,
            "減速時間_秒": t2,
            "平均減速度_m/s2": x2 / t2 if t2 else 0.0,
            "x2_減速の変化量_m/s": x2,
            "出発心拍_bpm": hr0,
            "終点心拍_bpm": hr1,
            "心拍の変化_bpm": hr1 - hr0,
        })
    return pd.DataFrame(rows)


def fit_k(tab: pd.DataFrame):
    """ΔHR = k1·x1 + k2·x2 を全区間で最小二乗。区間が2つ未満なら求めない"""
    d = tab.dropna(subset=["心拍の変化_bpm"])
    if len(d) < 2:
        return np.nan, np.nan, np.nan
    X = d[["x1_加速の変化量_m/s", "x2_減速の変化量_m/s"]].to_numpy()
    y = d["心拍の変化_bpm"].to_numpy()
    (k1, k2), *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ np.array([k1, k2])
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ((y - pred) ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    return k1, k2, r2


def add_fit(tab: pd.DataFrame, k1: float, k2: float) -> pd.DataFrame:
    tab = tab.copy()
    tab["式による終点心拍_bpm"] = tab["出発心拍_bpm"] + k1 * tab["x1_加速の変化量_m/s"] + k2 * tab["x2_減速の変化量_m/s"]
    tab["残差_bpm"] = tab["終点心拍_bpm"] - tab["式による終点心拍_bpm"]
    return tab


def formula_lines(tab: pd.DataFrame, minutes: int, k1, k2, r2) -> list[str]:
    lines = [f"[{minutes}分ごと]  終点心拍 = 出発心拍 + k1·x1 + k2·x2"]
    if np.isnan(k1):
        return lines + ["  区間が足りないため k1, k2 を求められません", ""]
    lines.append(f"  この試合の係数: k1 = {k1:.3f}（加速 1 m/s あたりの心拍変化）, "
                 f"k2 = {k2:.3f}（減速 1 m/s あたり）, 決定係数 R² = {r2:.2f}")
    for _, r in tab.iterrows():
        if np.isnan(r["心拍の変化_bpm"]):
            lines.append(f"  {r['区間']:>9}: 心拍欠測のため式なし")
            continue
        lines.append(
            f"  {r['区間']:>9}: {r['出発心拍_bpm']:.0f} + {k1:.3f}×{r['x1_加速の変化量_m/s']:.1f}"
            f" + {k2:.3f}×{r['x2_減速の変化量_m/s']:.1f} = {r['式による終点心拍_bpm']:.0f}"
            f"  （実際 {r['終点心拍_bpm']:.0f}, 残差 {r['残差_bpm']:+.0f}）"
        )
    return lines + [""]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="*", help="RAW CSV。省略すると HR_OK_FILES の5ファイル")
    ap.add_argument("--speed-unit", choices=["auto", "kmh", "ms"], default="auto")
    ap.add_argument("--out", default=str(ROOT / "output" / "hr_x1x2"))
    args = ap.parse_args()

    files = [Path(p) for p in args.raw] or [ROOT / "RAWデータ" / f"{n}.csv" for n in HR_OK_FILES]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in files:
        print(f"== {f.name}")
        s = load(f, args.speed_unit)
        text = [f"{f.stem}（0分 = 記録の開始）", ""]
        for m in WINDOWS_MIN:
            tab = window_table(s, m)
            k1, k2, r2 = fit_k(tab)
            if not np.isnan(k1):
                tab = add_fit(tab, k1, k2)
            tab.to_csv(out_dir / f"{f.stem}_{m}min.csv", index=False, encoding="utf-8-sig")
            text += formula_lines(tab, m, k1, k2, r2)
        (out_dir / f"{f.stem}_formulas.txt").write_text("\n".join(text), encoding="utf-8")
        print(f"  出力: {out_dir / (f.stem + '_formulas.txt')} ほか")


if __name__ == "__main__":
    main()