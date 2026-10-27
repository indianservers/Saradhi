"""Autoregressive structured command generation with an explicit confidence gate."""

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
import tf_keras as keras


class Interpreter:
    def accepts(self, text):
        return len(text) <= self.metadata["max_input"]

    def __init__(self, path):
        path = Path(path)
        self.metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
        self.vocab = self.metadata["vocab"]
        self.reverse = {value: key for key, value in self.vocab.items()}
        self.model = keras.models.load_model(path / "model.keras", compile=False)
        embedding = self.model.get_layer("embedding")
        encoder = self.model.get_layer("encoder")
        decoder = self.model.get_layer("decoder")
        dense = self.model.get_layer("tokens")
        attention = self.model.get_layer("attention")

        @tf.function(input_signature=[tf.TensorSpec((1, self.metadata["max_input"]), tf.int32)])
        def generate(tokens):
            encoded, hidden = encoder(embedding(tokens), training=False)
            current = tf.ones((1, 1), dtype=tf.int32)
            output = tf.TensorArray(tf.int32, size=0, dynamic_size=True)
            confidence = tf.constant(0.0)
            index = tf.constant(0)

            def condition(index, current, hidden, output, confidence):
                return tf.logical_and(index < self.metadata["max_output"], current[0, 0] != 2)

            def step(index, current, hidden, output, confidence):
                values, hidden = decoder(embedding(current), initial_state=hidden, training=False)
                attended = attention([values, encoded], mask=[None, tf.not_equal(tokens, 0)])
                probs = dense(tf.concat([values, attended], axis=-1))[:, -1, :]
                next_token = tf.argmax(probs, axis=-1, output_type=tf.int32)
                output = output.write(index, next_token[0])
                confidence += tf.math.log(tf.reduce_max(probs) + 1e-8)
                return index + 1, next_token[:, None], hidden, output, confidence

            count, _, _, output, confidence = tf.while_loop(
                condition, step, (index, current, hidden, output, confidence)
            )
            return output.stack(), tf.exp(confidence / tf.cast(tf.maximum(count, 1), tf.float32))

        self._generate = generate

    def generate(self, text):
        length = self.metadata["max_input"]
        ids = [self.vocab.get(char, 3) for char in text.lower()][:length]
        ids += [0] * (length - len(ids))
        output, confidence = self._generate(np.array([ids], dtype="int32"))
        return "".join(self.reverse.get(int(i), "") for i in output.numpy() if int(i) > 3), float(
            confidence
        )
