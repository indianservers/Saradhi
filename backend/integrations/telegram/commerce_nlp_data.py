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
