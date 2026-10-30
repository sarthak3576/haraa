"""
Curated, hand-picked links for the News & Videos page. These are stable
homepages/section pages of well-known organizations rather than individual
articles or specific video IDs, which keeps the list accurate without
needing a live news/YouTube API (and keeps AWS costs at zero for this page).

Feel free to edit this list to point at your own preferred sources.
"""

NEWS_LINKS = [
    {
        "title": "UNEP -- Waste Management",
        "source": "UN Environment Programme",
        "url": "https://www.unep.org/topics/chemicals-and-pollution-action/pollution-and-health/waste-management",
    },
    {
        "title": "EPA -- Recycling & Sustainable Materials Management",
        "source": "U.S. Environmental Protection Agency",
        "url": "https://www.epa.gov/recycle",
    },
    {
        "title": "Ellen MacArthur Foundation -- Circular Economy",
        "source": "Ellen MacArthur Foundation",
        "url": "https://www.ellenmacarthurfoundation.org/topics/circular-economy-introduction/overview",
    },
    {
        "title": "Down To Earth -- Waste",
        "source": "Centre for Science and Environment (India)",
        "url": "https://www.downtoearth.org.in/waste",
    },
    {
        "title": "Swachh Bharat Mission",
        "source": "Government of India",
        "url": "https://swachhbharatmission.ddws.gov.in/",
    },
    {
        "title": "World Economic Forum -- Circular Economy",
        "source": "World Economic Forum",
        "url": "https://www.weforum.org/stories/circular-economy/",
    },
]

# YouTube search links (rather than guessed individual video IDs) so every
# link reliably resolves to real, current content on the topic.
YOUTUBE_TOPICS = [
    {"label": "How recycling actually works",
     "query": "how recycling actually works"},
    {"label": "Plastic waste and the circular economy",
     "query": "plastic waste circular economy explained"},
    {"label": "Composting at home",
     "query": "how to compost at home"},
    {"label": "E-waste recycling explained",
     "query": "e-waste recycling explained"},
    {"label": "Zero waste lifestyle tips",
     "query": "zero waste lifestyle tips"},
]

YOUTUBE_SEARCH_BASE = "https://www.youtube.com/results?search_query="
