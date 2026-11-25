"""
5分・10分ごとに「加速」と「心拍の変化」の関係を式にする

区間（0〜5分、5〜10分 … / 0〜10分、10〜20分 …）ごとに次を計算する:
  ① 加速時間 t_acc [秒]        … 加速度が A_ON 以上だった秒数
  ② 平均加速度 a_mean [m/s²]   … ①の間の加速度の平均
  ③ 速度の増加量 Δv [m/s]      … ①×②。区間の最初の速度を0として、加速で積み上がった速度
                                  （= Σ 加速度 × 時間）
  出発心拍 HR0 / 終点心拍 HR1 と、その差 ΔHR = HR1 − HR0

そして区間ごとに、その区間の値でぴったり成り立つ式を作る:
  HR1 = HR0 + k × Δv      （k = ΔHR / Δv … 速度が 1 m/s 積み上がるごとに心拍が何拍変わったか）

※ 1つの区間の値だけから作る式なので、その区間の事例の記述であり、予測式ではない。

入力: RAWデータ/ の CSV（読み込みと加速度の計算は hr_accel_line.py と同じ）
出力: output/hr_window/<ファイル名>_<5|10>min.csv   … 区間ごとの数値
      output/hr_window/<ファイル名>_formulas.txt   … 区間ごとの式

使い方:
  python analysis/hr_window_formula.py                                  # 心拍が残っている5ファイル（HR_OK_FILES）
  python analysis/hr_window_formula.py "RAWデータ/Player_B_250712.csv"
  --speed-unit kmh|ms|auto
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from hr_accel_line import ROOT, V_STOP, load

A_ON = 0.5          # m/s²。これ以上を「加速している」とみなす
HR_EDGE_SEC = 5     # 出発・終点の心拍は、区間の最初・最後の5秒の平均（1点だけだとブレるため）
WINDOWS_MIN = (5, 10)

# 心拍がしっかり残っているデータだけを使う
HR_OK_FILES = ["Player_A_250628", "Player_B_250712", "Player_B_250802", "Player_B_250917", "Player_B_251015"]


def window_table(s: pd.DataFrame, minutes: int) -> pd.DataFrame:
    t0 = s.index[0]
    rel_min = (s.index - t0).total_seconds() / 60
    rows = []
    for start in range(0, int(np.ceil(rel_min.max() / minutes)) * minutes, minutes):
        w = s[(rel_min >= start) & (rel_min < start + minutes)]
        if len(w) < 2 * HR_EDGE_SEC:
            continue
        acc = w["acc"]
        accel = (acc >= A_ON) & (w["speed"] >= V_STOP)
        t_acc = int(accel.sum())                                  # ① 秒（1秒刻みなので個数 = 秒数）
        a_mean = float(acc[accel].mean()) if t_acc else 0.0       # ②
        dv = float(acc[accel].sum())                              # ③ = Σ a×1秒 = ①×②
        hr0 = float(w["hr"].iloc[:HR_EDGE_SEC].mean())
        hr1 = float(w["hr"].iloc[-HR_EDGE_SEC:].mean())
        dhr = hr1 - hr0
        k = dhr / dv if dv > 0 else np.nan
        rows.append({
            "区間": f"{start}-{start + minutes}分",
            "①加速時間_秒": t_acc,
            "②平均加速度_m/s2": a_mean,
            "③速度の増加量_m/s": dv,
            "出発心拍_bpm": hr0,
            "終点心拍_bpm": hr1,
            "心拍の変化_bpm": dhr,
            "係数k_bpm_per_m/s": k,
        })
    return pd.DataFrame(rows)


def formula_lines(tab: pd.DataFrame, minutes: int) -> list[str]:
    lines = [f"[{minutes}分ごと]  式: 終点心拍 = 出発心拍 + k × (①加速時間 × ②平均加速度)"]
    for _, r in tab.iterrows():
        head = f"  {r['区間']:>9}:"
        if np.isnan(r["係数k_bpm_per_m/s"]) or np.isnan(r["心拍の変化_bpm"]):
            lines.append(f"{head} 加速なし（または心拍欠測）のため式なし"
                         f"  （心拍 {r['出発心拍_bpm']:.0f} → {r['終点心拍_bpm']:.0f}）")
            continue
        lines.append(
            f"{head} {r['終点心拍_bpm']:.0f} = {r['出発心拍_bpm']:.0f} + {r['係数k_bpm_per_m/s']:.3f}"
            f" × ({r['①加速時間_秒']}秒 × {r['②平均加速度_m/s2']:.2f} m/s² = {r['③速度の増加量_m/s']:.1f} m/s)"
        )
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", nargs="*", help="RAW CSV。省略すると HR_OK_FILES の5ファイル")
    ap.add_argument("--speed-unit", choices=["auto", "kmh", "ms"], default="auto")
    ap.add_argument("--out", default=str(ROOT / "output" / "hr_window"))
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
            tab.to_csv(out_dir / f"{f.stem}_{m}min.csv", index=False, encoding="utf-8-sig")
            text += formula_lines(tab, m) + [""]
        (out_dir / f"{f.stem}_formulas.txt").write_text("\n".join(text), encoding="utf-8")
        print(f"  出力: {out_dir / (f.stem + '_formulas.txt')} ほか")


if __name__ == "__main__":
    main()