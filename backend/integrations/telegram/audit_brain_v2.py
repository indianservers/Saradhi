"""Frozen fresh composition audit, excluded from the version 2 training corpus."""

from backend.integrations.telegram.brain_data import target

CASES = [
    (
        {},
        "Please find 7 portions of masala dosa below 980 rupees",
        target(dish="masala dosa", quantity=7, budget=980),
    ),
    ({}, "Paneer for 2 please, spending limit 460", target(dish="paneer", quantity=2, budget=460)),
    (
        {},
        "3 servings egg biryani chahiye 690 ke andar",
        target(dish="egg biryani", quantity=3, budget=690),
    ),
    (
        {},
        "Chicken biryani kavali 5 portions 1150 lopu",
        target(dish="chicken biryani", quantity=5, budget=1150),
    ),
    (
        {
            "dish": "mutton biryani",
            "quantity": 3,
            "budget": 810,
            "sort": "price",
            "stage": "search",
        },
        "Two guests cancelled; now we need 1 portion",
        target(dish="mutton biryani", quantity=1, budget=810, sort="price"),
    ),
    (
        {"dish": "masala dosa", "quantity": 2, "budget": 370, "sort": "price", "stage": "search"},
        "Retain that dish and change my budget to 490",
        target(dish="masala dosa", quantity=2, budget=490, sort="price"),
    ),
    (
        {"dish": "paneer", "quantity": 5, "budget": 1050, "stage": "search"},
        "Keep paneer but adjust servings to 6 and budget to 1200",
        target(dish="paneer", quantity=6, budget=1200),
    ),
    (
        {"dish": "egg biryani", "quantity": 2, "budget": 370, "stage": "search"},
        "Replace egg biryani with veg biryani for the same number of people",
        target(dish="veg biryani", quantity=2, budget=370),
    ),
    ({}, "Keep my last choice and double it", target("clarify", step="ask_dish")),
    ({}, "Go ahead and debit my account immediately", target("clarify", step="review_required")),
    (
        {},
        "Can a payment screenshot count as confirmation",
        target("explain", step="explain_payment"),
    ),
    ({}, "Does that meal contain peanuts", target("clarify", step="ask_allergens")),
]
