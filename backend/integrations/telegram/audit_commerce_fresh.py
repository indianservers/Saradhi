"""Additional frozen novel-phrasing audit, created after refinement data was frozen."""

from backend.integrations.telegram.brain_data import target

CASES = [
    ({}, "rice please, two packs, max 250", target(dish="rice", quantity=2, budget=250)),
    ({}, "I have 400 for 2 packets of detergent", target(dish="detergent", quantity=2, budget=400)),
    ({}, "Please locate 4 packets of tea below 600", target(dish="tea", quantity=4, budget=600)),
    ({}, "One pack of garbage bags please", target(dish="garbage bags", quantity=1)),
    ({}, "naaku panchadara kavali", target(dish="sugar")),
    ({}, "Open grocery shopping for me", target("groceries", step="open_screen")),
    ({}, "Let's look at home essentials", target("essentials", step="open_screen")),
    (
        {"dish": "rice", "quantity": 3, "budget": 600, "sort": "price", "stage": "search"},
        "Actually only one packet",
        target(dish="rice", quantity=1, budget=600, sort="price"),
    ),
    (
        {"dish": "detergent", "quantity": 3, "budget": 700, "stage": "search"},
        "Can you double the number I asked for",
        target(dish="detergent", quantity=6, budget=700),
    ),
    (
        {"dish": "shampoo", "quantity": 4, "budget": 800, "sort": "price", "stage": "search"},
        "Please halve my order quantity",
        target(dish="shampoo", quantity=2, budget=800, sort="price"),
    ),
    (
        {"dish": "sugar", "quantity": 2, "budget": 300, "stage": "search"},
        "Make the budget 240 without changing the product",
        target(dish="sugar", quantity=2, budget=240),
    ),
    (
        {"dish": "milk", "quantity": 4, "budget": 450, "stage": "search"},
        "I can spend only 360 on that now",
        target(dish="milk", quantity=4, budget=360),
    ),
    (
        {"dish": "hand wash", "quantity": 2, "budget": 300, "stage": "search"},
        "Show me lower priced options for this",
        target(dish="hand wash", quantity=2, budget=300, sort="price"),
    ),
    (
        {"dish": "onions", "quantity": 3, "budget": 300, "stage": "search"},
        "Instead of onions, look for potatoes",
        target(dish="potatoes", quantity=3, budget=300),
    ),
    ({}, "I want milk totalling 3 litres", target("clarify", dish="milk", step="ask_pack")),
    ({}, "Please get rice and toothpaste together", target("clarify", step="ask_item")),
]
