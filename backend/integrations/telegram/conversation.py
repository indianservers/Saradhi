"""Bounded multilingual normalization and entity extraction around neural suggestions."""

import difflib
import re

from backend.integrations.telegram.nlp_dataset import COMMANDS, DISHES

ALIASES = {phrase.lower(): intent for intent, phrases in COMMANDS.items() for phrase in phrases}
ACTIONS = {
    "restaurants": "Restaurants",
    "cart": "Cart",
    "checkout": "Checkout",
    "confirm": "Checkout",
    "cancel": "Cancel",
    "favorites": "Favorites",
    "repeat": "Order again",
    "location": "Share GPS location",
    "pickup": "Pickup",
    "delivery": "Delivery",
    "orders": "Order status",
    "help": "Help",
    "allergens": "Allergens",
    "suggest": "Meal suggestions",
}


def interpret(text, neural=None):
    raw = text.strip().lower()
    for word, number in (
        ("two", "2"),
        ("three", "3"),
        ("four", "4"),
        ("రెండు", "2"),
        ("మూడు", "3"),
        ("दो", "2"),
        ("तीन", "3"),
    ):
        raw = re.sub(r"(?<!\w)" + word + r"(?!\w)", number, raw)
    intent = ALIASES.get(raw)
    if intent:
        return {"action": ACTIONS.get(intent), "intent": intent, "query": raw}
    query = raw
    from backend.integrations.telegram.commerce_nlp_data import normalize_product_names

    query = normalize_product_names(query)
    for english, localized in DISHES.items():
        for term in localized:
            query = query.replace(term, english)
    for word in (
        "kavali",
        "chahiye",
        "ivvandi",
        "naaku",
        "mujhe",
        "చూపించు",
        "కావాలి",
        "నాకు",
        "मुझे",
        "चाहिए",
        "दिखाओ",
    ):
        query = query.replace(word, " ")
    query = re.sub(r"\b(\d+)\s*(lopu|ke andar)\b", r"under \1", query)
    quantity = re.search(r"(?:for |^)([1-9]\d?)\s*(?:people|persons|members|logon)?", raw)
    budget = re.search(
        r"(?:under|below|budget|within|at most|ceiling of|less than|లోపు|से कम)\s*(\d+)", query
    )
    if neural and neural.get("confidence", 0) >= 0.9:
        parts = neural.get("structured", "").split("|")
        if len(parts) == 5 and parts[0] in ACTIONS and not intent and neural.get("neural_promoted"):
            # A neural suggestion may open a screen, never submit or pay an order.
            intent = parts[0]
    return {
        "action": ACTIONS.get(intent),
        "intent": intent or "search",
        "query": query.strip(),
        "quantity": int(quantity[1]) if quantity else None,
        "budget": int(budget[1]) if budget else None,
    }


def fuzzy_query(query, catalog):
    words = sorted(
        {
            word
            for restaurant, dish in catalog.rows()
            for word in re.findall(r"[a-z]+", restaurant.name.lower() + " " + dish.name.lower())
        }
    )
    result = []
    protected = {
        "price",
        "prices",
        "quantity",
        "budget",
        "please",
        "same",
        "those",
        "these",
        "this",
        "that",
        "packs",
        "packets",
        "units",
        "bottles",
        "cheaper",
        "cheapest",
        "under",
        "below",
        "within",
        "keep",
        "change",
        "instead",
        "without",
        "store",
        "stores",
        "show",
        "find",
        "need",
        "want",
        "only",
        "from",
        "with",
    }
    for word in query.split():
        if word in protected:
            result.append(word)
            continue
        candidates = difflib.get_close_matches(word, words, n=1, cutoff=0.76)
        result.append(candidates[0] if candidates and word not in words else word)
    return " ".join(result)


TEXT = {
    "welcome": (
        "What would you like today? Browse food, groceries or household essentials.",
        "ఈరోజు ఏమి తినాలనుకుంటున్నారు? రెస్టారెంట్ లేదా వంటకం ఎంచుకోండి.",
        "आज क्या खाना चाहेंगे? रेस्टोरेंट या खाना चुनें।",
    ),
    "cart": ("Your cart", "మీ కార్ట్", "आपका कार्ट"),
    "empty": ("Your cart is empty.", "మీ కార్ట్ ఖాళీగా ఉంది.", "आपका कार्ट खाली है।"),
    "choose": ("Choose quantity", "పరిమాణం ఎంచుకోండి", "मात्रा चुनें"),
    "added": (
        "Added to cart. Keep shopping or review checkout.",
        "కార్ట్‌లో చేర్చబడింది. మరిన్ని ఎంచుకోండి లేదా బిల్లు చూడండి.",
        "कार्ट में जोड़ा गया। और चुनें या बिल देखें।",
    ),
    "missing": (
        "Ingredient/allergen information is missing. Ask the merchant before ordering.",
        "పదార్థాలు/అలెర్జీ సమాచారం లేదు. ముందుగా రెస్టారెంట్‌ను అడగండి.",
        "सामग्री/एलर्जी की जानकारी उपलब्ध नहीं है। पहले रेस्टोरेंट से पूछें।",
    ),
    "Restaurants": ("Restaurants", "రెస్టారెంట్లు", "रेस्टोरेंट"),
    "Cart": ("Cart", "కార్ట్", "कार्ट"),
    "Checkout": ("Checkout", "బిల్లు చూడండి", "बिल देखें"),
    "Favorites": ("Favorites", "ఇష్టమైనవి", "पसंदीदा"),
    "Languages": ("Languages", "భాషలు", "भाषाएँ"),
    "Order status": ("Order status", "ఆర్డర్ స్థితి", "ऑर्डर की स्थिति"),
    "Place order": ("Place order", "ఆర్డర్ పెట్టండి", "ऑर्डर करें"),
    "Share GPS location": ("Share GPS location", "లొకేషన్ పంపండి", "लोकेशन भेजें"),
}


