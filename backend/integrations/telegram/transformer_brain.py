"""Pretrained TensorFlow language model generating typed dialogue plans."""

import json
import os
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSeq2SeqLM


class TransformerBrain:
    def __init__(self, folder):
        folder = Path(folder)
        self.metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        self.tokenizer = AutoTokenizer.from_pretrained(folder)
        self.model = TFAutoModelForSeq2SeqLM.from_pretrained(folder)
        self.prefix = self.metadata["prefix"]

    def accepts(self, text):
        customer = text.split("customer:", 1)[-1]
        if self.tokenizer.unk_token_id in self.tokenizer(customer)["input_ids"]:
            return False
        return len(self.tokenizer(self.prefix + text)["input_ids"]) <= self.metadata["input_tokens"]

    def batch(self, texts):
        inputs = self.tokenizer(
            [self.prefix + t for t in texts],
            padding=True,
            truncation=True,
            max_length=self.metadata["input_tokens"],
            return_tensors="tf",
        )
        output = self.model.generate(
            **inputs,
            max_new_tokens=self.metadata["output_tokens"],
            do_sample=False,
            return_dict_in_generate=True,
            output_scores=True,
        )
        decoded = self.tokenizer.batch_decode(output.sequences, skip_special_tokens=True)
        scores = np.zeros(len(texts))
        counts = np.zeros(len(texts))
        for index, logits in enumerate(output.scores):
            token = output.sequences[:, index + 1].numpy()
            probability = tf.nn.softmax(logits, axis=-1).numpy()
            for row, selected in enumerate(token):
                if selected != self.tokenizer.pad_token_id:
                    scores[row] += np.log(max(float(probability[row, selected]), 1e-9))
                    counts[row] += 1
        confidence = np.exp(scores / np.maximum(counts, 1))
        return [
            ("|".join(part.strip() for part in text.strip().split("|")), float(score))
            for text, score in zip(decoded, confidence, strict=True)
        ]

    def generate(self, text):
        return self.batch([text])[0]
