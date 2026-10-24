# AgriPredict

Crop yield and profit web app: Flask backend, scikit-learn model trained on real ICRISAT district data, SQLite accounts, live weather and mandi prices.

## Run it
```
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000   (model.joblib is included)
```
Optional: set `DATA_GOV_API_KEY` (free, data.gov.in) for live mandi prices. For production use `gunicorn -w 2 app:app`, HTTPS, `COOKIE_SECURE=1` and `SECRET_KEY`.

## The data and model
- Source: ICRISAT district-level data, 560 districts, 1990-2015 (Mendeley, DOI 10.17632/ywp3y5j9vv.1).
- Crops available in that file: rice, pearl millet, groundnut, chickpea. It has no wheat, maize, soybean or cotton.
- `prepare_icrisat.py` builds `data/training.csv` (36.8k district-year-crop rows) with the weather of each crop's growing window: Kharif Jun-Sep, Rabi Oct-Feb. Rainfall is summed over months.
- `train.py` fits a gradient-boosting model on crop, state, year, rainfall and temperature.
- Held-out check (trained to 2009, tested on 2010-2015): R² 0.57, mean error 421 kg/ha. A plain crop+state average scores R² 0.45, error 486 kg/ha.

## Limits
- It predicts district-average yields from 1990-2015, so newer varieties and farm-level irrigation are not captured. The year is capped at 2015.
- Irrigation is not an input, so the rainfall response is not always smooth (dry irrigated districts and very wet districts both score high).
- Soil and humidity are not in the data; they are rule-of-thumb adjustments. The 40% off-season cut is also a rule.
- Prices and costs per hectare are rough defaults. Check the Agmarknet commodity names in `common.py` against data.gov.in.
- Live weather and mandi calls are untested (no internet where this was built).