def translate(key, language):
    extra = {
        "Customize": ("Customize", "మార్పులు", "अनुकूलित करें"),
        "Preparation notes": ("Preparation notes", "వంట సూచనలు", "तैयारी के निर्देश"),
        "Add to cart": ("Add to cart", "కార్ట్‌లో చేర్చు", "कार्ट में डालें"),
        "Cancel": ("Cancel", "రద్దు", "रद्द करें"),
        "Pickup": ("Pickup", "పికప్", "पिकअप"),
        "Delivery": ("Delivery", "డెలివరీ", "डिलीवरी"),
        "Save favorite": ("Save favorite", "ఇష్టమైనదిగా సేవ్", "पसंदीदा सहेजें"),
        "Save restaurant": ("Save restaurant", "రెస్టారెంట్ సేవ్", "रेस्टोरेंट सहेजें"),
        "Meal suggestions": ("Meal suggestions", "భోజన సూచనలు", "खाने के सुझाव"),
        "Allergens": ("Allergens", "అలెర్జీ వివరాలు", "एलर्जी की जानकारी"),
        "Choose item": ("Choose item", "వంటకం ఎంచుకోండి", "खाना चुनें"),
        "View full menu": ("View full menu", "పూర్తి మెనూ", "पूरा मेनू देखें"),
        "Full menu": ("Full menu", "పూర్తి మెనూ", "पूरा मेनू"),
        "Your cart is empty.": ("Your cart is empty.", "మీ కార్ట్ ఖాళీగా ఉంది.", "आपका कार्ट खाली है।"),
        "Selection cancelled. Your cart is retained.": (
            "Selection cancelled. Your cart is retained.",
            "ఎంపిక రద్దయింది. కార్ట్ అలాగే ఉంది.",
            "चयन रद्द किया गया। कार्ट सुरक्षित है।",
        ),
        "Choose 1–20 portions.": (
            "Choose 1–20 portions.",
            "1–20 పరిమాణాలు ఎంచుకోండి.",
            "1–20 मात्रा चुनें।",
        ),
        "No customization options supplied by this merchant.": (
            "No customization options supplied by this merchant.",
            "ఈ రెస్టారెంట్ మార్పుల ఎంపికలు ఇవ్వలేదు.",
            "रेस्टोरेंट ने अनुकूलन विकल्प नहीं दिए हैं।",
        ),
        "Notes saved.": ("Notes saved.", "సూచనలు సేవ్ అయ్యాయి.", "निर्देश सहेजे गए।"),
        "Quantity updated.": ("Quantity updated.", "పరిమాణం మార్చబడింది.", "मात्रा बदली गई।"),
        "Removed from cart.": ("Removed from cart.", "కార్ట్ నుండి తీసివేయబడింది.", "कार्ट से हटाया गया।"),
        "Cart dishes saved as favorites.": (
            "Cart dishes saved as favorites.",
            "వంటకాలు ఇష్టమైనవిగా సేవ్ అయ్యాయి.",
            "खाने पसंदीदा में सहेजे गए।",
        ),
        "Share GPS location before delivery checkout.": (
            "Share GPS location before delivery checkout.",
            "డెలివరీకి ముందు లొకేషన్ పంపండి.",
            "डिलीवरी के लिए पहले लोकेशन भेजें।",
        ),
    }
    index = {"en": 0, "te": 1, "hi": 2}.get(language, 0)
    values = {**TEXT, **extra}
    if key in values:
        return values[key][index]
    for prefix, translations in {
        "Qty ": ("Qty ", "పరిమాణం ", "मात्रा "),
        "Option ": ("Option ", "ఎంపిక ", "विकल्प "),
        "Slot ": ("Slot ", "సమయం ", "समय "),
        "Edit ": ("Edit ", "మార్చు ", "बदलें "),
        "Remove ": ("Remove ", "తొలగించు ", "हटाएँ "),
        "Set quantity ": ("Set quantity ", "పరిమాణం మార్చు ", "मात्रा बदलें "),
    }.items():
        if key.startswith(prefix):
            return translations[index] + key[len(prefix) :]
    return key
