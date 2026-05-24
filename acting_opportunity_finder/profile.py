PROFILE = {
    "name": "Roze Logtenberg",
    "email": "rozemarijn.logtenberg15@gmail.com",
    "playing_age_min": 27,
    "playing_age_max": 35,
    "search_age_min": 26,   # Cast wider net per brief
    "search_age_max": 37,
    "gender_terms": [
        "female", "woman", "women", "girl", "she/her",
        "non-binary", "non binary", "nonbinary", "nb",
        "female presenting", "female-presenting",
        "gender non-conforming", "gender nonconforming",
        "afab", "femme", "transgender woman", "trans woman",
    ],
    "location_terms": [
        "london", "greater london",
        # London areas that might appear without the word "London"
        "hackney", "shoreditch", "camden", "brixton", "islington",
        "peckham", "dalston", "bethnal green", "soho", "whitechapel",
        "clapham", "stratford", "greenwich", "southwark", "lambeth",
        "hoxton", "bermondsey", "elephant", "waterloo", "victoria",
        "shepherd's bush", "notting hill", "kentish town", "stoke newington",
        # UK-wide — included because she's open to UK shoots
        "uk", "united kingdom", "england", "british",
    ],
    # Cities to reject — if a post is explicitly set in one of these
    # and doesn't also mention London, it's not worth her travelling
    "excluded_locations": [
        "manchester", "birmingham", "leeds", "liverpool", "edinburgh",
        "glasgow", "bristol", "sheffield", "cardiff", "belfast",
        "newcastle", "nottingham", "brighton", "oxford", "cambridge",
        "coventry", "leicester", "reading", "southampton", "portsmouth",
    ],
    # Skills with bonus point values — higher = rarer / more distinctive
    "skills_bonus": {
        "dutch": 12,            # Native speaker — very rare
        "netherlands": 8,
        "bilingual": 8,
        "firearms": 10,         # Firearms trained for screen — rare
        "firearm": 10,
        "handgun": 8,
        "gun": 6,
        "meisner": 6,
        "comedy": 4,
        "improvisation": 4,
        "improv": 4,
        "physical theatre": 5,
        "laban": 5,
        "uta hagen": 5,
        "voice over": 4,
        "voiceover": 4,
        "voice acting": 4,
        "horse": 4,
        "horse riding": 4,
        "equestrian": 4,
        "swimming": 3,
        "water polo": 4,
        "scandinavian": 6,      # Appearance match
        "eastern european": 5,
        "european": 3,
        "blonde": 3,
        "dutch-english": 10,
        "central school": 4,
        "cssd": 4,
        "royal central": 4,
    },
}
