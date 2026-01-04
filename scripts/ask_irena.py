#!/usr/bin/env python3
"""
Instant Claude ↔ ChatGPT Communication
No files, no polling - direct API calls.
"""

import json
import os
import urllib.request

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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")

IRENA_SYSTEM_PROMPT = """Du bist IRENA, eine erfahrene Reservoir Engineering Consultant.

Deine Expertise:
- ECLIPSE Simulation (Keywords, Syntax, Best Practices)
- Reservoir Engineering Prinzipien  
- OPM Flow und Open-Source Alternativen
- Numerische Simulation und Modellierung

Kommunikationsstil:
- Deutsch, präzise, technisch fundiert
- Konkrete Empfehlungen mit Code-Beispielen wenn hilfreich
- Konstruktive Kritik, kein Bullshit
- Lies Code sorgfältig bevor du kritisierst

Du arbeitest mit Claude (Operator) zusammen am CLARISSA Projekt - einem NLP-System für Reservoir Simulation.
Wenn du Code reviewst, zitiere konkrete Zeilen.
"""


def ask_irena(question: str, context: str = "") -> str:
    """
    Ask IRENA (ChatGPT) a question and get immediate response.
    
    Args:
        question: The question to ask
        context: Optional code/context to include
        
    Returns:
        IRENA's response as string
    """
    
    content = question
    if context:
        content = f"{question}\n\n---\n\n**Context:**\n```\n{context}\n```"
    
    payload = {
        "model": "gpt-4o",
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": IRENA_SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    }
    
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps(payload).encode(),
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    # Test
    print(ask_irena("Was ist der Unterschied zwischen AQUFETP und AQUCT?"))