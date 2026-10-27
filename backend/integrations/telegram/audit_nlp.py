"""Independent post-training audit. Do not add these commands to the training corpus."""

import json
from pathlib import Path

from backend.integrations.telegram.trained_nlp import Interpreter

CASES = [
    ("could I get chicken biryani please", "search|chicken biryani|||"),
    ("today I want veg biryani", "search|veg biryani|||"),
    ("please serve mutton biryani", "search|mutton biryani|||"),
    ("I feel like having paneer", "search|paneer|||"),
    ("masala dosa for breakfast", "search|masala dosa|||"),
    ("egg biryani for dinner", "search|egg biryani|||"),
    ("naaku chicken biryani kavali please", "search|chicken biryani|||"),
    ("mujhe veg biryani chahiye please", "search|veg biryani|||"),
    ("నాకు పనీర్ కావాలి దయచేసి", "search|paneer|||"),
    ("कृपया मुझे चिकन बिरयानी चाहिए", "search|chicken biryani|||"),
    ("please show 2 chicken biryani under 250", "search|chicken biryani|2|250|"),
    ("veg biryani for 3 people below 400 please", "search|veg biryani|3|400|"),
    ("can you open my cart", "cart||||"),
    ("please show the final checkout bill", "checkout||||"),
    ("I would prefer something cheaper", "cheaper||||"),
    ("please show restaurants nearby", "restaurants||||"),
    ("I need help with my order", "help||||"),
    ("please repeat the previous meal", "repeat||||"),
    ("I want only vegetarian dishes", "vegetarian||||"),
    ("please deliver this to my house", "delivery||||"),
]


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[3] / ".local/models/quickbuddy-nlp"
    model = Interpreter(folder)
    results = [
        {"text": text, "expected": expected, "actual": model.generate(text)[0]}
        for text, expected in CASES
    ]
    report = {
        "examples": len(results),
        "independent": True,
        "used_for_training": False,
        "exact_match": sum(r["expected"] == r["actual"] for r in results) / len(results),
        "intent_accuracy": sum(
            r["expected"].split("|")[0] == r["actual"].split("|")[0] for r in results
        )
        / len(results),
        "results": results,
    }
    (folder / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "results"}), flush=True)
