"""
Category data for the Nearby Centres page. No API key and no embedded
map: every "Find centres" link is a plain Google Maps search URL built as
https://www.google.com/maps/search/?api=1&query=<url-encoded query>,
which works without any Google API key or billing account.
"""

NEARBY_CATEGORIES = [
    {
        "id": "ewaste",
        "label": "E-waste recycling centres",
        "search_term": "e-waste recycling centre",
        "bring": "Phones, laptops, chargers, cables, old TVs, routers, remotes.",
        "dont_bring": "Batteries loose and unprotected. Tape the terminals first.",
        "tip": "Wipe personal data from any device before handing it over.",
    },
    {
        "id": "scrap_dealer",
        "label": "Scrap dealers (kabadiwala)",
        "search_term": "scrap dealer kabadiwala",
        "bring": "Newspaper, cardboard, metal scrap, old utensils, plastic in bulk.",
        "dont_bring": "Biomedical, hazardous, or e-waste items. Those need a specialised centre.",
        "tip": "Scrap dealers often pay by weight, so sorting by material first gets you a better rate.",
    },
    {
        "id": "hazardous",
        "label": "Battery and hazardous waste collection",
        "search_term": "hazardous waste collection centre",
        "bring": "Batteries, paint, pesticides, motor oil, broken thermometers, aerosol cans.",
        "dont_bring": "Anything leaking. Seal it in a container first.",
        "tip": "Many electronics stores also accept household batteries for recycling.",
    },
    {
        "id": "biomedical",
        "label": "Medicine take-back and biomedical waste",
        "search_term": "biomedical waste disposal medicine take back pharmacy",
        "bring": "Expired or unused medicines, syringes (in a sealed container), bandages.",
        "dont_bring": "Loose needles. Always seal sharps in a puncture-proof container first.",
        "tip": "Many pharmacies run their own medicine take-back program. Ask at the counter.",
    },
    {
        "id": "composting",
        "label": "Composting units",
        "search_term": "composting unit facility",
        "bring": "Vegetable peels, fruit waste, garden trimmings, coconut shells, eggshells.",
        "dont_bring": "Large amounts of meat, bones or dairy without a managed hot-compost setup.",
        "tip": "Many Resident Welfare Associations run a community composting pit. Ask your society office first.",
    },
    {
        "id": "transfer_station",
        "label": "Municipal waste transfer stations",
        "search_term": "municipal solid waste transfer station",
        "bring": "General household waste that doesn't fit another category here.",
        "dont_bring": "Hazardous, biomedical, or e-waste. Those need a specialised centre.",
        "tip": "Useful for bulky items like old furniture or construction debris.",
    },
    {
        "id": "plastic_recycling",
        "label": "Plastic recycling centres",
        "search_term": "plastic recycling centre",
        "bring": "Clean, dry plastic bottles, containers, and packaging.",
        "dont_bring": "Multilayer plastic (chip packets) unless the centre specifically accepts it.",
        "tip": "Rinse containers first. Food residue is the most common reason a load gets rejected.",
    },
    {
        "id": "textile",
        "label": "Textile donation or recycling",
        "search_term": "textile recycling donation centre",
        "bring": "Clothes, shoes, bedsheets, and towels, wearable or not.",
        "dont_bring": "Wet or mouldy textiles. Dry them out first.",
        "tip": "Still-wearable clothing is usually better donated directly than recycled.",
    },
    {
        "id": "glass_recycling",
        "label": "Glass recycling",
        "search_term": "glass recycling centre",
        "bring": "Bottles and jars, rinsed, with lids removed.",
        "dont_bring": "Ceramics, mirrors, or window glass. These need a different process and contaminate the batch.",
        "tip": "Wrap any broken glass separately and label it before transport.",
    },
]

CATEGORY_BY_ID = {c["id"]: c for c in NEARBY_CATEGORIES}

# Maps this app's waste-dashboard categories onto a nearby-centres category,
# used by the "Find a place near me" shortcut on the Disposal Guide and
# Photo Upload result pages.
DASHBOARD_CATEGORY_TO_NEARBY_ID = {
    "plastic": "plastic_recycling",
    "paper": "scrap_dealer",
    "metal": "scrap_dealer",
    "glass": "glass_recycling",
    "organic": "composting",
    "e-waste": "ewaste",
    "hazardous": "hazardous",
    "other": "transfer_station",
}
