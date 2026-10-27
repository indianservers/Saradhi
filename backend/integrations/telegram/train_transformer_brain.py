"""Instruction-tune pretrained TensorFlow FLAN-T5 for context-to-tool-plan generation."""

import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
import tf_keras as keras
from transformers import AutoTokenizer, TFAutoModelForSeq2SeqLM

from backend.integrations.telegram.nlp_dataset import ROOT

PREFIX = "Quickbuddy dialogue plan: "


if __name__ == "__main__":
    keras.utils.set_random_seed(20261028)
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    folder = Path(
        os.environ.get(
            "QUICKBUDDY_TRAIN_OUTPUT", str(ROOT / ".local/models/quickbuddy-transformer-brain")
        )
    )
    folder.mkdir(parents=True, exist_ok=True)
    rows = [
        json.loads(line)
        for line in Path(__file__)
        .with_name("brain-commands.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    train = [r for r in rows if r["split"] == "train"]
    source = Path(
        os.environ.get("QUICKBUDDY_TRAIN_SOURCE", str(ROOT / ".local/models/flan-t5-small"))
    )
    epochs = int(os.environ.get("QUICKBUDDY_TRAIN_EPOCHS", "5"))
    learning_rate = float(os.environ.get("QUICKBUDDY_TRAIN_RATE", "0.0003"))
    action_weight = int(os.environ.get("QUICKBUDDY_ACTION_WEIGHT", "1"))
    assert action_weight >= 1
    unique_train = train
    train = train + [r for r in train if r["target"].split("|")[0] != "search"] * (
        action_weight - 1
    )
    tokenizer = AutoTokenizer.from_pretrained(source)
    model = TFAutoModelForSeq2SeqLM.from_pretrained(source)
    # Preserve pretrained language representations and train the decoder's planning layers.
    model.encoder.trainable = False
    model.shared.trainable = False
    for block in model.decoder.block[:-3]:
        block.trainable = False
    input_lengths = [
        len(ids) for ids in tokenizer([PREFIX + r["input"] for r in train])["input_ids"]
    ]
    output_lengths = [
        len(ids) for ids in tokenizer(text_target=[r["target"] for r in train])["input_ids"]
    ]
    assert max(input_lengths) <= 112, "Training inputs exceed the serving context limit"
    assert max(output_lengths) <= 48, "Training targets would be truncated"
    inputs = tokenizer(
        [PREFIX + r["input"] for r in train],
        padding="max_length",
        truncation=True,
        max_length=max(input_lengths),
        return_tensors="np",
    )
    labels = tokenizer(
        text_target=[r["target"] for r in train],
        padding="max_length",
        truncation=True,
        max_length=max(output_lengths),
        return_tensors="np",
    )["input_ids"]
    labels = np.where(labels == tokenizer.pad_token_id, -100, labels).astype("int32")
    x = {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
        "labels": labels,
    }
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=learning_rate, clipnorm=1.0))
    metadata = {
        "architecture": "Pretrained FLAN-T5 TensorFlow encoder-decoder instruction tuning",
        "examples": len(rows),
        "training_examples": len(unique_train),
        "fit_examples_with_replay": len(train),
        "development_examples": len(rows) - len(unique_train),
        "new_unique_commands": len({r["text"] for r in rows if r["new"]}),
        "new_training_commands": len({r["text"] for r in train if r["new"]}),
        "new_v2_training_commands": len({r["text"] for r in train if r.get("new_v2")}),
        "new_v2_unique_commands": len({r["text"] for r in rows if r.get("new_v2")}),
        "unique_utterances": len({r["text"] for r in rows}),
        "input_tokens": 112,
        "output_tokens": 48,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "non_search_replay_copies": action_weight,
        "initial_checkpoint": str(source),
        "new_v3_training_commands": len({r["text"] for r in train if r.get("new_v3")}),
        "new_v3_unique_commands": len({r["text"] for r in rows if r.get("new_v3")}),
        "new_v4_training_commands": len({r["text"] for r in train if r.get("new_v4")}),
        "new_v4_unique_commands": len({r["text"] for r in rows if r.get("new_v4")}),
        "new_v5_training_commands": len({r["text"] for r in train if r.get("new_v5")}),
        "new_v5_unique_commands": len({r["text"] for r in rows if r.get("new_v5")}),
        "prefix": PREFIX,
        "synthetic": True,
        "dataset_sha256": hashlib.sha256(
            Path(__file__).with_name("brain-commands.jsonl").read_bytes()
        ).hexdigest(),
        "max_observed_input_tokens": max(input_lengths),
        "max_observed_target_tokens": max(output_lengths),
        "trainable_parameters": sum(int(np.prod(v.shape)) for v in model.trainable_variables),
    }
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata), flush=True)

    class Progress(keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            print(json.dumps({"epoch": epoch + 1, **(logs or {})}), flush=True)
            (folder / "progress.json").write_text(
                json.dumps({"epoch": epoch + 1, "epochs": epochs, **(logs or {})}), encoding="utf-8"
            )

    model.fit(x=x, batch_size=8, epochs=epochs, verbose=0, callbacks=[Progress()])
    model.save_pretrained(folder)
    tokenizer.save_pretrained(folder)
    print("Transformer planner training complete", flush=True)
