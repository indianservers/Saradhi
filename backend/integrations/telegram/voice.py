"""Download bounded Telegram voice media for local ASR; never execute the transcript."""

import base64

import httpx

from backend.integrations.telegram.backend_client import BackendError


async def transcribe(voice, telegram):
    try:
        info = await telegram.call("getFile", file_id=voice["file_id"])
        file_url = telegram.base.replace("/bot", "/file/bot") + info["file_path"]
        content = bytearray()
        async with telegram.client.stream("GET", file_url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > 10_000_000:
                    raise BackendError("Voice file exceeds 10 MB.")
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "http://127.0.0.1:8766/transcribe",
                json={"audio": base64.b64encode(content).decode()},
            )
            response.raise_for_status()
            text = response.json().get("text", "").strip()
        if not text:
            raise BackendError(
                "Could not understand that voice message. Type your request or try again."
            )
        return text[:500]
    except (httpx.HTTPError, RuntimeError, ValueError, KeyError):
        raise BackendError(
            "Local voice transcription is unavailable. No order was sent; please type your request."
        ) from None
