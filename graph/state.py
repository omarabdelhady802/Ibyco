from typing import TypedDict, List, Dict, Optional, Any


class AgentState(TypedDict):
    client: Optional[Any]                        # Client model object passed from the request
    current_message: str
    intent: Optional[str]                        # browse | filter | details | installment | booking | greeting | other
    product_type: Optional[str]                  # motorcycle | scooter | helmet | None
    filters: Dict[str, Any]                      # extracted filters from user message
    vehicles: List[Dict[str, Any]]               # fetched vehicle/product records (as raw dicts)
    lead: Dict[str, Any]                         # lead info: name, phone
    booking_stage: Optional[str]                 # None | collecting_info | confirmed
    response: Optional[str]                      # final response to send back
    recommendations: List[str]                   # suggested follow-up questions
    complaint_saved: Optional[bool]              # True if complaint was persisted to DB
    booking_saved: Optional[bool]                # True if booking was persisted to DB
    ask_clarification: Optional[str]             # "down_payment" | "vehicle_name" | None — ask user for missing info
    total_count: Optional[int]                   # total matching vehicles in DB (so response knows if there are more)
    other_types_hint: Optional[Dict[str, int]]   # other available product types when current type has no more results
    intent_usage: Optional[Dict[str, int]]       # token counts from intent_node LLM call
    usage: Optional[Dict[str, int]]              # token counts from response_node LLM call
