from typing import Dict
from botbuilder.core import TurnContext
from botbuilder.schema import ConversationReference

conversation_refs: Dict[str, ConversationReference] = {}

def upsert_conversation_reference(turn_context: TurnContext) -> str:
    ref = TurnContext.get_conversation_reference(turn_context.activity)
    user_id = (turn_context.activity.from_property and turn_context.activity.from_property.id) or "user"
    conversation_refs[user_id] = ref
    return user_id
