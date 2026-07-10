import re
try:
    from transformers import pipeline
    _bot=pipeline("text2text-generation",model="google/flan-t5-small")
except Exception:
    _bot=None

FAQ={
"hello":"Hello! How can I help you today?",
"hours":"We are open from 9 AM to 6 PM.",
"refund":"Refunds are processed within 5-7 business days."
}

def get_response(message:str)->str:
    text=message.lower().strip()
    for k,v in FAQ.items():
        if k in text:
            return v
    if _bot:
        try:
            out=_bot(f"Answer briefly: {message}",max_new_tokens=60)
            return out[0]["generated_text"]
        except Exception:
            pass
    return "Sorry, I don't know that yet. Please contact support."
