import json


def build_kb_qa_prompt(user_msg, knowledge_base):
    """Build a grounded prompt so answers come only from the local knowledge base."""
    kb_text = json.dumps(knowledge_base, indent=2)

    return (
        "You are AutoStream's sales assistant. "
        "Answer using ONLY the knowledge base below.\n\n"
        "Rules:\n"
        "1. Do not invent facts or features.\n"
        "2. If the answer is not present in the knowledge base, say: "
        "'I do not have that information in the current knowledge base.'\n"
        "3. Keep answers concise and sales-friendly.\n"
        "4. Use simple bullet points when useful.\n\n"
        f"Knowledge Base:\n{kb_text}\n\n"
        f"User Question: {user_msg}\n\n"
        "Final Answer:"
    )


def build_rephrase_prompt(user_msg, factual_answer):
    """Rephrase a factual draft without changing meaning or adding facts."""
    return (
        "You are a response rewriter for AutoStream.\n"
        "Rewrite the DRAFT ANSWER to sound clear, friendly, and concise.\n\n"
        "Strict rules:\n"
        "1. Do not add any new facts, numbers, policies, or features.\n"
        "2. Keep all original facts exactly the same.\n"
        "3. If DRAFT ANSWER says information is unavailable, keep that meaning unchanged.\n"
        "4. Output only the final rewritten answer text.\n\n"
        f"User Question: {user_msg}\n"
        f"DRAFT ANSWER: {factual_answer}\n\n"
        "Rewritten Answer:"
    )
