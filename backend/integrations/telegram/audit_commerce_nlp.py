"""Frozen new-domain audit. Do not add these phrases to training after evaluation."""

from backend.integrations.telegram.brain_data import target

CASES = [
    ({}, "Please find two packets of rice under 420", target(dish="rice", quantity=2, budget=420)),
    (
        {},
        "Can I buy 3 bottles of dishwashing liquid below 500",
        target(dish="dishwashing liquid", quantity=3, budget=500),
    ),
    (
        {},
        "Need toothpaste quantity 2 ceiling 250",
        target(dish="toothpaste", quantity=2, budget=250),
    ),
    (
        {},
        "Floor cleaner for 2 packs budget 300",
        target(dish="floor cleaner", quantity=2, budget=300),
    ),
    ({}, "Show stores that stock garbage bags", target(dish="garbage bags")),
    ({}, "chawal kavali 2 packets budget 200", target(dish="rice", quantity=2, budget=200)),
    ({}, "washing powder 3 packs within 450", target(dish="detergent", quantity=3, budget=450)),
    ({}, "palu kavali please", target(dish="milk")),
    ({}, "Could you locate detergnt", target(dish="detergent")),
    ({}, "I need 2 packs of bananas below 150", target(dish="bananas", quantity=2, budget=150)),
    (
        {"dish": "rice", "quantity": 2, "budget": 500, "stage": "search"},
        "increase that to 4 packs",
        target(dish="rice", quantity=4, budget=500),
    ),
    (
        {"dish": "milk", "quantity": 3, "budget": 500, "stage": "search"},
        "only one bottle now",
        target(dish="milk", quantity=1, budget=500),
    ),
    (
        {"dish": "detergent", "quantity": 4, "budget": 900, "sort": "price", "stage": "search"},
        "same product below 600",
        target(dish="detergent", quantity=4, budget=600, sort="price"),
    ),
    (
        {"dish": "bath soap", "quantity": 2, "budget": 500, "stage": "search"},
        "show the cheapest ones",
        target(dish="bath soap", quantity=2, budget=500, sort="price"),
    ),
    (
        {"dish": "atta", "quantity": 2, "budget": 500, "sort": "price", "stage": "search"},
        "double my pack count",
        target(dish="atta", quantity=4, budget=500, sort="price"),
    ),
    (
        {"dish": "notebooks", "quantity": 4, "budget": 500, "sort": "price", "stage": "search"},
        "half the number of packs",
        target(dish="notebooks", quantity=2, budget=500, sort="price"),
    ),
    (
        {"dish": "onions", "quantity": 2, "budget": 200, "stage": "search"},
        "get potatoes instead",
        target(dish="potatoes", quantity=2, budget=200),
    ),
    (
        {"dish": "tissues", "quantity": 4, "budget": 300, "stage": "search"},
        "switch to hand wash with the same budget and count",
        target(dish="hand wash", quantity=4, budget=300),
    ),
    ({}, "I'd like household essentials", target("essentials", step="open_screen")),
    ({}, "Where can I shop for groceries", target("groceries", step="open_screen")),
    ({}, "Let me browse all stores", target("stores", step="open_screen")),
    ({}, "Bring milk, 2 litres in total", target("clarify", dish="milk", step="ask_pack")),
    ({}, "I need rice, milk and detergent", target("clarify", step="ask_item")),
    ({}, "same product but cheaper please", target("clarify", step="ask_dish")),
]

if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    from backend.integrations.telegram.audit_brain import evaluate
    from backend.integrations.telegram.transformer_brain import TransformerBrain

    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = evaluate(TransformerBrain(Path(args.folder)), CASES)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}), flush=True)
