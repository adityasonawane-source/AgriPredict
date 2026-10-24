"""Turn the ICRISAT district-level file into a training table.

Usage:  python prepare_icrisat.py icrisat.csv data/training.csv
(The original download is a legacy .xls; convert it first, e.g.
 soffice --headless --convert-to csv:"Text - txt - csv (StarCalc)":44,34,76,1 file.xls)

Each output row is one district-year-crop with the weather of that crop's growing window:
  Kharif crops: Jun-Sep.   Rabi crops: Oct-Dec of the year plus Jan-Feb of the next.
Rainfall is summed over the months (the file's seasonal columns are monthly means).
Temperature is the mean of monthly max and min temperature over the window.
"""
import sys
import pandas as pd

CROPS = {"RICE": ("Rice", "Kharif"), "PEARL MILLET": ("Pearl millet", "Kharif"),
         "GROUNDNUT": ("Groundnut", "Kharif"), "CHICKPEA": ("Chickpea", "Rabi")}
MON = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER",
       "OCTOBER", "NOVEMBER", "DECEMBER"]
STATE_FIX = {"Orissa": "Odisha"}


def main(src, dst):
    df = pd.read_csv(src, low_memory=False)
    num = lambda c: pd.to_numeric(df[c], errors="coerce")
    for m in MON:
        df[f"R_{m}"] = num(f"{m} PERCIPITATION (Millimeters)")
        df[f"T_{m}"] = (num(f"{m} MAXIMUM TEMPERATURE (Centigrate)") + num(f"{m} MINIMUM TEMPERATURE (Centigrate)")) / 2
    key = ["Dist Code", "Year"]
    nxt = df[key + ["R_JANUARY", "R_FEBRUARY", "T_JANUARY", "T_FEBRUARY"]].copy()
    nxt["Year"] -= 1                                        # next year's Jan-Feb joins this year's row
    df = df.merge(nxt, on=key, how="left", suffixes=("", "_nx"))
    win = {
        "Kharif": (df[[f"R_{m}" for m in MON[5:9]]].sum(axis=1, min_count=4),
                   df[[f"T_{m}" for m in MON[5:9]]].mean(axis=1)),
        "Rabi": (df[["R_OCTOBER", "R_NOVEMBER", "R_DECEMBER", "R_JANUARY_nx", "R_FEBRUARY_nx"]].sum(axis=1, min_count=5),
                 df[["T_OCTOBER", "T_NOVEMBER", "T_DECEMBER", "T_JANUARY_nx", "T_FEBRUARY_nx"]].mean(axis=1)),
    }
    out = []
    for col, (name, season) in CROPS.items():
        y = pd.to_numeric(df[f"{col} YIELD (Kg per ha)"], errors="coerce")
        part = pd.DataFrame(dict(crop=name, region=df["State Name"].replace(STATE_FIX), district=df["Dist Name"],
                                 year=df["Year"], temp=win[season][1], rain=win[season][0], yield_kg_ha=y))
        out.append(part)
    t = pd.concat(out).dropna()
    t = t[t.yield_kg_ha > 0]
    t.round(2).to_csv(dst, index=False)
    print(len(t), "rows"); print(t.groupby("crop").yield_kg_ha.agg(["count", "median"]))


if __name__ == "__main__":
    main(*sys.argv[1:3])
