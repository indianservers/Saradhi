"""Train a separate candidate: context + utterance -> generated multi-slot dialogue plan."""

from backend.integrations.telegram.brain_data import build
from backend.integrations.telegram.nlp_dataset import ROOT
from backend.integrations.telegram.train_nlp import main

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    rows, count = build()
    print({"new_unique_commands": count, "examples": len(rows)}, flush=True)
    main(
        dataset=rows,
        output_dir=ROOT / ".local/models/quickbuddy-brain",
        epochs=45,
        max_input=144,
        max_output=64,
        resume=args.resume,
    )
