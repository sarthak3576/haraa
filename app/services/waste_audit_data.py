"""
A short (2-minute), 8-question household waste audit. Each question maps
to a category; the three lowest-scoring categories become the "top 3
improvements" shown in the results. Scoring and recommendations stay
entirely client-side (no backend state needed for a one-off self-check).
"""

AUDIT_QUESTIONS = [
    {
        "id": "segregation",
        "question": "Do you separate wet (food) waste from dry (recyclable) waste?",
        "options": [("Always", 2), ("Sometimes", 1), ("Never", 0)],
        "tip": "Keep two bins at home: green for wet waste, blue for dry waste. It's the single biggest improvement most households can make.",
    },
    {
        "id": "rinsing",
        "question": "Do you rinse recyclables (bottles, cans, containers) before putting them out?",
        "options": [("Always", 2), ("Sometimes", 1), ("Never", 0)],
        "tip": "A quick rinse keeps your whole batch of dry waste from being rejected at the sorting stage.",
    },
    {
        "id": "composting",
        "question": "Do you compost kitchen scraps at home or through a local service?",
        "options": [("Yes", 2), ("Sometimes", 1), ("No", 0)],
        "tip": "Even a small balcony compost bin for vegetable peels and coconut shells keeps a lot of weight out of landfill.",
    },
    {
        "id": "ewaste",
        "question": "Do you know where your nearest e-waste collection point is?",
        "options": [("Yes", 2), ("Not sure", 1), ("No", 0)],
        "tip": "Check the Nearby Centres page once, bookmark it, and you'll always know where old electronics should go.",
    },
    {
        "id": "hazardous",
        "question": "Do you know which bin hazardous items (batteries, thermometers, bulbs) go in?",
        "options": [("Yes", 2), ("Not sure", 1), ("No", 0)],
        "tip": "Batteries and mercury items should never go in a regular bin. Visit the Sorting Guide for the full hazardous-item list.",
    },
    {
        "id": "medicine",
        "question": "Do you take expired or unused medicines to a pharmacy instead of binning them?",
        "options": [("Always", 2), ("Sometimes", 1), ("Never", 0)],
        "tip": "Most pharmacies will take expired medicines back. Flushing or binning them risks contaminating water.",
    },
    {
        "id": "plastic",
        "question": "Do you avoid single-use plastic (bags, straws, cutlery) when you can?",
        "options": [("Always", 2), ("Sometimes", 1), ("Never", 0)],
        "tip": "Carrying a reusable bag and bottle cuts out a surprising amount of plastic waste over a year.",
    },
    {
        "id": "reuse",
        "question": "Do you donate or sell usable items instead of throwing them away?",
        "options": [("Always", 2), ("Sometimes", 1), ("Never", 0)],
        "tip": "Clothes, furniture and electronics in working condition are almost always worth donating or selling to a kabadiwala first.",
    },
]

MAX_SCORE = sum(max(pts for _, pts in q["options"]) for q in AUDIT_QUESTIONS)
