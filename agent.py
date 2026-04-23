import json
import re
from tools import valid_email, mock_lead_capture
from model import ask_llm
from prompt import build_rephrase_prompt

# -------------------------
# Conversation State Memory
# -------------------------
DEFAULT_STATE = {
    "lead_mode": False,
    "name": None,
    "email": None,
    "platform": None,
}

# -------------------------
# Load Knowledge Base
# -------------------------
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)


def draft_kb_answer(user_msg):
    msg = user_msg.lower()
    basic = kb["plans"]["basic"]
    pro = kb["plans"]["pro"]
    refund = kb["policies"]["refund"]
    support = kb["policies"]["support"]

    if any(x in msg for x in ["yearly", "annual", "year", "annually"]):
        return "I do not have that information in the current knowledge base."

    if any(x in msg for x in ["refund", "money back", "cancel"]):
        return f"Refund policy: {refund}."

    if any(x in msg for x in ["support", "help", "customer care"]):
        return f"Support policy: {support}."

    if any(x in msg for x in ["resolution", "quality", "4k", "720p"]):
        return (
            f"Basic supports {basic['resolution']} export. "
            f"Pro supports {pro['resolution']} export."
        )

    if any(x in msg for x in ["feature", "features", "caption", "captions"]):
        return (
            "Pro plan includes AI captions. "
            f"Basic includes {basic['videos']} with {basic['resolution']} export, "
            f"while Pro includes {pro['videos']} with {pro['resolution']} export."
        )

    if any(x in msg for x in ["video", "videos", "limit", "unlimited"]):
        return (
            f"Basic allows {basic['videos']}. "
            f"Pro allows {pro['videos']}."
        )

    if "basic" in msg and any(x in msg for x in ["price", "cost", "pricing"]):
        return f"Basic plan price is {basic['price']} with {basic['videos']} and {basic['resolution']} export."

    if "pro" in msg and any(x in msg for x in ["price", "cost", "pricing"]):
        return (
            f"Pro plan price is {pro['price']} with {pro['videos']}, "
            f"{pro['resolution']} export, and {pro['feature']}."
        )

    if any(x in msg for x in ["price", "pricing", "cost", "plan", "plans", "subscription"]):
        return (
            f"Basic: {basic['price']} ({basic['videos']}, {basic['resolution']} export). " 
            f"Pro: {pro['price']} ({pro['videos']}, {pro['resolution']} export, {pro['feature']})."
        )

    return "I do not have that information in the current knowledge base."


def draft_pro_subscription_answer():
    pro = kb["plans"]["pro"]
    support = kb["policies"]["support"]
    return (
        "Pro subscription details: "
        f"Price is {pro['price']}. "
        f"It includes {pro['videos']}, {pro['resolution']} export, and {pro['feature']}. "
        f"Support: {support}. "
        "If you want, I can help you start Pro signup now."
    )


# -------------------------
# Intent Detection
# -------------------------
def detect_intent(msg):
    msg = msg.lower().strip()

    if re.search(r"\b(pro subscription|pro plan|want pro|subscribe pro|upgrade)\b", msg):
        return "pro_subscription"

    if re.search(r"\b(price|pricing|plan|subscription|cost)\b", msg):
        return "pricing"

    if re.search(r"\b(buy|signup|sign\s+up|purchase|interested|trial)\b", msg) or "want pro" in msg:
        return "lead"

    if re.search(r"\b(hi|hello|hey|good morning|good evening)\b", msg):
        return "greeting"

    return "general"


# -------------------------
# Pricing Response (RAG)
# -------------------------
def kb_answer(user_msg):
    factual_answer = draft_kb_answer(user_msg)
    prompt = build_rephrase_prompt(user_msg, factual_answer)
    llm_answer = ask_llm(prompt)

    if (
        "temporarily unavailable" in llm_answer.lower()
        or "missing" in llm_answer.lower()
        or "quota" in llm_answer.lower()
    ):
        return factual_answer

    return llm_answer


def kb_rephrase_only(user_msg, factual_answer):
    prompt = build_rephrase_prompt(user_msg, factual_answer)
    llm_answer = ask_llm(prompt)

    if (
        "temporarily unavailable" in llm_answer.lower()
        or "missing" in llm_answer.lower()
        or "quota" in llm_answer.lower()
    ):
        return factual_answer

    return llm_answer


# -------------------------
# Main Agent Function
# -------------------------
def run_agent(user_msg, state=None):
    if state is None:
        state = DEFAULT_STATE.copy()

    user_msg = user_msg.strip()

    # -------------------------
    # Lead Capture Flow
    # -------------------------
    if state["lead_mode"]:

        if not state["name"]:
            state["name"] = user_msg
            return "Great! Please share your email address."

        elif not state["email"]:
            if not valid_email(user_msg):
                return "Please enter a valid email address."

            state["email"] = user_msg
            return "Which creator platform do you use? (YouTube / Instagram / TikTok)"

        elif not state["platform"]:
            state["platform"] = user_msg

            mock_lead_capture(
                state["name"],
                state["email"],
                state["platform"]
            )

            user_name = state["name"]

            # Reset State
            state.update(DEFAULT_STATE)

            return f"""
Lead captured successfully for {user_name}.

Our sales team will contact you shortly.
Thank you for choosing AutoStream.
"""

    # -------------------------
    # Detect Intent
    # -------------------------
    intent = detect_intent(user_msg)

    # -------------------------
    # Pro Subscription Intent
    # -------------------------
    if intent == "pro_subscription":
        return kb_rephrase_only(user_msg, draft_pro_subscription_answer())

    # -------------------------
    # Pricing Intent
    # -------------------------
    elif intent == "pricing":
        return kb_answer(user_msg)

    # -------------------------
    # Lead Intent
    # -------------------------
    elif intent == "lead":
        state["lead_mode"] = True
        return """
Awesome choice.

To help you get started with AutoStream Pro,
please share your full name.
"""

    # -------------------------
    # Greeting Intent
    # -------------------------
    elif intent == "greeting":
        return """
Hello! Welcome to AutoStream!

I can help you with:

Pricing Plans  
Features  
Pro Subscription  

"""

    # -------------------------
    # General Intent (KB-grounded Gemini)
    # -------------------------
    else:
        return kb_answer(user_msg)