"""Train a multilingual character encoder-decoder, never an order-executing classifier."""

import json
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

import numpy as np
import tensorflow as tf
import tf_keras as keras

from backend.integrations.telegram.brain_data import training_source
from backend.integrations.telegram.nlp_dataset import ROOT, build

OUTPUT = ROOT / ".local/models/quickbuddy-nlp"


def main(dataset=None, output_dir=OUTPUT, epochs=60, max_input=120, max_output=80, resume=False):
    keras.utils.set_random_seed(20261027)
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    rows = dataset if dataset is not None else build()
    chars = sorted(set("".join(training_source(r).lower() + r["target"] for r in rows)))
    vocab = {char: index + 4 for index, char in enumerate(chars)}

    def encode(text, length, target=False):
        ids = [vocab.get(c, 3) for c in text.lower()]
        ids = ([1] + ids + [2]) if target else ids
        return (ids[:length] + [0] * length)[:length]

    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] != "train"]
    x = np.array([encode(training_source(r), max_input) for r in train], dtype="int32")
    targets = np.array([encode(r["target"], max_output + 1, True) for r in train], dtype="int32")
    source = None
    initial_epoch = 0
    if resume and (output_dir / "checkpoint.keras").exists():
        prior = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
        assert prior["vocab"] == vocab, "Checkpoint vocabulary must match this corpus"
        source = keras.models.load_model(output_dir / "checkpoint.keras")
        initial_epoch = int(source.optimizer.iterations.numpy()) // ((len(train) + 23) // 24)
        print(
            json.dumps(
                {"resumed_epoch": initial_epoch, "max_input": max_input, "max_output": max_output}
            ),
            flush=True,
        )
    enc = keras.Input(shape=(max_input,), dtype="int32", name="text")
    dec = keras.Input(shape=(max_output,), dtype="int32", name="prefix")
    embedding = (
        source.get_layer("embedding")
        if source
        else keras.layers.Embedding(len(vocab) + 4, 64, mask_zero=True, name="embedding")
    )
    encoder = (
        source.get_layer("encoder")
        if source
        else keras.layers.GRU(160, return_sequences=True, return_state=True, name="encoder")
    )
    encoded, state = encoder(embedding(enc))
    decoder = (
        source.get_layer("decoder")
        if source
        else keras.layers.GRU(160, return_sequences=True, return_state=True, name="decoder")
    )
    seq, _ = decoder(embedding(dec), initial_state=state)
    attention = (
        source.get_layer("attention")
        if source
        else keras.layers.AdditiveAttention(name="attention")
    )
    attended = attention([seq, encoded])
    joined = keras.layers.Concatenate(name="context")([seq, attended])
    dense = (
        source.get_layer("tokens")
        if source
        else keras.layers.Dense(len(vocab) + 4, activation="softmax", name="tokens")
    )
    output = dense(joined)
    model = keras.Model([enc, dec], output)
    model.compile(
        optimizer=source.optimizer if source else keras.optimizers.Adam(0.003),
        loss="sparse_categorical_crossentropy",
        weighted_metrics=["accuracy"],
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "vocab": vocab,
        "max_input": max_input,
        "max_output": max_output,
        "commands": len(rows),
        "unique_utterances": len({r["text"] for r in rows}),
        "new_unique_commands": len({r["text"] for r in rows if r.get("new")}),
        "new_training_commands": len(
            {r["text"] for r in rows if r.get("new") and r["split"] == "train"}
        ),
        "contextual": any("context" in r for r in rows),
        "resumed_epoch": initial_epoch,
        "training_examples": len(train),
        "held_out_examples": len(test),
        "architecture": "Character GRU encoder-decoder with generated intent and slots",
        "synthetic": True,
        "split": "development paraphrase templates; separate audit required",
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
    )

    class Progress(keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            (output_dir / "progress.json").write_text(
                json.dumps({"epoch": epoch + 1, "epochs": epochs, **(logs or {})}), encoding="utf-8"
            )
            if (epoch + 1) % 5 == 0:
                print(json.dumps({"epoch": epoch + 1, **(logs or {})}), flush=True)
                model.save(output_dir / "checkpoint.keras")

    model.fit(
        [x, targets[:, :-1]],
        targets[:, 1:],
        sample_weight=(targets[:, 1:] != 0).astype("float32"),
        epochs=epochs,
        initial_epoch=initial_epoch,
        batch_size=24,
        verbose=0,
        callbacks=[Progress()],
    )
    model.save(output_dir / "model.keras")
    from backend.integrations.telegram.trained_nlp import Interpreter

    interpreter = Interpreter(output_dir)
    results = [
        {
            "text": r["text"],
            "expected": r["target"],
            "actual": interpreter.generate(training_source(r))[0],
        }
        for r in test
    ]
    exact = sum(r["actual"] == r["expected"] for r in results) / len(results)
    intent = sum(r["actual"].split("|")[0] == r["expected"].split("|")[0] for r in results) / len(
        results
    )
    report = {**metadata, "exact_match": exact, "intent_accuracy": intent, "results": results}
    (output_dir / "evaluation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps({"complete": True, "exact_match": exact, "intent_accuracy": intent}), flush=True
    )


if __name__ == "__main__":
    main()
