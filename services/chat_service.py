from graph.agent_graph import get_agent

# In-memory session store: user_id → AgentState
_chat_sessions = {}


def _get_or_create_session(user_id: str) -> dict:
    if user_id not in _chat_sessions:
        _chat_sessions[user_id] = {
            "user_id": user_id,
            "current_message": "",
            "conversation_history": [],
            "intent": None,
            "filters": {},
            "vehicles": [],
            "lead": {},
            "booking_stage": None,
            "response": None,
            "recommendations": [],
            "complaint_saved": None,
            "booking_saved": None,
            "ask_clarification": None,
            "intent_usage": None,
            "usage": None,
        }
    return _chat_sessions[user_id]


def chat(user_id: str, message: str) -> dict:
    """Run the agent and return the result."""
    session = _get_or_create_session(user_id)
    session["current_message"] = message

    agent = get_agent()
    result = agent.invoke(session)

    _chat_sessions[user_id] = result

    return {
        "response": result.get("response", ""),
        "intent": result.get("intent"),
        "vehicles": result.get("vehicles", []),
        "usage": result.get("usage") or {},
    }


def reset_session(user_id: str):
    """Clear conversation history for a user."""
    _chat_sessions.pop(user_id, None)
