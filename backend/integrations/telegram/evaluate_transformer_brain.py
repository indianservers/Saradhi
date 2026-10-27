"""Development evaluation and the fixed, previously untrained conversation audit."""

import hashlib
import json
import os
from pathlib import Path

from backend.integrations.telegram.brain_data import OUTPUT
from backend.integrations.telegram.nlp_dataset import ROOT

if __name__ == "__main__":
    from backend.integrations.telegram.audit_brain import evaluate
    from backend.integrations.telegram.transformer_brain import TransformerBrain

    folder = Path(
        os.environ.get(
            "QUICKBUDDY_TRAIN_OUTPUT", str(ROOT / ".local/models/quickbuddy-transformer-brain")
        )
    )
    model = TransformerBrain(folder)
    rows = [json.loads(line) for line in OUTPUT.read_text(encoding="utf-8").splitlines()]
    test = [r for r in rows if r["split"] != "train"]
    results = []
    for start in range(0, len(test), 8):
        batch = test[start : start + 8]
        predictions = model.batch([r["input"] for r in batch])
        for row, (raw, score) in zip(batch, predictions, strict=True):
            results.append(
                {
                    "text": row["text"],
                    "family": row["family"],
                    "context": row["context"],
                    "expected": row["target"],
                    "actual": raw,
                    "confidence": score,
                    "correct": raw == row["target"],
                }
            )
        if start % 80 == 0:
            print(json.dumps({"evaluated": len(results), "of": len(test)}), flush=True)
    contextual = [r for r in results if r["context"]]
    previous = [r for r in results if not r["family"].startswith(("v2_", "v3_", "v4_", "v5_"))]
    expanded = [r for r in results if r["family"].startswith(("v2_", "v3_", "v4_", "v5_"))]
    previous_v2 = [r for r in results if not r["family"].startswith(("v3_", "v4_", "v5_"))]
    newest = [r for r in results if r["family"].startswith(("v3_", "v4_", "v5_"))]
    previous_v3 = [r for r in results if not r["family"].startswith(("v4_", "v5_"))]
    current_v4 = [r for r in results if r["family"].startswith("v4_")]
    previous_v4 = [r for r in results if not r["family"].startswith("v5_")]
    current_v5 = [r for r in results if r["family"].startswith("v5_")]
    metadata = model.metadata
    metadata["model_sha256"] = hashlib.sha256((folder / "tf_model.h5").read_bytes()).hexdigest()
    metadata["commands"] = len(rows)
    metadata["held_out_examples"] = len(test)
    report = {
        **metadata,
        "exact_match": sum(r["correct"] for r in results) / len(results),
        "contextual_exact_match": sum(r["correct"] for r in contextual) / len(contextual),
        "intent_accuracy": sum(
            r["expected"].split("|")[0] == r["actual"].split("|")[0] for r in results
        )
        / len(results),
        "previous_development_exact": sum(r["correct"] for r in previous) / len(previous),
        "expanded_development_exact": sum(r["correct"] for r in expanded) / len(expanded)
        if expanded
        else None,
        "previous_v2_development_exact": sum(r["correct"] for r in previous_v2) / len(previous_v2),
        "newest_development_exact": sum(r["correct"] for r in newest) / len(newest)
        if newest
        else None,
        "previous_v3_development_exact": sum(r["correct"] for r in previous_v3) / len(previous_v3),
        "v4_development_exact": sum(r["correct"] for r in current_v4) / len(current_v4)
        if current_v4
        else None,
        "previous_v4_development_exact": sum(r["correct"] for r in previous_v4) / len(previous_v4),
        "v5_development_exact": sum(r["correct"] for r in current_v5) / len(current_v5)
        if current_v5
        else None,
        "results": results,
    }
    (folder / "evaluation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    audit = {**evaluate(model), "model_sha256": metadata["model_sha256"]}
    (folder / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    from backend.integrations.telegram.audit_brain_v2 import CASES as fresh_cases

    fresh = evaluate(model, fresh_cases)
    (folder / "audit-v2.json").write_text(
        json.dumps(fresh, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (folder / "deployment.json").write_text(
        json.dumps(
            {
                "model_sha256": metadata["model_sha256"],
                "weight_file": "tf_model.h5",
                "mode": "bounded_read_only_planner",
                "independent_exact_match": audit["exact_match"],
            }
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "development_exact": report["exact_match"],
                "previous_v2_development_exact": report["previous_v2_development_exact"],
                "newest_development_exact": report["newest_development_exact"],
                "previous_development_exact": report["previous_development_exact"],
                "expanded_development_exact": report["expanded_development_exact"],
                "fresh_composition_exact": fresh["exact_match"],
                "contextual_exact": report["contextual_exact_match"],
                "independent_exact": audit["exact_match"],
                "abstention_rate": audit["abstention_rate"],
            }
        ),
        flush=True,
    )
