# -*- coding: utf-8 -*-
"""
Interactive CLI chat — type messages and get live replies.

Usage:
    python tests/chat_cli.py
    python tests/chat_cli.py --client 1   # use a real DB client
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import app

app.config["TESTING"] = True
flask_client = app.test_client()

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
DIM    = "\033[2m"
def _c(t, *codes): return "".join(codes) + str(t) + RESET


def send(message: str, client_obj: dict | None, lead: dict | None = None) -> dict:
    r = flask_client.post("/api/chat", json={"client": client_obj, "message": message, "lead": lead or {}})
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.data.decode()}"
    return r.get_json()


def run(client_id: int | None = None):
    client_obj = {"id": client_id} if client_id else None
    lead: dict = {}

    print()
    print(_c("═" * 60, CYAN, BOLD))
    print(_c("  ibyco chat  |  type 'exit' to quit", CYAN, BOLD))
    label = f"client_id={client_id}" if client_id else "anonymous"
    print(_c(f"  {label}", DIM))
    print(_c("═" * 60, CYAN, BOLD))
    print()

    while True:
        try:
            msg = input(_c("YOU  ▶ ", BOLD)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break

        if not msg:
            continue
        if msg.lower() in ("exit", "quit", "bye"):
            print("bye!")
            break

        body = send(msg, client_obj, lead)

        response_text   = body.get("response", "")
        intent          = body.get("intent") or "—"
        booking_saved   = body.get("booking_saved")
        complaint_saved = body.get("complaint_saved")
        returned_client = body.get("client")
        usage           = body.get("usage") or {}

        # Carry lead and fresh client to next turn
        lead = body.get("lead") or {}
        if returned_client:
            client_obj = returned_client

        print()
        print(_c("BOT  ▶ ", BOLD, GREEN) + response_text)
        tok = usage.get("total_all_tokens") or (
            usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        )
        info = f"[{intent}]  tokens={tok}"
        if booking_saved:
            info += "  BOOKING saved"
        if complaint_saved:
            info += "  COMPLAINT saved"
        print(_c(f"       {info}", DIM))
        print()


if __name__ == "__main__":
    client_id = None
    if "--client" in sys.argv:
        idx = sys.argv.index("--client")
        if idx + 1 < len(sys.argv):
            client_id = int(sys.argv[idx + 1])
    run(client_id=client_id)
