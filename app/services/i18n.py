"""
Lightweight i18n: English and Tamil translations for navigation, the home
page, and the UI chrome (headings, buttons, bin-type names) of the
"Where does it go?", Nearby Centres, and Sorting Guide pages. Detailed,
per-item descriptive content (the 124-item database, category bring/
don't-bring/tip paragraphs) stays in English only -- translating that
much domain-specific text reliably was out of scope for this pass; a
native speaker should review the Tamil strings below before relying on
them for anything beyond a demo.

The chosen language is remembered in both the session and a long-lived
cookie, so it survives login/logout and new visits.
"""
from fastapi import Request

SUPPORTED_LANGUAGES = ["en", "ta"]
LANGUAGE_LABELS = {"en": "English", "ta": "தமிழ்"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "nav.home": "Home",
        "nav.learn": "Learn",
        "nav.watch_learn": "Watch & learn",
        "nav.news": "News",
        "nav.dashboard": "Dashboard",
        "nav.waste_audit": "Waste audit",
        "nav.segregation_game": "Segregation game",
        "nav.reminders": "Reminders",
        "nav.impact": "Impact",
        "nav.scan": "Scan an item",
        "nav.my_scans": "My scans",
        "nav.where_does_it_go": "Where does it go?",
        "nav.sorting_guide": "Sorting guide",
        "nav.composting_guide": "Composting & DIY",
        "nav.nearby_centres": "Nearby centres",
        "nav.chat": "Ask Haraa",
        "nav.model_performance": "Model Performance",
        "nav.about": "About",
        "nav.logout": "Log out",
        "nav.poster": "Poster",
        "nav.weekly_report": "Weekly report",
        "nav.menu_learn": "Learn",
        "nav.menu_tools": "Tools",
        "nav.menu_activity": "My activity",
        "nav.menu_more": "More",

        "home.hero_title": "Know where it goes, before it goes in the bin.",
        "home.hero_subtitle": "Point your camera at anything from a milk packet to a dead battery, and get a straight answer: which bin it belongs in, and what to do with it next.",
        "home.hero_cta": "Scan an item",
        "home.how_it_works": "How it works",
        "home.step1_title": "Scan or describe it",
        "home.step1_desc": "Take a photo, or just search for the item by name.",
        "home.step2_title": "Get the right bin",
        "home.step2_desc": "Wet, dry, hazardous, e-waste or biomedical, with simple steps to prepare it.",
        "home.step3_title": "Log it and track your impact",
        "home.step3_desc": "One tap adds it to your dashboard, so your effort adds up over time.",
        "home.impact_so_far": "Your impact so far",
        "home.items_sorted": "Items sorted",
        "home.kept_out": "Kept out of landfill",
        "home.co2_avoided": "CO2 avoided",
        "home.common_mistakes": "A few things most households get wrong",
        "home.see_guide": "See the full sorting guide",

        "lookup.title": "Where does it go?",
        "lookup.subtitle": "Search over {count} household items to find the right bin.",
        "lookup.search_placeholder": "Try 'battery', 'milk packet', 'thermometer'...",
        "lookup.all_categories": "All categories",
        "lookup.no_results": "No items match your search.",
        "lookup.find_nearby": "Find a place near me",

        "nearby.title": "Find a place to take it",
        "nearby.subtitle": "Opens a Google Maps search in a new tab. No account or sign-in needed on their side.",
        "nearby.location_label": "Your city, area, or PIN code",
        "nearby.use_location": "Use my current location",
        "nearby.find_centres": "Find centres",
        "nearby.bring": "Bring",
        "nearby.dont_bring": "Don't bring",
        "nearby.hours_vary": "Opening hours and what's accepted vary by location. Check the listing or call ahead before you go.",

        "guide.title": "Sorting guide",
        "guide.subtitle": "What to do, what to avoid, and which bin each kind of waste belongs in.",
        "guide.do": "Do",
        "guide.dont": "Don't",
        "guide.bin_prefix": "Bin",

        "bin.wet": "Wet waste",
        "bin.dry": "Dry waste",
        "bin.hazardous": "Hazardous",
        "bin.e-waste": "E-waste",
        "bin.biomedical": "Biomedical",
        "bin.other": "Other",

        "category.plastic": "Plastic",
        "category.paper": "Paper",
        "category.metal": "Metal",
        "category.glass": "Glass",
        "category.organic": "Organic",
        "category.e-waste": "E-waste",
        "category.hazardous": "Hazardous",
        "category.other": "Other",
    },
    "ta": {
        "nav.home": "முகப்பு",
        "nav.learn": "கற்றுக்கொள்",
        "nav.watch_learn": "பார்த்து கற்க",
        "nav.news": "செய்திகள்",
        "nav.dashboard": "டாஷ்போர்டு",
        "nav.waste_audit": "கழிவு மதிப்பீடு",
        "nav.segregation_game": "பிரிப்பு விளையாட்டு",
        "nav.reminders": "நினைவூட்டல்கள்",
        "nav.impact": "தாக்கம்",
        "nav.scan": "ஒரு பொருளை ஸ்கேன் செய்",
        "nav.my_scans": "எனது ஸ்கேன்கள்",
        "nav.where_does_it_go": "இது எங்கே போகும்?",
        "nav.sorting_guide": "பிரிப்பு வழிகாட்டி",
        "nav.composting_guide": "உரமாக்கல் & DIY",
        "nav.nearby_centres": "அருகிலுள்ள மையங்கள்",
        "nav.chat": "ஹராவிடம் கேள்",
        "nav.model_performance": "மாடல் செயல்திறன்",
        "nav.about": "எங்களைப் பற்றி",
        "nav.logout": "வெளியேறு",
        "nav.poster": "சுவரொட்டி",
        "nav.weekly_report": "வாராந்திர அறிக்கை",
        "nav.menu_learn": "கற்றுக்கொள்",
        "nav.menu_tools": "கருவிகள்",
        "nav.menu_activity": "எனது செயல்பாடு",
        "nav.menu_more": "மேலும்",

        "home.hero_title": "குப்பைத் தொட்டியில் போடும் முன் அது எங்கே போகுமெனத் தெரிந்துகொள்ளுங்கள்.",
        "home.hero_subtitle": "பால் பாக்கெட் முதல் பழைய பேட்டரி வரை எதையும் உங்கள் கேமராவில் காட்டுங்கள், அது எந்தத் தொட்டியில் போக வேண்டும், அடுத்து என்ன செய்ய வேண்டும் என்பதை நேரடியாக அறியுங்கள்.",
        "home.hero_cta": "ஒரு பொருளை ஸ்கேன் செய்",
        "home.how_it_works": "இது எப்படி செயல்படுகிறது",
        "home.step1_title": "ஸ்கேன் செய் அல்லது விவரி",
        "home.step1_desc": "ஒரு புகைப்படம் எடுக்கவும், அல்லது பொருளின் பெயரைத் தேடவும்.",
        "home.step2_title": "சரியான தொட்டியைப் பெறுங்கள்",
        "home.step2_desc": "ஈரம், உலர், அபாயகரம், மின்-கழிவு அல்லது உயிரியல் மருத்துவக் கழிவு, தயார் செய்வதற்கான எளிய படிகளுடன்.",
        "home.step3_title": "பதிவு செய்து உங்கள் தாக்கத்தைக் கண்காணிக்கவும்",
        "home.step3_desc": "ஒரு தட்டலில் உங்கள் டாஷ்போர்டில் சேர்க்கப்படும், காலப்போக்கில் உங்கள் முயற்சி கூடிக்கொண்டே இருக்கும்.",
        "home.impact_so_far": "இதுவரை உங்கள் தாக்கம்",
        "home.items_sorted": "பிரிக்கப்பட்ட பொருட்கள்",
        "home.kept_out": "குப்பைத் தொட்டியிலிருந்து தவிர்க்கப்பட்டது",
        "home.co2_avoided": "தவிர்க்கப்பட்ட CO2",
        "home.common_mistakes": "பெரும்பாலான வீடுகள் தவறாகச் செய்யும் சில விஷயங்கள்",
        "home.see_guide": "முழு பிரிப்பு வழிகாட்டியைப் பார்க்கவும்",

        "lookup.title": "இது எங்கே போகும்?",
        "lookup.subtitle": "சரியான தொட்டியைக் கண்டறிய {count} வீட்டுப் பொருட்களில் தேடுங்கள்.",
        "lookup.search_placeholder": "'பேட்டரி', 'பால் பாக்கெட்', 'தெர்மாமீட்டர்' என முயற்சிக்கவும்...",
        "lookup.all_categories": "அனைத்து வகைகளும்",
        "lookup.no_results": "உங்கள் தேடலுக்குப் பொருந்தும் பொருட்கள் இல்லை.",
        "lookup.find_nearby": "அருகிலுள்ள இடத்தைக் கண்டறி",

        "nearby.title": "கொண்டு செல்ல ஒரு இடத்தைக் கண்டறியுங்கள்",
        "nearby.subtitle": "புதிய தாவலில் கூகிள் மேப்ஸ் தேடலைத் திறக்கிறது. அவர்கள் தரப்பில் கணக்கு தேவையில்லை.",
        "nearby.location_label": "உங்கள் நகரம், பகுதி, அல்லது அஞ்சல் குறியீடு",
        "nearby.use_location": "எனது தற்போதைய இருப்பிடத்தைப் பயன்படுத்து",
        "nearby.find_centres": "மையங்களைக் கண்டறி",
        "nearby.bring": "கொண்டு வாருங்கள்",
        "nearby.dont_bring": "கொண்டு வர வேண்டாம்",
        "nearby.hours_vary": "திறக்கும் நேரமும் ஏற்கப்படுவதும் இடத்திற்கு இடம் மாறுபடும். செல்வதற்கு முன் பட்டியலைச் சரிபார்க்கவும் அல்லது அழைக்கவும்.",

        "guide.title": "பிரிப்பு வழிகாட்டி",
        "guide.subtitle": "என்ன செய்ய வேண்டும், என்ன தவிர்க்க வேண்டும், ஒவ்வொரு கழிவும் எந்தத் தொட்டியில் போக வேண்டும்.",
        "guide.do": "செய்யுங்கள்",
        "guide.dont": "செய்ய வேண்டாம்",
        "guide.bin_prefix": "தொட்டி",

        "bin.wet": "ஈரக் கழிவு",
        "bin.dry": "உலர் கழிவு",
        "bin.hazardous": "அபாயகரமான கழிவு",
        "bin.e-waste": "மின் கழிவு",
        "bin.biomedical": "உயிரியல் மருத்துவக் கழிவு",
        "bin.other": "மற்றவை",

        "category.plastic": "பிளாஸ்டிக்",
        "category.paper": "காகிதம்",
        "category.metal": "உலோகம்",
        "category.glass": "கண்ணாடி",
        "category.organic": "இயற்கைக் கழிவு",
        "category.e-waste": "மின் கழிவு",
        "category.hazardous": "அபாயகரமானது",
        "category.other": "மற்றவை",
    },
}


def get_current_language(request: Request) -> str:
    lang = request.session.get("lang") or request.cookies.get("lang") or "en"
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def translate(lang: str, key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key) or TRANSLATIONS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text
