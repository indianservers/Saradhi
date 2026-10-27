"""Shared live/simulator entry point for multilingual discovery and guarded backend actions."""

import httpx

from backend.integrations.telegram.accounts import Vault
from backend.integrations.telegram.backend_client import Backend, BackendError
from backend.integrations.telegram.catalog import Catalog, load_catalog
from backend.integrations.telegram.language import enrich


async def process(update, store, sandbox=False, telegram=None):
    from backend.integrations.telegram.bot import reply
    from backend.integrations.telegram.live_checkout import execute

    message = update.get("message") or update.get("callback_query", {}).get("message", {})
    chat = message.get("chat", {})
    if chat.get("type") != "private":
        return None
    chat_id = chat["id"]
    text = update.get("callback_query", {}).get("data", message.get("text", ""))

    class SandboxVault:
        def get(self, chat):
            return None

        def close(self):
            pass

    vault = SandboxVault() if sandbox else Vault()
    backend = Backend(chat_id, vault)
    try:
        if text.startswith("Link "):
            ok = vault.redeem(chat_id, text[5:].strip())
            return {
                **reply(
                    "Account linked. Open Restaurants for the live catalog."
                    if ok
                    else "Pairing code invalid or expired."
                ),
                "chat_id": chat_id,
            }
        profile = store.profile(chat_id)
        if message.get("voice"):
            if not telegram or sandbox:
                return {
                    **reply("Voice testing requires a Telegram voice message."),
                    "chat_id": chat_id,
                }
            voice = message["voice"]
            if voice.get("duration", 0) > 120 or voice.get("file_size", 0) > 10_000_000:
                return {
                    **reply("Send a voice message under 2 minutes and 10 MB."),
                    "chat_id": chat_id,
                }
            from backend.integrations.telegram.voice import transcribe

            transcript = await transcribe(voice, telegram)
            profile["voice_draft"] = transcript
            with store.db:
                store.save_profile(chat_id, profile)
            return {
                "chat_id": chat_id,
                "text": "I heard: “"
                + transcript
                + "”\nConfirm this transcription before it is used.",
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {"text": "Use transcript", "callback_data": "Use transcript"},
                            {"text": "Discard voice", "callback_data": "Discard voice"},
                        ]
                    ]
                },
            }
        if text in ("Use transcript", "Discard voice"):
            transcript = profile.pop("voice_draft", "")
            with store.db:
                store.save_profile(chat_id, profile)
            if text == "Discard voice" or not transcript:
                return {**reply("Voice draft discarded."), "chat_id": chat_id}
            update = {
                "update_id": update["update_id"],
                "message": {"chat": chat, "text": transcript},
            }
        store.live_mode = not sandbox
        if sandbox:
            store.catalog = load_catalog()
        elif backend.tokens:
            store.catalog = await backend.catalog(profile.get("city_id"))
        else:
            store.catalog = Catalog(demo=False, restaurants=[])
        result = store.process(await enrich(update, store))
        if result and store.neural:
            result["nlp"] = {
                key: store.neural.get(key)
                for key in (
                    "structured",
                    "confidence",
                    "query",
                    "neural_promoted",
                    "plan",
                    "plan_raw",
                    "brain_version",
                )
            }
        if result and not sandbox and not backend.tokens:
            result["text"] += (
                "\nLink your customer account using a pairing code from the control page. "
                "No demo menus are used in live Telegram."
            )
        action = result.pop("live_action", None) if result else None
        expected_quote = result.pop("expected_quote", None) if result else None
        if action:
            if sandbox:
                result["text"] = (
                    "Simulator: live checkout/merchant/payment requires a linked backend account. "
                    "No real order was sent."
                )
            else:
                result = await execute(action, chat_id, store, backend, expected_quote)
        return result
    except (BackendError, httpx.HTTPError, ValueError) as error:
        message = (
            str(error)
            if isinstance(error, BackendError)
            else "Service unavailable; no success assumed. Try again."
        )
        return {**reply(message), "chat_id": chat_id}
    finally:
        await backend.client.aclose()
        vault.close()
