from dataclasses import dataclass
from typing import Any, Optional


def _serialize_client(client) -> Optional[dict]:
    if not client:
        return None
    return {
        "id":                   client.id,
        "phone_number":         client.phone_number,
        "chat_summary":         client.chat_summary,
        "last_user_reply":      client.last_user_reply,
        "last_bot_reply":       client.last_bot_reply,
        "last_bot_reply_type":  client.last_bot_reply_type,
        "info":                 client.info,
        "has_purchased":        client.has_purchased,
        "is_active":            client.is_active,
    }


@dataclass
class AgentResponse:
    response: str
    intent: Optional[str]
    vehicles: list
    conversation_history: list
    booking_saved: Optional[Any]
    complaint_saved: Optional[Any]
    usage: dict
    client: Optional[dict]

    @staticmethod
    def from_result(result: dict) -> "AgentResponse":
        return AgentResponse(
            response=result.get("response") or "",
            intent=result.get("intent"),
            vehicles=result.get("vehicles") or [],
            conversation_history=result.get("conversation_history") or [],
            booking_saved=result.get("booking_saved"),
            complaint_saved=result.get("complaint_saved"),
            usage=result.get("usage") or {},
            client=_serialize_client(result.get("client")),
        )

    def to_dict(self) -> dict:
        return {
            "response":             self.response,
            "intent":               self.intent,
            "vehicles":             self.vehicles,
            "conversation_history": self.conversation_history,
            "booking_saved":        self.booking_saved,
            "complaint_saved":      self.complaint_saved,
            "usage":                self.usage,
            "client":               self.client,
        }
