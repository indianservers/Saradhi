"""Local TensorFlow encoder-decoder inference, isolated from commerce and credentials."""

import os
import threading
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parents[3] / ".local/huggingface"))

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from backend.integrations.telegram.dialogue_brain import Memory

app = FastAPI(docs_url=None, redoc_url=None)
MODEL = "google/flan-t5-small"
LOCAL_MODEL = Path(__file__).resolve().parents[3] / ".local/models/flan-t5-small"
tokenizer = None
model = None
failure = None
lock = threading.Lock()
trained = None
evaluation = None
speech = None
speech_failure = None
brain = None
brain_evaluation = None


def load_brain():
    global brain, brain_evaluation
    transformer_path = LOCAL_MODEL.parent / "quickbuddy-transformer-brain"
    path = (
        transformer_path
        if (transformer_path / "deployment.json").exists()
        else LOCAL_MODEL.parent / "quickbuddy-brain"
    )
    if not (path / "deployment.json").exists():
        return False
    import hashlib
    import json

    deployment = json.loads((path / "deployment.json").read_text(encoding="utf-8"))
    if (
        hashlib.sha256(
            (path / deployment.get("weight_file", "model.keras")).read_bytes()
        ).hexdigest()
        != deployment["model_sha256"]
    ):
        return False

    if path == transformer_path:
        from backend.integrations.telegram.transformer_brain import TransformerBrain

        candidate = TransformerBrain(path)
    else:
        from backend.integrations.telegram.trained_nlp import Interpreter

        candidate = Interpreter(path)
    report = json.loads((path / "evaluation.json").read_text(encoding="utf-8"))
    if (path / "audit.json").exists():
        report["audit"] = json.loads((path / "audit.json").read_text(encoding="utf-8"))
    brain, brain_evaluation = candidate, report
    return True


@app.post("/brain/reload")
def reload_brain(request: Request):
    if request.headers.get("X-Quickbuddy-Local-Request") != "1":
        raise HTTPException(403, "Use the local control page to reload models.")
    with lock:
        return {"loaded": load_brain()}


def load_voice():
    global speech, speech_failure
    try:
        from faster_whisper import WhisperModel

        speech = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8",
            download_root=str(LOCAL_MODEL.parent / "whisper"),
        )
    except Exception as error:
        speech_failure = type(error).__name__


def load():
    global tokenizer, model, failure, trained, evaluation
    try:
        from transformers import AutoTokenizer, TFAutoModelForSeq2SeqLM

        source = str(LOCAL_MODEL) if (LOCAL_MODEL / "tf_model.h5").exists() else MODEL
        tokenizer = AutoTokenizer.from_pretrained(source)
        model = TFAutoModelForSeq2SeqLM.from_pretrained(source)
        print("TensorFlow FLAN-T5 ready", flush=True)
        path = LOCAL_MODEL.parent / "quickbuddy-nlp"
        if (path / "model.keras").exists():
            import json

            from backend.integrations.telegram.trained_nlp import Interpreter

            trained = Interpreter(path)
            evaluation = json.loads((path / "evaluation.json").read_text(encoding="utf-8"))
            if (path / "audit.json").exists():
                audit = json.loads((path / "audit.json").read_text(encoding="utf-8"))
                evaluation["audit_exact_match"] = audit["exact_match"]
                evaluation["audit_examples"] = audit["examples"]
        load_brain()
    except Exception as error:
        failure = type(error).__name__
        print("Model unavailable: " + failure, flush=True)


@app.get("/health")
def health():
    return {
        "ready": model is not None,
        "model": MODEL,
        "engine": "TensorFlow text-to-text transformer",
        "error": failure,
        "trained_ready": trained is not None,
        "training": {
            key: evaluation.get(key)
            for key in (
                "commands",
                "training_examples",
                "held_out_examples",
                "architecture",
                "contextual_exact_match",
                "trainable_parameters",
                "exact_match",
                "intent_accuracy",
                "audit_exact_match",
                "audit_examples",
            )
        }
        if evaluation
        else None,
        "voice_ready": speech is not None,
        "voice_error": speech_failure,
        "brain_ready": brain is not None,
        "brain": {
            key: brain_evaluation.get(key)
            for key in (
                "commands",
                "unique_utterances",
                "new_unique_commands",
                "new_training_commands",
                "new_v2_training_commands",
                "new_v2_unique_commands",
                "new_v3_training_commands",
                "new_v3_unique_commands",
                "new_v4_training_commands",
                "new_v4_unique_commands",
                "new_v5_training_commands",
                "new_v5_unique_commands",
                "new_v6_training_commands",
                "new_v6_unique_commands",
                "architecture",
                "contextual_exact_match",
                "trainable_parameters",
                "exact_match",
                "training_examples",
                "held_out_examples",
            )
        }
        if brain_evaluation
        else None,
        "brain_audit_exact": brain_evaluation.get("audit", {}).get("exact_match")
        if brain_evaluation
        else None,
    }


class Query(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    previous: str = Field(default="", max_length=500)
    context: Memory = Field(default_factory=Memory)


@app.post("/understand")
def understand(body: Query):
    if model is None:
        return {"ready": False, "query": ""}
    from backend.integrations.telegram.dialogue_brain import (
        grounded_plan,
        model_input,
        parse_plan,
    )

    memory = body.context
    structured, confidence = "", 0.0
    with lock:
        brain_input = model_input(body.text, memory)
        raw, score = (
            brain.generate(brain_input) if brain and brain.accepts(brain_input) else ("", 0.0)
        )
        if not raw and trained:
            structured, confidence = trained.generate(body.text)
        if not raw and structured and confidence >= 0.9:
            fields = structured.split("|")
            if len(fields) == 5:
                raw = "|".join(
                    fields + ["", "show_matches" if fields[0] == "search" else "open_screen"]
                )
                score = confidence
        plan = grounded_plan(parse_plan(raw, score, memory), body.text, memory)
    return {
        "ready": True,
        "query": plan.dish[:150] if plan and plan.action == "search" else "",
        "model": MODEL,
        "structured": structured,
        "confidence": confidence,
        "plan": plan.model_dump() if plan else None,
        "plan_raw": raw,
        "plan_confidence": score,
        "brain_version": brain.metadata.get("architecture", "context-v1") if brain else None,
        "neural_promoted": bool(
            evaluation
            and evaluation["intent_accuracy"] >= 0.9
            and evaluation["exact_match"] >= 0.75
        ),
    }


class Audio(BaseModel):
    audio: str = Field(min_length=1, max_length=14000000)


@app.post("/transcribe")
def transcribe(body: Audio):
    import base64
    from io import BytesIO

    from fastapi import HTTPException

    if speech is None:
        raise HTTPException(503, "Local transcription is loading or unavailable.")
    try:
        audio = base64.b64decode(body.audio, validate=True)
        from backend.integrations.telegram.nlp_dataset import DISHES

        vocabulary = ", ".join(DISHES)
        segments, info = speech.transcribe(
            BytesIO(audio),
            beam_size=5,
            vad_filter=True,
            initial_prompt="Food ordering: " + vocabulary,
            hotwords=vocabulary,
        )
        return {
            "text": " ".join(s.text for s in segments)[:500],
            "language": info.language,
            "confirmation_required": True,
        }
    except Exception:
        raise HTTPException(422, "Audio could not be transcribed.") from None


if __name__ == "__main__":
    import uvicorn

    threading.Thread(target=load, daemon=True).start()
    threading.Thread(target=load_voice, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8766, access_log=False)
