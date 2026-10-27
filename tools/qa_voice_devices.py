"""Run the two Android peers in order, accepting only their microphone prompts."""

import os
import re
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLUTTER = os.environ.get("FLUTTER_QA_BIN", "C:/tools/flutter/bin/flutter.bat")
ADB = str(Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/platform-tools/adb.exe")


def device_for(variable, emulator):
    override = os.environ.get(variable)
    if override:
        return override
    result = subprocess.run([ADB, "devices"], capture_output=True, text=True, check=True)
    matches = [
        line.split()[0]
        for line in result.stdout.splitlines()
        if line.endswith("\tdevice") and line.startswith("emulator-") == emulator
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Set {variable} to select one connected Android device")
    return matches[0]


BROWSER_PEER = os.environ.get("QA_BROWSER_PEER") == "true"
PHONE = "" if BROWSER_PEER else device_for("QA_ANDROID_DEVICE", False)
EMULATOR = device_for("QA_ANDROID_EMULATOR", True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    environment = {**os.environ, "TEMP": "C:/tmp/quickbuddy-java", "TMP": "C:/tmp/quickbuddy-java"}
    ready, stop = threading.Event(), threading.Event()
    customer_ready, customer_done = threading.Event(), threading.Event()
    output_lock = threading.Lock()
    log_path = ROOT / ".local/device-qa/voice-devices.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    processes = []

    with log_path.open("w", encoding="utf-8") as log:

        def output(role, message):
            with output_lock:
                log.write(f"[{role}] {message}\n")
                log.flush()
                if any(
                    marker in message
                    for marker in [
                        "QA CALL listener",
                        "QA CALL incoming call",
                        "QA CALL answer",
                        "QA CALL peer state",
                        "QA CALL received",
                        "QA AUDIO",
                        "QA BROWSER",
                        "QA HANGUP",
                        "All tests passed",
                        "failed",
                        "TestFailure",
                        "permission",
                        "Call failed",
                    ]
                ):
                    print(f"[{role}] {message}", flush=True)

        def launch(role, app, device):
            process = subprocess.Popen(
                [
                    FLUTTER,
                    "test",
                    "integration_test/voice_call_test.dart",
                    "-d",
                    device,
                    f"--dart-define-from-file=../../.secrets/device-call-{role}.json",
                ],
                cwd=ROOT / "apps" / app,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            processes.append(process)

            def consume():
                for line in process.stdout:
                    message = line.rstrip()
                    output(role, message)
                    if role == "pilot" and "QA CALL listener started" in message:
                        ready.set()
                    if role == "customer" and "QA CALL listener started" in message:
                        customer_ready.set()
                    if role == "customer" and (
                        "tearDownAll" in message
                        or "tests passed" in message
                        or "tests failed" in message
                    ):
                        customer_done.set()

            threading.Thread(target=consume, daemon=True).start()
            return process

        def microphone_prompts():
            allowed = set()
            while not stop.is_set():
                for device in [] if BROWSER_PEER else [PHONE]:
                    prefix = [ADB, "-s", device, "shell"]
                    try:
                        dump = subprocess.run(
                            prefix + ["uiautomator", "dump", "/sdcard/quickbuddy-call-qa.xml"],
                            capture_output=True,
                            timeout=8,
                        )
                        if dump.returncode != 0 or b"dumped to:" not in dump.stdout:
                            continue
                        result = subprocess.run(
                            prefix + ["cat", "/sdcard/quickbuddy-call-qa.xml"],
                            capture_output=True,
                            timeout=5,
                        )
                        tree = ET.fromstring(result.stdout)
                        words = " ".join(node.get("text", "") for node in tree.iter("node")).lower()
                        if "quickbuddy" not in words:
                            continue
                        kind = (
                            "microphone"
                            if ("record audio" in words or "microphone" in words)
                            else "notifications"
                            if "notifications" in words
                            else None
                        )
                        if kind is None or (device, kind) in allowed:
                            continue
                        suffix = (
                            "permission_allow_foreground_only_button"
                            if kind == "microphone"
                            else "permission_allow_button"
                        )
                        for node in tree.iter("node"):
                            if node.get("resource-id", "").endswith(suffix):
                                x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.get("bounds")))
                                subprocess.run(
                                    prefix
                                    + ["input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2)],
                                    check=True,
                                    timeout=5,
                                )
                                allowed.add((device, kind))
                                output(device, f"Call {kind} permission accepted")
                    except (subprocess.SubprocessError, ET.ParseError, ValueError):
                        pass
                stop.wait(1)

        def keep_test_foreground():
            while not stop.wait(3):
                if BROWSER_PEER or not customer_ready.is_set() or customer_done.is_set():
                    continue
                try:
                    alive = subprocess.run(
                        [ADB, "-s", PHONE, "shell", "pidof", "com.quickbuddy.customer_app"],
                        capture_output=True,
                        timeout=5,
                    )
                    if alive.returncode != 0:
                        continue
                    state = subprocess.run(
                        [ADB, "-s", PHONE, "shell", "dumpsys", "activity", "activities"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    current = [
                        line.lower()
                        for line in state.stdout.splitlines()
                        if "resumedactivity" in line.lower()
                    ]
                    text = " ".join(current)
                    if (
                        "com.quickbuddy.customer_app" in text
                        or "permissioncontroller" in text
                        or "incall" in text
                        or "voip" in text
                    ):
                        continue
                    subprocess.run(
                        [
                            ADB,
                            "-s",
                            PHONE,
                            "shell",
                            "am",
                            "start",
                            "--activity-reorder-to-front",
                            "-n",
                            "com.quickbuddy.customer_app/.MainActivity",
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                except subprocess.SubprocessError:
                    pass

        threading.Thread(target=microphone_prompts, daemon=True).start()
        threading.Thread(target=keep_test_foreground, daemon=True).start()
        try:
            pilot = launch("pilot", "pilot_app", EMULATOR)
            deadline = time.monotonic() + 240
            while not ready.wait(1):
                if pilot.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Pilot did not reach the calling listener")
            subprocess.run(
                [
                    ADB,
                    "-s",
                    EMULATOR,
                    "shell",
                    "pm",
                    "grant",
                    "com.quickbuddy.pilot_app",
                    "android.permission.RECORD_AUDIO",
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    ADB,
                    "-s",
                    EMULATOR,
                    "shell",
                    "pm",
                    "grant",
                    "com.quickbuddy.pilot_app",
                    "android.permission.POST_NOTIFICATIONS",
                ],
                check=True,
                capture_output=True,
            )
            output("pilot", "Call permissions ready before ringing")
            if BROWSER_PEER:
                browser = subprocess.Popen(
                    ["node", "tools/qa_voice_browser.cjs"],
                    cwd=ROOT,
                    env=environment,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                processes.append(browser)

                def consume_browser():
                    for line in browser.stdout:
                        output("browser", line.rstrip())

                threading.Thread(target=consume_browser, daemon=True).start()
                (ROOT / ".local/calling-qa/go").touch()
            else:
                launch("customer", "customer_app", PHONE)
            while any(process.poll() is None for process in processes):
                if time.monotonic() > deadline + 300:
                    raise RuntimeError("Device calling test timed out")
                stop.wait(1)
            if any(process.returncode != 0 for process in processes):
                raise RuntimeError(f"Device calling failed; inspect {log_path}")
            print("Both call peers passed.", flush=True)
        finally:
            stop.set()
            for process in processes:
                if process.poll() is None:
                    process.terminate()


if __name__ == "__main__":
    main()
