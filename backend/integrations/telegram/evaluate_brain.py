"""Evaluate all development rows and the frozen independent conversation audit."""

import hashlib
import json

from backend.integrations.telegram.brain_data import OUTPUT
from backend.integrations.telegram.nlp_dataset import ROOT

if __name__ == "__main__":
    from backend.integrations.telegram.audit_brain import evaluate
    from backend.integrations.telegram.trained_nlp import Interpreter

    folder = ROOT / ".local/models/quickbuddy-brain"
    model = Interpreter(folder)
    rows = [json.loads(line) for line in OUTPUT.read_text(encoding="utf-8").splitlines()]
    test = [r for r in rows if r["split"] != "train"]
    existing = json.loads((folder / "evaluation.json").read_text(encoding="utf-8"))
    assert len(existing["results"]) == len(test), "Evaluate the complete development split first"
    results = [
        {**result, "context": row["context"], "correct": result["actual"] == row["target"]}
        for row, result in zip(test, existing["results"], strict=True)
    ]
    metadata = model.metadata
    metadata["held_out_examples"] = len(test)
    metadata["model_sha256"] = hashlib.sha256((folder / "model.keras").read_bytes()).hexdigest()
    metadata["architecture"] = (
        "Character encoder-decoder with additive attention and conversation memory"
    )
    contextual = [r for r in results if r["context"]]
    report = {
        **metadata,
        "exact_match": sum(r["correct"] for r in results) / len(results),
        "contextual_exact_match": sum(r["correct"] for r in contextual) / len(contextual),
        "intent_accuracy": sum(
            r["expected"].split("|")[0] == r["actual"].split("|")[0] for r in results
        )
        / len(results),
        "results": results,
    }
    for name, value in (("metadata.json", metadata), ("evaluation.json", report)):
        (folder / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    audit = {**evaluate(model), "model_sha256": metadata["model_sha256"]}
    (folder / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (folder / "deployment.json").write_text(
        json.dumps(
            {
                "model_sha256": metadata["model_sha256"],
                "mode": "bounded_read_only_planner",
                "order_writes": "explicit_quote_confirmation_only",
                "independent_exact_match": audit["exact_match"],
            }
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "development_examples": len(results),
                "development_exact": report["exact_match"],
                "contextual_exact": report["contextual_exact_match"],
                "independent_examples": audit["examples"],
                "independent_exact": audit["exact_match"],
                "abstention_rate": audit["abstention_rate"],
            }
        ),
        flush=True,
    )
