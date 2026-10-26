"""Deterministic bounded task-to-pilot recommendation; never commits assignments."""


def greedy_one_to_one(tasks, pilots, score_candidate):
    """Return suggestions for distinct tasks/pilots; hard filters are caller-owned."""
    remaining = {pilot["id"]: max(0, int(pilot.get("remaining_capacity", 1))) for pilot in pilots}
    suggestions = []
    candidates = []
    for task in tasks:
        for pilot in pilots:
            if remaining.get(pilot["id"], 0) > 0:
                score = score_candidate(task, pilot)
                candidates.append((score, str(task["id"]), str(pilot["id"]), task, pilot))
    for score, _, pilot_key, task, pilot in sorted(candidates, key=lambda row: row[:3]):
        if remaining.get(pilot["id"], 0) <= 0 or any(
            item["task_id"] == str(task["id"]) for item in suggestions
        ):
            continue
        remaining[pilot["id"]] -= 1
        suggestions.append(
            {"task_id": str(task["id"]), "pilot_id": pilot_key, "score": round(score, 5)}
        )
    return suggestions
