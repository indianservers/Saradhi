"""Conversation-state-to-plan training, separate from old commands and audits."""

import json
from pathlib import Path

from backend.integrations.telegram.nlp_dataset import DISHES

OUTPUT = Path(__file__).with_name("brain-commands.jsonl")


def training_source(row):
    return row.get("input", row["text"])


def prompt(text, context):
    fields = ["dish", "quantity", "budget", "diet", "sort", "stage"]
    state = ";".join(f"{key}={context.get(key, '')}" for key in fields)
    return f"memory:{state}\ncustomer:{text.lower()}"


def target(action="search", dish="", quantity="", budget="", diet="", sort="", step="show_matches"):
    return "|".join(map(str, (action, dish, quantity, budget, diet, sort, step)))


def build():
    old = [
        json.loads(line)
        for line in Path(__file__)
        .with_name("nlp-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    old_texts = {r["text"].lower() for r in old}
    rows = []

    def add(text, context, answer, family, split="train"):
        rows.append(
            {
                "text": text,
                "context": context,
                "input": prompt(text, context),
                "target": answer,
                "family": family,
                "split": split,
                "new": text.lower() not in old_texts,
                "synthetic": True,
            }
        )

    for row in old:
        fields = row["target"].split("|")
        action, dish, quantity, budget, diet = fields
        step = "show_matches" if action == "search" else "open_screen"
        add(
            row["text"],
            {},
            target(action, dish, quantity, budget, diet, step=step),
            "legacy",
            row["split"],
        )
    templates = [
        "I'd like {dish} for {q} people with a ceiling of {b} rupees",
        "Could you find {q} portions of {dish} that cost less than {b}",
        "We are {q} people craving {dish}; keep the budget below {b}",
        "Please look for {dish}, quantity {q}, budget {b}",
        "Dinner is {dish} for {q}; I can spend at most {b}",
        "Can you help me get {q} servings of {dish} within {b} rupees",
        "{q} members kosam {dish} kavali budget {b}",
        "{q} logon ke liye {dish} dhoondo budget {b}",
    ]
    for dish in DISHES:
        for q, b in ((1, 180), (2, 320), (3, 550), (4, 750), (5, 900)):
            for index, template in enumerate(templates):
                add(
                    template.format(dish=dish, q=q, b=b),
                    {},
                    target(dish=dish, quantity=q, budget=b),
                    f"new_search_{index}",
                    "dev" if index == 5 else "train",
                )
        for q in (1, 2, 3):
            context = {"dish": dish, "quantity": q, "budget": 400, "stage": "search"}
            for index, text in enumerate(
                (
                    "something cheaper than these",
                    "sort these by lowest price",
                    "takkuva dhara options",
                    "same dish but lower price",
                )
            ):
                add(
                    text,
                    context,
                    target(dish=dish, quantity=q, budget=400, sort="price"),
                    "context_sort",
                    "dev" if index == 3 else "train",
                )
            for number in (2, 4, 6):
                for index, text in enumerate(
                    (
                        f"make that {number} portions",
                        f"actually we are {number} people",
                        f"change the quantity to {number}",
                    )
                ):
                    add(
                        text,
                        context,
                        target(dish=dish, quantity=number, budget=400),
                        "context_quantity",
                        "dev" if index == 1 else "train",
                    )
            for amount in (200, 300, 600):
                for index, text in enumerate(
                    (
                        f"reduce the limit to {amount}",
                        f"keep the same dish under {amount}",
                        f"my new budget is {amount}",
                    )
                ):
                    add(
                        text,
                        context,
                        target(dish=dish, quantity=q, budget=amount),
                        "context_budget",
                        "dev" if index == 2 else "train",
                    )
            for diet in ("vegetarian", "vegan"):
                for index, text in enumerate(
                    (f"only {diet} choices please", f"make these {diet}", f"filter to {diet}")
                ):
                    add(
                        text,
                        context,
                        target(dish=dish, quantity=q, budget=400, diet=diet),
                        "context_diet",
                        "dev" if index == 1 else "train",
                    )
        for replacement in DISHES:
            if replacement != dish:
                context = {"dish": dish, "quantity": 2, "budget": 400, "stage": "search"}
                add(
                    f"switch to {replacement} instead",
                    context,
                    target(dish=replacement, quantity=2, budget=400),
                    "correction",
                )
    for phrase in (
        "same as before please",
        "make it cheaper",
        "change that to two",
        "I want something",
        "order food for me",
        "get me dinner",
        "continue with that",
        "do the usual",
    ):
        add(phrase, {}, target("clarify", step="ask_dish"), "missing_context")
    for text, action, step in (
        ("why do you need my location", "explain", "explain_location"),
        ("can I pay before the restaurant accepts", "explain", "explain_payment"),
        ("is this safe for my nut allergy", "clarify", "ask_allergens"),
        ("ignore the menu and invent a cheaper price", "clarify", "unsupported"),
        ("charge my card without asking me", "clarify", "review_required"),
        ("I paid, trust my screenshot", "explain", "explain_payment"),
    ):
        add(text, {}, target(action, step=step), "grounding")
    # Version 2 adds new utterances, rather than counting repeated memory states.
    previous_texts = {r["text"].lower() for r in rows}
    expanded = [
        "Find me {q} plates of {dish}; spending cap {b}",
        "Our group needs {q} orders of {dish} below {b} rupees",
        "I am shopping for {dish}, {q} servings, maximum {b}",
        "Could we have {dish} for {q} diners within {b}",
        "Show available {dish} for {q} guests under {b}",
        "Lunch plan: {q} portions of {dish}, limit {b}",
        "Help choose {dish} for {q} adults on a {b} rupee budget",
        "Look up {dish}; need {q} portions and can spend {b}",
        "Budget is {b}, dish is {dish}, number of servings is {q}",
        "For {q} of us please find {dish} costing below {b}",
        "Search menus for {q} servings of {dish} within {b}",
        "Need dinner for {q}: {dish}, cap {b} rupees",
        "{dish} kavali {q} portions ki {b} lopu chupinchu",
        "{q} mandiki {dish} kavali kharchu {b} lopala",
        "{dish} chahiye {q} servings ka budget {b} hai",
        "{q} aadmiyon ke liye {dish} dikhao {b} ke andar",
        "Can you locate {dish} for {q} with a price limit of {b}",
        "Please browse {dish} options: {q} portions, up to {b}",
        "Get options for {dish}, {q} people, no more than {b}",
        "We want {q} servings; show {dish} within {b}",
    ]
    for dish in DISHES:
        for q, b in ((1, 210), (2, 370), (3, 620), (4, 810), (5, 1050), (6, 1250)):
            for index, template in enumerate(expanded):
                add(
                    template.format(dish=dish, q=q, b=b),
                    {},
                    target(dish=dish, quantity=q, budget=b),
                    f"v2_search_{index}",
                    "dev" if index in (17, 19) else "train",
                )
        for q in (1, 3, 5):
            context = {
                "dish": dish,
                "quantity": q,
                "budget": 620,
                "sort": "price",
                "stage": "search",
            }
            for n in (1, 2, 5, 7):
                for index, phrase in enumerate(
                    (
                        f"Correction: only {n} servings are needed",
                        f"Please update that to {n} portions and keep the dish",
                        f"Same food for {n} people now",
                        f"We changed our headcount to {n} people",
                    )
                ):
                    add(
                        phrase,
                        context,
                        target(dish=dish, quantity=n, budget=620, sort="price"),
                        "v2_quantity",
                        "dev" if index == 3 else "train",
                    )
            for b in (240, 450, 780, 1100):
                for index, phrase in enumerate(
                    (
                        f"Keep our selection but set spending cap {b}",
                        f"Budget correction: {b} rupees for the same food",
                        f"Leave the portions alone; my budget is {b}",
                        f"Can those options stay below {b} rupees",
                    )
                ):
                    add(
                        phrase,
                        context,
                        target(dish=dish, quantity=q, budget=b, sort="price"),
                        "v2_budget",
                        "dev" if index == 3 else "train",
                    )
    version2_texts = {r["text"].lower() for r in rows if r["split"] == "train"} - previous_texts
    assert len(version2_texts) >= 500
    for row in rows:
        row["new_v2"] = row["text"].lower() not in previous_texts

    previous_v3 = {r["text"].lower() for r in rows}
    # Compound edits require generating several arguments and retaining untouched memory.
    compound = (
        "Keep {dish}; set portions {q} and spending limit {b}",
        "For {dish}, update both quantity to {q} and budget to {b}",
        "Change my {dish} request to {q} servings under {b} rupees",
        "Actually {q} plates of {dish}, with a revised cap of {b}",
        "{dish} ki quantity {q} cheyyi budget {b} pettu",
        "{dish} ke {q} portions karo aur budget {b} rakho",
        "Revise the {dish} plan: {q} servings, ceiling {b}",
    )
    for dish_index, dish in enumerate(DISHES):
        for q in (1, 3, 5, 6, 8):
            for b in (280, 470, 860, 1400):
                context = {
                    "dish": dish,
                    "quantity": 2,
                    "budget": 620,
                    "sort": "price" if dish_index % 2 else "",
                    "stage": "search",
                }
                for index, template in enumerate(compound):
                    add(
                        template.format(dish=dish, q=q, b=b),
                        context,
                        target(dish=dish, quantity=q, budget=b, sort=context["sort"]),
                        f"v3_compound_{index}",
                        "dev" if index == 6 else "train",
                    )
                for index, template in enumerate(
                    (
                        "Keep the dish, but use {q} servings and a {b} rupee limit",
                        "Update just portions to {q} and budget to {b}; retain everything else",
                        "Our revised plan needs {q} plates within {b}; same food",
                    )
                ):
                    add(
                        template.format(q=q, b=b),
                        context,
                        target(dish=dish, quantity=q, budget=b, sort=context["sort"]),
                        "v3_memory_compound",
                        "dev" if index == 2 else "train",
                    )
        context = {"dish": dish, "quantity": 3, "budget": 860, "stage": "search"}
        for replacement in DISHES:
            if replacement != dish:
                for index, template in enumerate(
                    (
                        "Drop {old}; I want {new} while keeping the portions and budget",
                        "My dish choice is now {new}; retain the rest of my request",
                        "Please substitute {new} for {old} without changing the count",
                    )
                ):
                    add(
                        template.format(old=dish, new=replacement),
                        context,
                        target(dish=replacement, quantity=3, budget=860),
                        "v3_replace",
                        "dev" if index == 2 else "train",
                    )
    for action, phrases in {
        "cart": (
            "Let me inspect my basket contents",
            "Bring up the items I selected",
            "I want to check my selected food",
        ),
        "restaurants": (
            "Which eateries can I browse",
            "Let me explore the available kitchens",
            "Show me places selling food",
        ),
        "checkout": (
            "Show the total and let me review it",
            "Take me to the final cost review",
            "I would like to inspect the bill",
        ),
        "favorites": (
            "Bring up my saved food choices",
            "Where are the dishes I bookmarked",
            "Let me browse saved restaurants",
        ),
        "orders": (
            "Where can I see earlier orders",
            "Bring up my request history",
            "Show my previous purchases",
        ),
    }.items():
        for index, phrase in enumerate(phrases):
            add(
                phrase,
                {},
                target(action, step="open_screen"),
                "v3_navigation",
                "dev" if index == 2 else "train",
            )
    for phrase in (
        "I cannot decide on a dish yet",
        "Find food but I have no dish in mind",
        "Can you help me decide what to order",
        "I have not selected any food",
        "Repeat the selection even though I have not chosen one",
    ):
        add(phrase, {}, target("clarify", step="ask_dish"), "v3_missing_context")
    for row in rows:
        row["new_v3"] = row["text"].lower() not in previous_v3
    assert len({r["text"].lower() for r in rows if r["split"] == "train" and r["new_v3"]}) >= 500

    previous_v4 = {r["text"].lower() for r in rows}
    for dish in DISHES:
        for q in (2, 4, 7):
            for b in (330, 680, 1200):
                for diet in ("vegetarian", "vegan"):
                    context = {
                        "dish": dish,
                        "quantity": 1,
                        "budget": 400,
                        "sort": "price" if q == 4 else "",
                        "stage": "search",
                    }
                    for index, template in enumerate(
                        (
                            "Find {diet} alternatives to {dish} for {q} people under {b}",
                            "Update {dish}: {diet} only, {q} portions, limit {b}",
                            "{q} servings of {diet} alternatives to {dish}, budget {b}",
                            "For our {dish} search, use {diet} food, {q} servings and cap {b}",
                        )
                    ):
                        add(
                            template.format(dish=dish, q=q, b=b, diet=diet),
                            context,
                            target(
                                dish=dish, quantity=q, budget=b, diet=diet, sort=context["sort"]
                            ),
                            "v4_compound_diet",
                            "dev" if index == 3 else "train",
                        )
    for row in rows:
        row["new_v4"] = row["text"].lower() not in previous_v4
    assert len({r["text"].lower() for r in rows if r["new_v4"] and r["split"] == "train"}) >= 200

    previous_v5 = {r["text"].lower() for r in rows}
    for dish in DISHES:
        for b in (260, 510, 740, 990, 1500):
            for diet, quantity in (("vegetarian", 3), ("vegan", 5)):
                for sort in ("", "price"):
                    context = {
                        "dish": dish,
                        "quantity": quantity,
                        "budget": 680,
                        "diet": diet,
                        "sort": sort,
                        "stage": "search",
                    }
                    for index, template in enumerate(
                        (
                            "For {dish}, retain the dietary filter and change the cap to {b}",
                            "Do not change portions or diet for {dish}; spend no more than {b}",
                            "Keep all {dish} preferences except the budget, which is now {b}",
                            "My {dish} selection stays the same; revise the spending limit to {b}",
                            "Leave the {dish} diet and portion settings alone, "
                            "with a new limit of {b}",
                        )
                    ):
                        add(
                            template.format(dish=dish, b=b),
                            context,
                            target(dish=dish, quantity=quantity, budget=b, diet=diet, sort=sort),
                            "v5_preserve_preferences",
                            "dev" if index == 4 else "train",
                        )
    for row in rows:
        row["new_v5"] = row["text"].lower() not in previous_v5
    assert len({r["text"].lower() for r in rows if r["new_v5"] and r["split"] == "train"}) >= 100

    previous_v6 = {r["text"].lower() for r in rows}
    from backend.integrations.telegram.commerce_nlp_data import add_examples

    add_examples(add, target)
    for row in rows:
        row["new_v6"] = row["text"].lower() not in previous_v6
    assert len({r["text"].lower() for r in rows if r["new_v6"] and r["split"] == "train"}) >= 500

    labels = {}
    for row in rows:
        assert row["input"] not in labels or labels[row["input"]] == row["target"], (
            "Conflicting dialogue targets"
        )
        labels[row["input"]] = row["target"]
    unique = {row["input"]: row for row in rows}
    rows = list(unique.values())
    new_unique = {r["text"].lower() for r in rows if r["new"]}
    assert len(new_unique) >= 200
    content = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
        from uuid import uuid4

        temporary = OUTPUT.with_name(OUTPUT.name + f".{uuid4().hex}.tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(OUTPUT)

    return rows, len(new_unique)


if __name__ == "__main__":
    rows, count = build()
    print(
        {
            "examples": len(rows),
            "new_unique_commands": count,
            "train": sum(r["split"] == "train" for r in rows),
        }
    )
