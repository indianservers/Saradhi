"""Grocery/essentials language and context examples; no medicine catalog or user data."""

PRODUCTS = {
    "rice": "groceries",
    "basmati rice": "groceries",
    "milk": "groceries",
    "eggs": "groceries",
    "tomatoes": "groceries",
    "onions": "groceries",
    "potatoes": "groceries",
    "atta": "groceries",
    "sugar": "groceries",
    "cooking oil": "groceries",
    "tea": "groceries",
    "coffee": "groceries",
    "dal": "groceries",
    "apples": "groceries",
    "bananas": "groceries",
    "oats": "groceries",
    "detergent": "essentials",
    "dishwashing liquid": "essentials",
    "floor cleaner": "essentials",
    "hand wash": "essentials",
    "toothpaste": "essentials",
    "shampoo": "essentials",
    "bath soap": "essentials",
    "toilet paper": "essentials",
    "tissues": "essentials",
    "garbage bags": "essentials",
    "batteries": "essentials",
    "notebooks": "essentials",
}
PRODUCT_ALIASES = {
    "rice": ("biyyam", "chawal"),
    "milk": ("palu", "doodh"),
    "sugar": ("panchadara", "cheeni"),
    "cooking oil": ("vanta noone", "cooking tel"),
    "atta": ("wheat flour",),
    "detergent": ("washing powder",),
    "bath soap": ("soap", "sabbu"),
    "dishwashing liquid": ("dish soap",),
    "garbage bags": ("trash bags",),
    "tomatoes": ("tomato",),
    "onions": ("onion",),
    "potatoes": ("potato",),
    "eggs": ("egg packs",),
}


