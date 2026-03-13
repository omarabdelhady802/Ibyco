# -*- coding: utf-8 -*-
"""
Simulates WhatsApp messages hitting /api/chat exactly as the integration
layer would — sending a full client object and managing conversation_history
between turns.

Usage:
    python tests/test_whatsapp_sim.py
    python tests/test_whatsapp_sim.py --json       # show raw response
    python tests/test_whatsapp_sim.py --client 3   # use a real DB client id
"""
import sys
import json
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app import app

app.config["TESTING"] = True
flask_client = app.test_client()

# ── colours ───────────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"
def _c(t, *codes): return "".join(codes) + str(t) + RESET


# ── WhatsApp-style conversation ───────────────────────────────────────────────

def send(message: str, client_obj: dict | None, lead: dict | None = None) -> dict:
    payload = {
        "client":  client_obj,
        "message": message,
        "lead":    lead or {},
    }
    r = flask_client.post("/api/chat", json=payload)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.data.decode()}"
    return r.get_json()


def run(client_id: int | None = None, show_json: bool = False):
    """
    Simulates one WhatsApp user sending several messages in sequence.
    client_id=None  → anonymous (no client row needed).
    client_id=<int> → pass a real DB id to test full DB writes.
    """
    client_obj = {"id": client_id} if client_id else None
    lead: dict = {}

    CONVERSATION = [
        # 1. Greeting
        "اهلاً عندكم ايه؟",
        # 2. Browse motorcycles
        "عندكم إيه من موتوسيكلات؟",
        # 3. Ask about specific model price
        "كلمني عن الـ Jet X — سعره كام؟",
        # 4. Ask installment
        "ممكن اعرف نظام تقسيطه؟",
        # 5. Provide down payment
        "هدفع مقدم 25000 جنيه",
        # 6. Start booking — no details yet
        "عايز أحجز موعد لأجرب الموتور",
        # 7. Provide name + phone
        "اسمي محمد وتليفوني 01012345678",
        # 8. Provide date → booking should save now
        "هيجي يوم السبت",
        # 9. Complaint about a previous product
        "عندي شكوى — اشتريت موتور من عندكم من شهر وبدأ يعمل صوت غريب في الموتور",
    ]

    print()
    print(_c("═" * 65, CYAN, BOLD))
    print(_c("  WhatsApp Simulation", CYAN, BOLD))
    client_label = f"client_id={client_id}" if client_id else "anonymous (no client)"
    print(_c(f"  {client_label}", DIM))
    print(_c("═" * 65, CYAN, BOLD))

    for i, msg in enumerate(CONVERSATION, 1):
        print()
        print(_c(f"  [{i}] USER ▶ {msg}", BOLD))

        body = send(msg, client_obj, lead)

        intent          = body.get("intent") or "—"
        response_text   = body.get("response", "")
        booking_saved   = body.get("booking_saved")
        complaint_saved = body.get("complaint_saved")
        usage           = body.get("usage") or {}
        returned_client = body.get("client")

        # Carry lead and fresh client data to next turn
        lead = body.get("lead") or {}
        if returned_client:
            client_obj = returned_client

        # Print
        intent_colour = GREEN if intent not in ("other", None, "—") else YELLOW
        print(_c(f"       INTENT   : {intent}", intent_colour))

        if booking_saved:
            print(_c("       BOOKING  : saved to DB", GREEN, BOLD))
        if complaint_saved:
            print(_c("       COMPLAINT: saved to DB", GREEN, BOLD))

        tok = usage.get("total_all_tokens") or (
            usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        )
        cost = usage.get("cost_usd", 0)
        print(_c(f"       TOKENS   : {tok}  |  cost ${cost:.5f}", CYAN))

        print(_c("       BOT ▶", BOLD, GREEN))
        for line in response_text.splitlines():
            print(f"         {line}")

        if show_json:
            print(_c("\n  [RAW JSON]", DIM))
            for line in json.dumps(body, ensure_ascii=False, indent=2).splitlines():
                print(_c("  ", DIM) + line)

    print()
    print(_c("═" * 65, CYAN))
    print(_c(f"  Done — {len(CONVERSATION)} messages sent", CYAN))
    print(_c("═" * 65, CYAN))
    print()


if __name__ == "__main__":
    show_json = "--json" in sys.argv
    client_id = None
    if "--client" in sys.argv:
        idx = sys.argv.index("--client")
        if idx + 1 < len(sys.argv):
            client_id = int(sys.argv[idx + 1])

    run(client_id=client_id, show_json=show_json)
