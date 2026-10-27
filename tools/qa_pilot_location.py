"""Physical pilot QA with foreground-only permission handling for Quickbuddy."""

import os
import re
import subprocess
import threading
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    adb = str(Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk/platform-tools/adb.exe")
    devices = subprocess.check_output([adb, "devices"], text=True)
    phones = [
        line.split()[0]
        for line in devices.splitlines()
        if line.endswith("\tdevice") and not line.startswith("emulator-")
    ]
    phone = os.environ.get("QA_ANDROID_DEVICE") or (phones[0] if len(phones) == 1 else None)
    if phone is None:
        raise SystemExit("Connect one physical Android phone or set QA_ANDROID_DEVICE")
    stop = threading.Event()

    def permission_prompt():
        while not stop.wait(1):
            try:
                dump = subprocess.run(
                    [
                        adb,
                        "-s",
                        phone,
                        "shell",
                        "uiautomator",
                        "dump",
                        "/sdcard/quickbuddy-qa-permission.xml",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                if "dumped to:" not in dump.stdout:
                    continue
                xml = subprocess.check_output(
                    [adb, "-s", phone, "shell", "cat", "/sdcard/quickbuddy-qa-permission.xml"],
                    text=True,
                    timeout=5,
                )
                if "permissioncontroller" not in xml or "Quickbuddy Pilot" not in xml:
                    continue
                node = next(
                    (
                        n
                        for n in ET.fromstring(xml).iter("node")
                        if n.get("resource-id", "").endswith(
                            "/permission_allow_foreground_only_button"
                        )
                    ),
                    None,
                )
                if node is None:
                    continue
                bounds = list(map(int, re.findall(r"\d+", node.get("bounds", ""))))
                if len(bounds) == 4:
                    subprocess.run(
                        [
                            adb,
                            "-s",
                            phone,
                            "shell",
                            "input",
                            "tap",
                            str((bounds[0] + bounds[2]) // 2),
                            str((bounds[1] + bounds[3]) // 2),
                        ],
                        capture_output=True,
                        timeout=5,
                    )
                    print("QA accepted foreground-only Quickbuddy location prompt", flush=True)
            except (subprocess.SubprocessError, ET.ParseError):
                pass

    threading.Thread(target=permission_prompt, daemon=True).start()
    environment = {**os.environ, "TEMP": "C:/tmp/quickbuddy-java", "TMP": "C:/tmp/quickbuddy-java"}
    target = root / ".local/qa-pilot-location-device-final.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [
                    os.environ.get("FLUTTER_QA_BIN", "C:/tools/flutter/bin/flutter.bat"),
                    "test",
                    "integration_test/availability_test.dart",
                    "-d",
                    phone,
                    "--dart-define-from-file=../../.secrets/device-audit-pilot.json",
                ],
                cwd=root / "apps/pilot_app",
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in process.stdout:
                log.write(line)
                log.flush()
                if "QA " in line or "tests passed" in line or "tests failed" in line:
                    print(line.rstrip(), flush=True)
            return process.wait()
    finally:
        stop.set()


if __name__ == "__main__":
    raise SystemExit(main())
