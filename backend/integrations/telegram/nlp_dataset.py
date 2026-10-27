"""Reproducible synthetic multilingual command/slot corpus with template-held-out split."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DISHES = {
    "chicken biryani": ("చికెన్ బిర్యానీ", "चिकन बिरयानी"),
    "veg biryani": ("వెజ్ బిర్యానీ", "वेज बिरयानी"),
    "mutton biryani": ("మటన్ బిర్యానీ", "मटन बिरयानी"),
    "paneer": ("పనీర్", "पनीर"),
    "masala dosa": ("మసాలా దోస", "मसाला डोसा"),
    "egg biryani": ("ఎగ్ బిర్యానీ", "अंडा बिरयानी"),
}
COMMANDS = {
    "restaurants": [
        "show restaurants",
        "list restaurants",
        "nearby restaurants",
        "restaurants chupinchu",
        "restaurants kavali",
        "హోటళ్లు చూపించు",
        "రెస్టారెంట్లు చూపించు",
        "रेस्टोरेंट दिखाओ",
        "रेस्टोरेंट की सूची",
        "restaurant dikhao",
    ],
    "cart": [
        "show my cart",
        "open basket",
        "review my cart",
        "cart chupinchu",
        "నా కార్ట్ చూపించు",
        "బుట్ట చూపించు",
        "कार्ट दिखाओ",
        "मेरा कार्ट",
        "mera cart dikhao",
    ],
    "checkout": [
        "checkout please",
        "review before placing order",
        "show final bill",
        "checkout cheyyi",
        "బిల్లు చూపించు",
        "చెకౌట్",
        "बिल दिखाओ",
        "चेकआउट करो",
        "bill dikhao",
    ],
    "confirm": [
        "confirm my order",
        "place this order",
        "submit my order",
        "order confirm cheyyi",
        "ఆర్డర్ నిర్ధారించు",
        "ఆర్డర్ పెట్టు",
        "ऑर्डर पक्का करो",
        "ऑर्डर करो",
        "order confirm karo",
    ],
    "cancel": [
        "cancel current selection",
        "clear this draft",
        "never mind",
        "cancel cheyyi",
        "రద్దు చేయి",
        "వద్దు",
        "रद्द करो",
        "नहीं चाहिए",
        "cancel karo",
    ],
    "cheaper": [
        "show cheaper options",
        "something less expensive",
        "lowest priced please",
        "takkuva dhara",
        "చౌకగా కావాలి",
        "తక్కువ ధర",
        "सस्ता दिखाओ",
        "कम दाम में",
        "sasta dikhao",
    ],
    "vegetarian": [
        "vegetarian only",
        "no meat please",
        "show veg dishes",
        "veg matrame",
        "శాకాహారం మాత్రమే",
        "వెజ్ మాత్రమే",
        "शाकाहारी खाना",
        "सिर्फ वेज",
        "sirf veg chahiye",
    ],
    "vegan": [
        "vegan dishes only",
        "show vegan food",
        "no animal products",
        "vegan kavali",
        "వీగన్ ఆహారం",
        "వీగన్ కావాలి",
        "वीगन खाना",
        "केवल वीगन",
        "vegan chahiye",
    ],
    "favorites": [
        "show favorites",
        "my saved dishes",
        "saved restaurants",
        "favorites chupinchu",
        "ఇష్టమైన వంటకాలు",
        "సేవ్ చేసినవి",
        "पसंदीदा खाना",
        "मेरे पसंदीदा",
        "favorites dikhao",
    ],
    "repeat": [
        "repeat my last order",
        "same as last time",
        "order again",
        "malli ade order",
        "మళ్ళీ అదే ఆర్డర్",
        "గత ఆర్డర్ మళ్ళీ",
        "पिछला ऑर्डर फिर से",
        "वही फिर से",
        "phir se wahi",
    ],
    "location": [
        "share my location",
        "use my gps",
        "change delivery location",
        "location pampali",
        "నా లొకేషన్",
        "చిరునామా మార్చు",
        "लोकेशन भेजो",
        "पता बदलो",
        "location bhejo",
    ],
    "pickup": [
        "I will pick up",
        "pickup please",
        "collect at restaurant",
        "pickup kavali",
        "నేనే తీసుకుంటాను",
        "పికప్ కావాలి",
        "खुद ले जाऊंगा",
        "पिकअप चाहिए",
        "pickup chahiye",
    ],
    "delivery": [
        "deliver to my home",
        "home delivery",
        "send it to my location",
        "intiki pampu",
        "ఇంటికి పంపు",
        "డెలివరీ కావాలి",
        "घर पर भेजो",
        "डिलीवरी चाहिए",
        "ghar bhejo",
    ],
    "orders": [
        "show my orders",
        "track my order",
        "was my order accepted",
        "order status enti",
        "ఆర్డర్ స్థితి",
        "నా ఆర్డర్లు",
        "ऑर्डर कहाँ है",
        "मेरे ऑर्डर",
        "order kahan hai",
    ],
    "allergens": [
        "what allergens are in this",
        "show ingredients",
        "does this contain nuts",
        "ingredients enti",
        "అలెర్జీ వివరాలు",
        "పదార్థాలు ఏమిటి",
        "एलर्जी की जानकारी",
        "सामग्री बताओ",
        "ingredients batao",
    ],
    "suggest": [
        "suggest a meal",
        "recommend a combination",
        "help plan lunch",
        "meal suggest cheyyi",
        "భోజనం సూచించు",
        "ఏం తినాలి",
        "खाना सुझाओ",
        "क्या खाऊँ",
        "khana suggest karo",
    ],
    "help": [
        "help me order",
        "how does this work",
        "what can you do",
        "help cheyyi",
        "సహాయం కావాలి",
        "ఎలా ఆర్డర్ చేయాలి",
        "मदद करो",
        "ऑर्डर कैसे करें",
        "madad karo",
    ],
}


def build():
    rows = []

    def add(text, intent, dish="", quantity="", budget="", diet="", family="", split="train"):
        rows.append(
            {
                "text": text,
                "target": "|".join([intent, dish, str(quantity), str(budget), diet]),
                "family": family,
                "split": split,
                "synthetic": True,
            }
        )

    for intent, phrases in COMMANDS.items():
        for index, text in enumerate(phrases):
            add(
                text,
                intent,
                family=f"{intent}:{index}",
                split="test" if index in (2, 8) else "train",
            )
    extra = {
        "restaurants": ["restaurants nearby please", "restaurant list dikhao", "रेस्टोरेंट सूची दिखाओ"],
        "cart": ["review cart", "mera cart please", "cart dikhao please", "review basket"],
        "checkout": [
            "final bill please",
            "mera bill dikhao",
            "checkout bill",
            "bill dikhao please",
        ],
        "confirm": ["submit order please", "confirm order karo", "please submit this order"],
        "cancel": ["I changed my mind", "never mind cancel", "please cancel karo"],
        "cheaper": ["lowest price please", "sasta khana dikhao", "low priced food"],
        "vegetarian": ["sirf vegetarian chahiye", "veg chahiye please", "शाकाहारी व्यंजन दिखाओ"],
        "vegan": ["vegan meal chahiye", "please vegan chahiye", "only vegan meals"],
        "favorites": ["my favorites dikhao", "favorites list dikhao", "show preferred dishes"],
        "repeat": ["phir se wahi order", "wahi khana phir se", "repeat same meal"],
        "location": ["location bhejo please", "my location please", "please change location"],
        "pickup": ["pickup chahiye please", "please collect at restaurant", "restaurant pickup"],
        "delivery": ["ghar bhejo please", "please send home", "deliver at home"],
        "orders": ["mera order kahan hai", "order location status", "track my current order"],
        "allergens": [
            "ingredients batao please",
            "allergen details please",
            "contains nuts question",
        ],
        "suggest": ["khana suggest karo please", "lunch suggestion please", "plan a meal"],
        "help": ["madad karo please", "please help with ordering", "show ordering help"],
    }
    for intent, phrases in extra.items():
        for phrase in phrases:
            add(phrase, intent, family="additional paraphrases")
    for dish, (te, hi) in DISHES.items():
        templates = [
            (f"I want {dish}", "", "", ""),
            (f"please find {dish}", "", "", ""),
            (f"show me {dish}", "", "", ""),
            (f"{dish} kavali", "", "", ""),
            (f"naaku {dish} ivvandi", "", "", ""),
            (f"{dish} chahiye", "", "", ""),
            (f"mujhe {dish} do", "", "", ""),
            (f"నాకు {te} కావాలి", "", "", ""),
            (f"{te} చూపించు", "", "", ""),
            (f"मुझे {hi} चाहिए", "", "", ""),
            (f"{hi} दिखाओ", "", "", ""),
        ]
        for index, (text, qty, budget, diet) in enumerate(templates):
            add(
                text,
                "search",
                dish,
                qty,
                budget,
                diet,
                family=f"search:{index}",
                split="test" if index in (2, 4) else "train",
            )
        for qty in (1, 2, 3, 4):
            for budget in (150, 250, 400):
                for index, text in enumerate(
                    [
                        f"{qty} {dish} under {budget}",
                        f"{dish} for {qty} people below {budget}",
                        f"{qty} {dish} kavali {budget} lopu",
                        f"{qty} {dish} chahiye {budget} ke andar",
                        f"please find {dish} under {budget} for {qty} people",
                        f"order {dish} for {qty} people under {budget}",
                        f"{qty} portions of {dish} below {budget}",
                    ]
                ):
                    add(
                        text,
                        "search",
                        dish,
                        qty,
                        budget,
                        family=f"slots:{index}",
                        split="test" if index == 1 else "train",
                    )
    for qty in (1, 2, 3, 4, 5, 6):
        for text in (f"for {qty} people", f"{qty} members ki", f"{qty} logon ke liye"):
            add(text, "quantity", quantity=qty, family="quantity")
    unique = {row["text"]: row for row in rows}
    path = Path(__file__).with_name("nlp-commands.jsonl")
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in unique.values()) + "\n",
        encoding="utf-8",
    )
    return list(unique.values())


if __name__ == "__main__":
    rows = build()
    print(
        {
            "unique_commands": len(rows),
            "train": sum(r["split"] == "train" for r in rows),
            "test": sum(r["split"] == "test" for r in rows),
        }
    )