def add_examples(add, target):
    direct = (
        "I need {q} packs of {item} within {b} rupees",
        "Could you find {item}? I need {q} packs and my budget is {b}",
        "Please show {item}, quantity {q}, under {b}",
        "We are running out of {item}; find {q} packs below {b}",
        "Can I get {q} packets of {item} for at most {b}",
        "For my shopping basket, find {item}: {q} packs, limit {b}",
        "Show store options for {q} packs of {item} within {b}",
        "Please compare {item} across stores for {q} packs under {b}",
        "{item} kavali {q} packets budget {b}",
        "{q} packets {item} chahiye budget {b}",
        "Restock {item} for me: {q} packs, spending cap {b}",
        "Looking for {item}; {q} packs and no more than {b} rupees",
        "Our shopping list needs {q} packs of {item}, with a limit of {b}",
        "Could you check shops for {item}, {q} packs below {b}",
    )
    items = list(PRODUCTS)
    for index, item in enumerate(items):
        for q, b in ((1, 180), (3, 650)):
            for n, phrase in enumerate(direct):
                add(
                    phrase.format(item=item, q=q, b=b),
                    {},
                    target(dish=item, quantity=q, budget=b),
                    "v6_product_search",
                    "dev" if n >= 12 else "train",
                )
        for alias in PRODUCT_ALIASES.get(item, ()):
            for phrase in (f"I need {alias} please", f"Show shops selling {alias}"):
                add(phrase, {}, target(dish=item), "v6_alias")
        for quantity, budget, sort in ((2, 500, ""), (4, 900, "price")):
            memory = {
                "dish": item,
                "quantity": quantity,
                "budget": budget,
                "sort": sort,
                "stage": "search",
            }
            for n, phrase in enumerate(
                (
                    "show cheaper choices for that item",
                    "sort the same product by price",
                    "find a less costly option for this product",
                )
            ):
                add(
                    phrase,
                    memory,
                    target(dish=item, quantity=quantity, budget=budget, sort="price"),
                    "v6_context_sort",
                    "dev" if n == 2 else "train",
                )
            for n, phrase in enumerate(
                (
                    "make that 5 packs",
                    "change it to 5 units please",
                    "we now need 5 packs of the same product",
                )
            ):
                add(
                    phrase,
                    memory,
                    target(dish=item, quantity=5, budget=budget, sort=sort),
                    "v6_context_quantity",
                    "dev" if n == 2 else "train",
                )
            for n, phrase in enumerate(
                (
                    "same item, my limit is now 350",
                    "keep the product but budget 350",
                    "leave the product alone and cap spending at 350",
                )
            ):
                add(
                    phrase,
                    memory,
                    target(dish=item, quantity=quantity, budget=350, sort=sort),
                    "v6_context_budget",
                    "dev" if n == 2 else "train",
                )
            for phrase, number in (
                ("double those packs", quantity * 2),
                ("make it half as many", quantity // 2),
            ):
                add(
                    phrase,
                    memory,
                    target(dish=item, quantity=number, budget=budget, sort=sort),
                    "v6_arithmetic",
                )
            replacement = items[(index + 1) % len(items)]
            for phrase in (
                f"Switch to {replacement} and keep the quantity and budget",
                f"I meant {replacement} instead of {item}",
            ):
                add(
                    phrase,
                    memory,
                    target(dish=replacement, quantity=quantity, budget=budget, sort=sort),
                    "v6_replace",
                )
            add(
                f"Replace {item} with {replacement}; leave the other settings alone",
                memory,
                target(dish=replacement, quantity=quantity, budget=budget, sort=sort),
                "v6_replace",
                "dev",
            )
        for phrase in (f"Is {item} in stock", f"Which store has {item}"):
            add(phrase, {}, target(dish=item), "v6_availability")
    for index, item in enumerate(items):
        replacement = items[(index + 1) % len(items)]
        for quantity, budget, sort in ((2, 500, ""), (4, 900, "price")):
            memory = {
                "dish": item,
                "quantity": quantity,
                "budget": budget,
                "sort": sort,
                "stage": "search",
            }
            for phrase in (
                f"Remove {item} from my request and search for {replacement}",
                f"Stop looking for {item}; find {replacement} instead",
            ):
                add(
                    phrase,
                    memory,
                    target(dish=replacement, quantity=quantity, budget=budget, sort=sort),
                    "v6_replace_training",
                )
            for phrase, number in (
                ("Double the pack quantity for me", quantity * 2),
                ("I would like twice as many of the same item", quantity * 2),
                ("Halve the quantity of that product", quantity // 2),
                ("Cut my current pack count in half", quantity // 2),
            ):
                add(
                    phrase,
                    memory,
                    target(dish=item, quantity=number, budget=budget, sort=sort),
                    "v6_arithmetic_training",
                )
    for action, phrases in {
        "groceries": (
            "Bring up grocery shopping",
            "Let us browse the grocery aisle",
            "I am looking for grocery supplies",
            "Take me to the grocery catalog",
            "Grocery shopping please",
            "I would like to browse groceries",
            "Open groceries for shopping",
            "Show the available grocery items",
            "Where is the grocery catalog",
            "Can we shop for groceries now",
            "Display grocery supplies",
            "Let me see grocery choices",
        ),
        "essentials": (
            "Bring up household supplies",
            "I want to browse essentials",
            "Can we shop for home essentials",
            "Take me to cleaning and personal care",
            "Let us browse household goods",
            "Household shopping please",
            "Open essentials for shopping",
            "Show the essentials catalog",
            "Display household products",
            "I am shopping for household needs",
            "Let me see essential supplies",
            "Take me to everyday essentials",
        ),
        "stores": (
            "Browse available shops",
            "I want to explore shops",
            "Let me see nearby shops",
            "Take me to store browsing",
            "List the stores I can shop from",
            "Open merchant stores",
            "Which stores are available",
            "Display the shop list",
            "Bring up local stores",
            "Show shops for ordering",
            "I want to look through stores",
            "Take me to available shops",
        ),
        "browse_all": (
            "Bring up the entire product catalog",
            "Show every available item",
            "Let me explore all categories",
            "Browse the whole catalog",
            "Open all shopping products",
            "Display all available products",
            "Show every product you have",
            "I want to browse everything available",
            "Take me to all items",
            "Show your full product range",
            "List products from every category",
            "Browse food and household products",
        ),
    }.items():
        for phrase in phrases:
            add(phrase, {}, target(action, step="open_screen"), "v6_navigation_training")
    for action, phrases in {
        "groceries": (
            "show grocery products",
            "I want to shop for groceries",
            "open the grocery section",
            "kirana saman chupinchu",
            "kirana samaan dikhao",
        ),
        "essentials": (
            "show household essentials",
            "I need cleaning supplies",
            "open household products",
            "show personal care products",
            "inti avasaralu chupinchu",
        ),
        "stores": (
            "show nearby stores",
            "which shops can I browse",
            "open the store list",
            "dukan dikhao",
            "shops chupinchu",
        ),
        "browse_all": (
            "show all available products",
            "browse every product category",
            "I want to see everything you sell",
            "show food groceries and essentials",
        ),
    }.items():
        for n, phrase in enumerate(phrases):
            add(
                phrase,
                {},
                target(action, step="open_screen"),
                "v6_navigation",
                "dev" if n == len(phrases) - 1 else "train",
            )
    for item, unit in (
        ("rice", "kg"),
        ("milk", "litres"),
        ("cooking oil", "litres"),
        ("detergent", "kg"),
    ):
        for q in (2, 3, 5):
            add(
                f"I need {q} {unit} of {item}",
                {},
                target("clarify", dish=item, step="ask_pack"),
                "v6_pack_clarification",
            )
    for phrase in (
        "I need rice and milk",
        "Get detergent and toothpaste",
        "I want sugar, tea and rice",
        "Show milk and floor cleaner together",
    ):
        add(phrase, {}, target("clarify", step="ask_item"), "v6_multi_item_clarification")


def normalize_product_names(text):
    import re

    mapping = {name: name for name in PRODUCTS}
    for name, aliases in PRODUCT_ALIASES.items():
        mapping.update({alias: name for alias in aliases})
    pattern = (
        r"(?<!\w)(?:"
        + "|".join(re.escape(x) for x in sorted(mapping, key=len, reverse=True))
        + r")(?!\w)"
    )
    return re.sub(pattern, lambda m: mapping[m.group()], text.lower())


def canonical_item_name(name):
    import re

    from backend.integrations.telegram.nlp_dataset import DISHES

    normalized = normalize_product_names(name.split(" · ")[0])
    for item in sorted([*PRODUCTS, *DISHES], key=len, reverse=True):
        if re.search(r"(?<!\w)" + re.escape(item) + r"(?!\w)", normalized):
            return item
    return normalized[:100]


def product_mentions(text):
    import re

    normalized = normalize_product_names(text)
    pattern = (
        r"(?<!\w)(?:"
        + "|".join(re.escape(x) for x in sorted(PRODUCTS, key=len, reverse=True))
        + r")(?!\w)"
    )
    return list(dict.fromkeys(re.findall(pattern, normalized)))


def quantity_adjustment(text, memory):
    """A bounded calculator tool; never changes a cart or selects a product."""
    import re

    raw = text.lower()
    if not memory.dish or not memory.quantity:
        return None
    if any(p != memory.dish for p in product_mentions(raw)):
        return None
    if not re.search(
        r"\b(packs?|packets?|units?|bottles?|quantity|count|number|those|these|them)\b|as many", raw
    ):
        return None
    if re.search(r"\b(double|doubling|twice)\b", raw):
        result = memory.quantity * 2
    elif re.search(r"\b(half|halve|halving)\b", raw) and memory.quantity % 2 == 0:
        result = memory.quantity // 2
    else:
        return None
    return result if 1 <= result <= 20 else None
