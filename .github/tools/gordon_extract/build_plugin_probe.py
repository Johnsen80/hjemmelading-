from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_ROOT = REPO_ROOT / ".github" / "tmp" / "gordon_plugin_probe"
PYTHON_EXE = REPO_ROOT / ".github" / ".tool-venv" / "Scripts" / "python.exe"


MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<GordonsReloadingTool>
  <plugin
    name="Hjemmelading Gordon Probe"
    id="com.grt.plugin.hjemmeladingprobe"
    version="0.1.0"
    provider="Hjemmelading"
    description="Temporary IPC probe for Gordon data extraction"
    launch-windows="plugin.cmd"
    launch-linux="plugin.py"
    launch-type="permanent"
    launch-args="{PLUGIN_COMMANDLINE}"
    start-timeout="3.0"
    enabled="true"
  >
    <registerevent>
      <event name="Attached" enabled="true" />
      <event name="TabSwitch" enabled="true" />
      <event name="TabComputed" enabled="true" />
      <event name="TabDataChange" enabled="true" />
      <event name="MenuAction" enabled="true" />
      <event name="ToolbarAction" enabled="true" />
      <event name="WindowActivate" enabled="true" />
    </registerevent>
    <menu autoenable="true">
      <menuitem id="dump_tablist" label="Dump TabList" enabled="true" checked="false" />
      <menuitem id="dump_tab_on_top" label="Dump Active Tab" enabled="true" checked="false" />
      <menuitem id="dump_tab_results" label="Dump Active Tab Results" enabled="true" checked="false" />
    </menu>
    <toolbar>
      <toolbaritem
        id="dump_tab_on_top"
        label="Dump active tab"
        tooltip="Probe active Gordon tab via IPC"
        enabled="true"
      />
    </toolbar>
  </plugin>
</GordonsReloadingTool>
"""


PLUGIN_SCRIPT = r"""from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "probe_log.jsonl"


def _log(payload: dict) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _send_json(sock: socket.socket, payload: dict) -> None:
    message = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    sock.sendall(message)


def _recv_line(sock: socket.socket, timeout: float = 2.0) -> str | None:
    sock.settimeout(timeout)
    chunks: list[bytes] = []
    try:
        while True:
            chunk = sock.recv(1)
            if not chunk:
                break
            if chunk == b"\n":
                break
            chunks.append(chunk)
    except Exception:
        return None
    if not chunks:
        return None
    return b"".join(chunks).decode("utf-8", errors="replace")


def _drain_socket(sock: socket.socket, duration_s: float = 3.0) -> list[str]:
    messages: list[str] = []
    end = time.time() + duration_s
    sock.settimeout(0.25)
    while time.time() < end:
        try:
            chunk = sock.recv(4096)
        except TimeoutError:
            continue
        except Exception as exc:
            _log({"event": "recv_error", "error": repr(exc), "ts": time.time()})
            break
        if not chunk:
            break
        text = chunk.decode("utf-8", errors="replace")
        messages.append(text)
        _log({"event": "raw_recv", "payload": text, "ts": time.time()})
    return messages


def _run_tcp_probe(port: int) -> int:
    with socket.create_connection(("127.0.0.1", port), timeout=3.0) as sock:
        _log({"event": "connected", "port": port, "ts": time.time()})
        _drain_socket(sock, duration_s=1.5)
        commands = [
            {"Get_TabList": {}},
            {"Get_TabOnTop": {}},
        ]
        for command in commands:
            _send_json(sock, command)
            _log({"event": "command_sent", "payload": command, "ts": time.time()})
            line = _recv_line(sock, timeout=4.0)
            if line is not None:
                _log({"event": "response", "payload": line, "ts": time.time()})
            _drain_socket(sock, duration_s=2.5)
        time.sleep(0.5)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipcport", type=int)
    parser.add_argument("--ipcfile")
    args, unknown = parser.parse_known_args()

    _log({"event": "startup", "argv": sys.argv, "unknown": unknown, "ts": time.time()})

    if args.ipcport:
        return _run_tcp_probe(args.ipcport)

    _log({"event": "no_supported_ipc", "ts": time.time()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


README = """# Hjemmelading Gordon Probe Plugin

Dette er en midlertidig plugin-probe for Gordon sin dokumenterte IPC/plugin-kanal.

Filer:
- `com.grt.plugin.xml`
- `plugin.py`

Bruk:
1. Kopier hele denne mappa inn i Gordon sin `plugins`-mappe.
2. Start Gordon.
3. Se etter `probe_log.jsonl` i samme mappe.

Mål:
- bekrefte IPC-tilkobling
- logge events
- prøve enkle `Get_TabList` / `Get_TabOnTop`-kall

Dette er ikke full database-ekstraksjon ennå. Det er første probe på plugin-sporet.
"""


WINDOWS_WRAPPER_TEMPLATE = """@echo off
"{python_exe}" "%~dp0plugin.py" %*
"""


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "com.grt.plugin.xml").write_text(MANIFEST_TEMPLATE, encoding="utf-8")
    (OUTPUT_ROOT / "plugin.py").write_text(PLUGIN_SCRIPT, encoding="utf-8")
    (OUTPUT_ROOT / "plugin.cmd").write_text(
        WINDOWS_WRAPPER_TEMPLATE.format(python_exe=str(PYTHON_EXE)),
        encoding="utf-8",
    )
    (OUTPUT_ROOT / "README.md").write_text(README, encoding="utf-8")
    print(OUTPUT_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
