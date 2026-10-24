
import argparse
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

CAT = ["crop", "region", "district"]
NUM = ["year", "temp", "rain"]


def make():
    return Pipeline([
        ("prep", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT)
        ], remainder="passthrough")),
        ("gbr", GradientBoostingRegressor(
            n_estimators=400,
            max_depth=6,
            learning_rate=0.04,
            subsample=0.8,
            min_samples_leaf=20,
            random_state=1
        )),
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/training.csv")
    ap.add_argument("--split", type=int, default=2009)
    a = ap.parse_args()

    t = pd.read_csv(a.csv)
    t = t[
        (t.yield_kg_ha < t.groupby("crop").yield_kg_ha.transform(
            lambda s: s.quantile(0.995)
        ))
        & (t.temp > 5)
    ]

    tr = t[t.year <= a.split]
    te = t[t.year > a.split]

    # Evaluate using years not used for training.
    p = make().fit(tr[CAT + NUM], tr.yield_kg_ha)
    pred = p.predict(te[CAT + NUM])

    # Baseline: historical average by crop and region.
    avg = tr.groupby(["crop", "region"]).yield_kg_ha.mean().to_dict()
    b = np.array([avg.get(k, np.nan) for k in zip(te.crop, te.region)])
    ok = ~np.isnan(b)

    meta = dict(
        source=f"ICRISAT district data {int(t.year.min())}-{int(t.year.max())}",
        rows=len(t),
        features=CAT + NUM,
        holdout=f"trained to {a.split}, tested {a.split + 1}-{int(t.year.max())}",
        r2=round(r2_score(te.yield_kg_ha, pred), 3),
        mae_kg_ha=round(mean_absolute_error(te.yield_kg_ha, pred)),
        baseline_r2=round(r2_score(te.yield_kg_ha[ok], b[ok]), 3),
        baseline_mae_kg_ha=round(mean_absolute_error(te.yield_kg_ha[ok], b[ok])),
        crops=sorted(t.crop.unique()),
        regions=sorted(t.region.unique()),
    )

    
    final = make().fit(t[CAT + NUM], t.yield_kg_ha)
    joblib.dump({"model": final, "meta": meta}, "model_district.joblib")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
