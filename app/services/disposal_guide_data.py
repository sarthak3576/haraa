"""
Do's/don'ts and bin guidance per waste category, including the bin-colour
convention commonly used in India (green = wet/organic, blue = dry/
recyclable, red = biomedical/hazardous, in line with Solid Waste Management
Rules, 2016 and the Bio-Medical Waste Management Rules, 2016).
"""

DISPOSAL_GUIDE = [
    {
        "category": "plastic",
        "bin": "Blue (dry waste)",
        "dos": [
            "Rinse containers before putting them in the dry waste bin.",
            "Flatten bottles to save space.",
            "Check the resin code (the number inside the recycling triangle) -- 1 (PET) and 2 (HDPE) are the most widely accepted.",
        ],
        "donts": [
            "Don't mix plastic with wet/food waste.",
            "Don't put thin plastic bags/wrappers loose -- bundle them.",
            "Don't burn plastic waste -- it releases toxic fumes.",
        ],
    },
    {
        "category": "paper",
        "bin": "Blue (dry waste)",
        "dos": [
            "Flatten cardboard boxes.",
            "Keep paper dry and free of food residue.",
        ],
        "donts": [
            "Don't recycle greasy/food-stained paper (e.g. pizza boxes) -- it contaminates the batch.",
            "Don't include laminated or wax-coated paper.",
        ],
    },
    {
        "category": "metal",
        "bin": "Blue (dry waste)",
        "dos": [
            "Rinse cans before disposal.",
            "Separate lids if they're a different metal.",
        ],
        "donts": [
            "Don't dispose of metal with sharp edges loosely -- wrap them.",
            "Don't mix with hazardous/paint containers (see Hazardous below).",
        ],
    },
    {
        "category": "glass",
        "bin": "Blue (dry waste)",
        "dos": [
            "Rinse jars and bottles.",
            "Remove non-glass lids before recycling.",
        ],
        "donts": [
            "Don't recycle broken glass loosely -- wrap it and label it to protect handlers.",
            "Don't include ceramics, mirrors, or window glass with container glass.",
        ],
    },
    {
        "category": "organic",
        "bin": "Green (wet waste)",
        "dos": [
            "Compost at home where possible (kitchen scraps, yard waste).",
            "Drain excess liquid before disposal.",
        ],
        "donts": [
            "Don't mix wet waste with recyclables -- it contaminates the whole batch.",
            "Don't dispose of large quantities of meat/dairy in home compost without a proper setup (odour/pests).",
        ],
    },
    {
        "category": "e-waste",
        "bin": "Not a household bin -- take to an authorised e-waste collection point",
        "dos": [
            "Take electronics and batteries to a certified e-waste collector or manufacturer take-back program.",
            "Wipe personal data from devices before handing them over.",
        ],
        "donts": [
            "Never put batteries or electronics in household dry/wet waste -- fire and heavy-metal contamination risk.",
            "Don't dismantle devices with lithium batteries yourself.",
        ],
    },
    {
        "category": "hazardous",
        "bin": "Red/black (as per local municipal guidance) -- never with regular waste",
        "dos": [
            "Take paints, solvents, pesticides, and medical/biomedical waste to a designated hazardous-waste facility.",
            "Keep hazardous waste in original, labelled containers until drop-off.",
        ],
        "donts": [
            "Never pour chemicals down a drain.",
            "Never mix hazardous or biomedical waste with household dry/wet waste.",
        ],
    },
    {
        "category": "other",
        "bin": "Check local municipal guidance",
        "dos": [
            "When in doubt, check with your local municipal body's segregation guidelines.",
        ],
        "donts": [
            "Don't assume unlabelled or mixed waste is safe for standard recycling streams.",
        ],
    },
]
