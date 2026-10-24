"""Reference data. Crops and states are those present in the ICRISAT district dataset."""

# t/w: rough optimum temperature and water need (used only for tips and the radar chart),
# p: default price Rs/kg, c: rough cash cost Rs/ha, s: crop's usual season,
# mandi: commodity name in the Agmarknet dataset (verify against data.gov.in)
CROPS = {
    "Rice":         dict(t=27, tw=9,  w=1100, p=23, c=45000, s="Kharif", mandi="Paddy(Dhan)(Common)"),
    "Pearl millet": dict(t=29, tw=8,  w=450,  p=26, c=22000, s="Kharif", mandi="Bajra(Pearl Millet/Cumbu)"),
    "Groundnut":    dict(t=27, tw=8,  w=600,  p=65, c=40000, s="Kharif", mandi="Groundnut"),
    "Chickpea":     dict(t=21, tw=8,  w=250,  p=55, c=28000, s="Rabi",   mandi="Bengal Gram(Gram)(Whole)"),
}
REGIONS = {  # state: representative farming district (lat, lon) for the weather fill
    "Andhra Pradesh": (16.31, 80.44), "Assam": (26.14, 91.74), "Bihar": (25.59, 85.14),
    "Chhattisgarh": (21.25, 81.63), "Gujarat": (23.02, 72.57), "Haryana": (29.69, 76.99),
    "Himachal Pradesh": (31.10, 77.17), "Jharkhand": (23.34, 85.31), "Karnataka": (15.46, 75.01),
    "Kerala": (10.85, 76.27), "Madhya Pradesh": (23.26, 77.41), "Maharashtra": (18.52, 73.86),
    "Odisha": (20.30, 85.82), "Punjab": (30.90, 75.85), "Rajasthan": (26.91, 75.79),
    "Tamil Nadu": (11.02, 76.96), "Telangana": (17.39, 78.49), "Uttar Pradesh": (26.85, 80.95),
    "Uttarakhand": (30.32, 78.03), "West Bengal": (23.23, 87.86),
}
# Soil and humidity are NOT in the training data. These are rule-of-thumb multipliers (loam = 1).
SOILS = {"Loam": 1.0, "Black (regur)": .98, "Alluvial": 1.0, "Clay": .92, "Red": .88, "Sandy": .82}
SEASONS = ("Kharif", "Rabi")


def adjust(crop, season, hum, soil):
    """Rule-based multiplier for things the dataset cannot tell us."""
    h = max(.85, 1 - .004 * max(0, abs(hum - 60) - 15))
    se = 1 if CROPS[crop]["s"] == season else .6
    return h * SOILS[soil] * se


def profit(crop, year, yield_kg, price_per_kg=None):
    c = CROPS[crop]
    price = price_per_kg if price_per_kg else c["p"] * (1 + .04 * (year - 2025))
    return yield_kg * price - c["c"], price
