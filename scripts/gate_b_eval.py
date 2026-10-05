"""
KisanMitra — scripts/gate_b_eval.py
Gate B Language Quality Evaluation Script (T-17).
Evaluates 5 Marathi and 5 Hindi responses against RULES.md §5.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from backend.handler import process_chat_request
from backend.schemas import AnswerCard

QUESTIONS_MR = [
    "आता रब्बी हंगामात कोणते पीक घ्यावे?",
    "नाशिक बाजारात कांद्याला आज काय भाव आहे?",
    "आज शेतात कीटकनाशक फवारणी करावी का?",
    "रब्बी कांदा लागवड कशी करावी?",
    "शेतात ट्रॅक्टर खरेदीसाठी कर्ज कसे मिळेल?"
]

QUESTIONS_HI = [
    "अभी रबी के मौसम में कौन सी फसल लगाएं?",
    "नासिक मंडी में आज प्याज का क्या भाव है?",
    "क्या आज खेत में कीटनाशक छिड़काव कर सकते हैं?",
    "रबी प्याज की खेती कैसे करें?",
    "ट्रैक्टर खरीदने के लिए लोन कैसे मिलेगा?"
]

def evaluate_responses():
    results = {"mr": [], "hi": []}

    print("=== GATE B EVALUATION: MARATHI (5 SAMPLES) ===")
    mr_pass = 0
    for q in QUESTIONS_MR:
        res = process_chat_request({"text": q, "language": "mr", "district": "nashik"})
        title = res.get("title", "")
        summary = res.get("summary_lines", [])
        steps = res.get("steps", [])
        speak = res.get("speak_text", "")
        lang = res.get("language", "")

        # Verification rules
        checks = {
            "lang_match": lang == "mr",
            "max_summary": len(summary) <= 3,
            "max_steps": len(steps) <= 3,
            "speak_present": bool(speak),
            "no_english_script_in_speak": not any(c.isascii() and c.isalpha() for c in speak.replace("MPKV", "").replace("KVK", ""))
        }
        passed = all(checks.values())
        if passed: mr_pass += 1

        print(f"\nQ: {q}")
        print(f"Title: {title}")
        print(f"Summary: {summary}")
        print(f"Speak: {speak}")
        print(f"Checks: {checks} -> {'PASS' if passed else 'FAIL'}")
        results["mr"].append({"q": q, "passed": passed, "card": res})

    print("\n=== GATE B EVALUATION: HINDI (5 SAMPLES) ===")
    hi_pass = 0
    for q in QUESTIONS_HI:
        res = process_chat_request({"text": q, "language": "hi", "district": "nashik"})
        title = res.get("title", "")
        summary = res.get("summary_lines", [])
        steps = res.get("steps", [])
        speak = res.get("speak_text", "")
        lang = res.get("language", "")

        checks = {
            "lang_match": lang == "hi",
            "max_summary": len(summary) <= 3,
            "max_steps": len(steps) <= 3,
            "speak_present": bool(speak),
            "no_english_script_in_speak": not any(c.isascii() and c.isalpha() for c in speak.replace("MPKV", "").replace("KVK", ""))
        }
        passed = all(checks.values())
        if passed: hi_pass += 1

        print(f"\nQ: {q}")
        print(f"Title: {title}")
        print(f"Summary: {summary}")
        print(f"Speak: {speak}")
        print(f"Checks: {checks} -> {'PASS' if passed else 'FAIL'}")
        results["hi"].append({"q": q, "passed": passed, "card": res})

    print(f"\nGate B Result: Marathi {mr_pass}/5, Hindi {hi_pass}/5")
    return mr_pass == 5 and hi_pass == 5

if __name__ == "__main__":
    success = evaluate_responses()
    exit(0 if success else 1)
