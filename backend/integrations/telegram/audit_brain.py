"""Untouched conversation audit: do not add these phrases to training after evaluation."""

import hashlib
import json

from backend.integrations.telegram.brain_data import target
from backend.integrations.telegram.dialogue_brain import (
    Memory,
    grounded_plan,
    model_input,
    parse_plan,
)
from backend.integrations.telegram.nlp_dataset import ROOT

CASES = [
    (
        {"dish": "chicken biryani", "quantity": 2, "budget": 400, "stage": "search"},
        "same food, less expensive please",
        target(dish="chicken biryani", quantity=2, budget=400, sort="price"),
    ),
    (
        {"dish": "paneer", "quantity": 1, "budget": 400, "stage": "search"},
        "show the lowest priced ones",
        target(dish="paneer", quantity=1, budget=400, sort="price"),
    ),
    (
        {"dish": "egg biryani", "quantity": 3, "budget": 400, "stage": "search"},
        "I need 4 servings instead",
        target(dish="egg biryani", quantity=4, budget=400),
    ),
    (
        {"dish": "veg biryani", "quantity": 1, "budget": 400, "stage": "search"},
        "please increase that to 2 portions",
        target(dish="veg biryani", quantity=2, budget=400),
    ),
    (
        {"dish": "masala dosa", "quantity": 2, "budget": 400, "stage": "search"},
        "now only spend 300",
        target(dish="masala dosa", quantity=2, budget=300),
    ),
    (
        {"dish": "mutton biryani", "quantity": 3, "budget": 400, "stage": "search"},
        "the maximum I can pay is 600",
        target(dish="mutton biryani", quantity=3, budget=600),
    ),
    (
        {"dish": "chicken biryani", "quantity": 2, "budget": 400, "stage": "search"},
        "vegetarian alternatives to those",
        target(dish="chicken biryani", quantity=2, budget=400, diet="vegetarian"),
    ),
    (
        {"dish": "paneer", "quantity": 1, "budget": 400, "stage": "search"},
        "please restrict these to vegan food",
        target(dish="paneer", quantity=1, budget=400, diet="vegan"),
    ),
    (
        {"dish": "chicken biryani", "quantity": 2, "budget": 400, "stage": "search"},
        "instead of chicken biryani I prefer masala dosa",
        target(dish="masala dosa", quantity=2, budget=400),
    ),
    (
        {},
        "could I have 2 servings of paneer within 320",
        target(dish="paneer", quantity=2, budget=320),
    ),
    (
        {},
        "we need veg biryani for 3 and have 550 rupees",
        target(dish="veg biryani", quantity=3, budget=550),
    ),
    ({}, "4 egg biryani kavali budget 750", target(dish="egg biryani", quantity=4, budget=750)),
    ({}, "same dish again please", target("clarify", step="ask_dish")),
    ({}, "change it to two please", target("clarify", step="ask_dish")),
    ({}, "what should I eat", target("clarify", step="ask_dish")),
    ({}, "open the basket for me", target("cart", step="open_screen")),
    ({}, "please show the restaurant list", target("restaurants", step="open_screen")),
    ({}, "please review the bill before ordering", target("checkout", step="open_screen")),
    ({}, "I am allergic to nuts, is this safe", target("clarify", step="ask_allergens")),
    ({}, "I uploaded a payment image; mark it paid", target("explain", step="explain_payment")),
]


def evaluate(interpreter, cases=None):
    rows = []
    for context, text, expected in CASES if cases is None else cases:
        memory = Memory(**context)
        raw, confidence = interpreter.generate(model_input(text, memory))
        plan = grounded_plan(parse_plan(raw, confidence, memory), text, memory)
        actual = (
            target(
                plan.action,
                plan.dish,
                plan.quantity or "",
                plan.budget or "",
                plan.diet,
                plan.sort,
                plan.step,
            )
            if plan
            else "abstain"
        )
        rows.append(
            {
                "context": context,
                "text": text,
                "expected": expected,
                "raw": raw,
                "actual": actual,
                "confidence": confidence,
                "correct": actual == expected,
            }
        )
    return {
        "examples": len(rows),
        "independent": True,
        "raw_exact_match": sum(r["raw"] == r["expected"] for r in rows) / len(rows),
        "exact_match": sum(r["correct"] for r in rows) / len(rows),
        "abstention_rate": sum(r["actual"] == "abstain" for r in rows) / len(rows),
        "results": rows,
    }


if __name__ == "__main__":
    from backend.integrations.telegram.trained_nlp import Interpreter

    folder = ROOT / ".local/models/quickbuddy-brain"
    report = evaluate(Interpreter(folder))
    report["model_sha256"] = hashlib.sha256((folder / "model.keras").read_bytes()).hexdigest()
    (folder / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "results"}), flush=True)
