import json, os, secrets, sqlite3, time
import joblib, pandas as pd
from flask import Flask, g, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from common import CROPS, REGIONS, SOILS, SEASONS, adjust, profit
import services

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = pd.read_csv(os.path.join(BASE, "data", "training.csv"))

DISTRICTS = {
    region: sorted(group["district"].dropna().unique())
    for region, group in DATA.groupby("region")
}
DB = os.environ.get("DB_PATH", os.path.join(BASE, "agripredict.db"))
app = Flask(__name__, static_folder="static", static_url_path="/static")


def _secret():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    path = os.path.join(BASE, ".secret_key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    return open(path).read().strip()


app.config.update(SECRET_KEY=_secret(), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1", MAX_CONTENT_LENGTH=64 * 1024)

BUNDLE = joblib.load(os.path.join(BASE, "model_district.joblib"))     # run train.py first
FEATURES = ["crop", "region", "district", "year", "temp", "rain"]
YEARS = (1990, 2015)                                        # years the model was trained on


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, pw TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, ts REAL NOT NULL,
        crop TEXT, region TEXT, season TEXT, yield REAL, profit REAL, inputs TEXT);""")
    return g.db


@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d:
        d.close()


def err(msg, code=400):
    return jsonify(error=msg), code



def parse(j):
    try:
        s = dict(
            crop=j["crop"],
            region=j["region"],
            district=j["district"],
            season=j["season"],
            soil=j["soil"],
            year=int(j["year"]),
            temp=float(j["temp"]),
            rain=float(j["rain"]),
            hum=float(j["hum"])
        )
    except (KeyError, TypeError, ValueError):
        return None, "Missing or invalid field."

    if (s["crop"] not in CROPS or
        s["region"] not in REGIONS or
        s["soil"] not in SOILS or
        s["season"] not in SEASONS):
        return None, "Unknown crop, region, season or soil."

    if s["district"] not in DISTRICTS.get(s["region"], []):
        return None, "Please select a valid district for this region."

    if not (2015 <= s["year"] <= 2050 and
            5 <= s["temp"] <= 45 and
            0 <= s["rain"] <= 5000 and
            5 <= s["hum"] <= 100):
        return None, "A value is outside the allowed range."

    return s, None



def predict_yield(rows):
    df = pd.DataFrame(rows)
    df["year"] = df["year"].clip(*YEARS)       # the data ends in 2015; do not extrapolate the trend
    base = BUNDLE["model"].predict(df[FEATURES])
    return [float(b) * adjust(r["crop"], r["season"], r["hum"], r["soil"]) for b, r in zip(base, rows)]


@app.get("/")
def index():
    return send_from_directory("static", "index.html")



@app.get("/api/config")
def config():
    return jsonify(
        model=BUNDLE["meta"],
        live_prices=bool(os.environ.get("DATA_GOV_API_KEY")),
        districts=DISTRICTS
    )


# ---- auth ----
@app.post("/api/register")
def register():
    j = request.get_json(silent=True) or {}
    email, pw = str(j.get("email", "")).strip().lower(), str(j.get("password", ""))
    if "@" not in email or len(email) > 120 or len(pw) < 8:
        return err("Enter a valid email and a password of at least 8 characters.")
    try:
        cur = db().execute("INSERT INTO users(email,pw) VALUES(?,?)", (email, generate_password_hash(pw)))
        db().commit()
    except sqlite3.IntegrityError:
        return err("That email is already registered.", 409)
    session.clear(); session["uid"] = cur.lastrowid; session["email"] = email
    return jsonify(email=email)


@app.post("/api/login")
def login():
    j = request.get_json(silent=True) or {}
    email, pw = str(j.get("email", "")).strip().lower(), str(j.get("password", ""))
    u = db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not u or not check_password_hash(u["pw"], pw):
        time.sleep(.5)
        return err("Wrong email or password.", 401)
    session.clear(); session["uid"] = u["id"]; session["email"] = email
    return jsonify(email=email)


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/me")
def me():
    return jsonify(email=session.get("email"))


# ---- data ----
@app.get("/api/weather")
def weather():
    region, season = request.args.get("region", ""), request.args.get("season", "")
    year = request.args.get("year", type=int) or time.localtime().tm_year
    if region not in REGIONS or season not in SEASONS:
        return err("Unknown region or season.")
    try:
        return jsonify(services.season_weather(region, season, year))
    except Exception:
        return err("Weather service is unavailable right now. Enter values by hand.", 502)


@app.post("/api/predict")
def predict():
    s, e = parse(request.get_json(silent=True) or {})
    if e:
        return err(e)
    live = services.mandi_price(s["crop"], s["region"])
    price_kg = live["price"] if live else None
    district = s["district"]
    rows = [dict(s, crop=c, district=district) for c in CROPS]
    ys = predict_yield(rows)
    ys = [max(0.0, float(y)) for y in ys]
    allc = []
    for c, y in zip(CROPS, ys):
        lv = services.mandi_price(c, s["region"]) if live else None
        allc.append([c, round(y), round(profit(c, s["year"], y, lv["price"] if lv else None)[0])])
    y = ys[list(CROPS).index(s["crop"])]
    p, used = profit(s["crop"], s["year"], y, price_kg)
    out = dict(yield_kg_ha=round(y), profit=round(p), price_per_kg=round(used, 2),
               price_source=live["source"] if live else "default estimate", all=allc,
               model=BUNDLE["meta"]["source"])
    if "uid" in session:
        db().execute("INSERT INTO history(user_id,ts,crop,region,season,yield,profit,inputs) VALUES(?,?,?,?,?,?,?,?)",
                     (session["uid"], time.time(), s["crop"], s["region"], s["season"], y, p, json.dumps(s)))
        db().execute("DELETE FROM history WHERE user_id=? AND id NOT IN (SELECT id FROM history WHERE user_id=? ORDER BY id DESC LIMIT 100)",
                     (session["uid"], session["uid"]))
        db().commit()
    return jsonify(out)


@app.route("/api/history", methods=["GET", "DELETE"])
def history():
    if "uid" not in session:
        return err("Sign in to see saved history.", 401)
    if request.method == "DELETE":
        db().execute("DELETE FROM history WHERE user_id=?", (session["uid"],))
        db().commit()
        return jsonify(ok=True)
    rows = db().execute("SELECT ts,crop,region,season,yield,profit FROM history WHERE user_id=? ORDER BY id DESC LIMIT 50",
                        (session["uid"],)).fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", 5000)))
