"""
Illustrative impact-equivalence formulas used by the Impact Calculator page.
These are commonly cited, rounded rule-of-thumb conversion factors (not a
peer-reviewed LCA) -- good enough for a demo/report, and the page cites
each assumption next to its number so a reader can judge for themselves.

Sources for the ballpark magnitudes (orders of magnitude, not precise
figures): US EPA WARM model public summaries, and widely circulated
recycling-benefit factsheets (e.g. "1 ton of recycled paper saves ~17
trees").
"""

# kg CO2-equivalent avoided per kg of material recycled instead of
# landfilled/incinerated/newly produced.
CO2_PER_KG = {
    "plastic": 1.5,
    "paper": 0.9,
    "metal": 2.0,
    "glass": 0.3,
    "organic": 0.5,
    "e-waste": 3.0,
    "other": 0.2,
}

# Trees saved per kg of paper/cardboard recycled.
# Basis: ~17 trees saved per 1,000 kg (1 US ton) of recycled paper.
TREES_PER_KG_PAPER = 17 / 1000

# Litres of water saved per kg of material recycled (very approximate,
# varies hugely by material and process -- plastics and metals save the
# most via avoided virgin extraction/refining).
WATER_LITRES_PER_KG = {
    "plastic": 90,
    "paper": 60,
    "metal": 180,
    "glass": 20,
    "organic": 5,
    "e-waste": 200,
    "other": 10,
}

# kWh of energy saved per kg of material recycled vs. virgin production.
ENERGY_KWH_PER_KG = {
    "plastic": 2.0,
    "paper": 1.0,
    "metal": 4.5,
    "glass": 0.3,
    "organic": 0.2,
    "e-waste": 5.0,
    "other": 0.3,
}


def calculate_impact(amounts_kg: dict) -> dict:
    """amounts_kg: {category: kg}. Returns totals plus a per-category breakdown."""
    total_co2 = 0.0
    total_trees = 0.0
    total_water = 0.0
    total_energy = 0.0
    breakdown = {}

    for category, kg in amounts_kg.items():
        if kg <= 0:
            continue
        co2 = kg * CO2_PER_KG.get(category, CO2_PER_KG["other"])
        water = kg * WATER_LITRES_PER_KG.get(category, WATER_LITRES_PER_KG["other"])
        energy = kg * ENERGY_KWH_PER_KG.get(category, ENERGY_KWH_PER_KG["other"])
        trees = kg * TREES_PER_KG_PAPER if category == "paper" else 0.0

        total_co2 += co2
        total_water += water
        total_energy += energy
        total_trees += trees

        breakdown[category] = {
            "kg": kg, "co2_kg": co2, "water_litres": water,
            "energy_kwh": energy, "trees": trees,
        }

    return {
        "total_co2_kg": round(total_co2, 2),
        "total_water_litres": round(total_water, 1),
        "total_energy_kwh": round(total_energy, 2),
        "total_trees": round(total_trees, 3),
        "breakdown": breakdown,
    }
