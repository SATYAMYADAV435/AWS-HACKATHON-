"""
KisanMitra — scripts/voice_test_set_eval.py
Runs the full 10-question x 3-language voice test set (T-26).
Saves golden responses and records hit/miss evaluation.
"""

import os
import sys
import json
from pathlib import Path

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.handler import process_chat_request
from backend.schemas import AnswerCard

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_SET_FILE = BASE_DIR / "data" / "voice_test_set.json"
GOLDEN_DIR = BASE_DIR / "fallback" / "golden_responses"

def run_evaluation():
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    with open(TEST_SET_FILE, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    langs = ["mr", "hi", "en"]
    results = {"mr": {"hits": 0, "total": 0}, "hi": {"hits": 0, "total": 0}, "en": {"hits": 0, "total": 0}}
    misses = []

    print(f"=== RUNNING VOICE TEST SET EVALUATION ({len(test_cases)} questions x 3 languages) ===")

    for tc in test_cases:
        qid = tc["id"]
        expected_intent = tc["intent"]

        for lang in langs:
            query = tc[lang]
            results[lang]["total"] += 1

            payload = {
                "text": query,
                "language": lang,
                "district": "nashik"
            }
            try:
                res = process_chat_request(payload)
                card = AnswerCard(**res)

                # Validation checks
                checks = {
                    "lang_match": card.language == lang,
                    "summary_len": len(card.summary_lines) <= 3,
                    "steps_len": len(card.steps) <= 3,
                    "speak_text": bool(card.speak_text),
                    "script_lock": True if lang == "en" else not any(c.isascii() and c.isalpha() for c in card.speak_text.replace("MPKV", "").replace("KVK", ""))
                }

                passed = all(checks.values())
                if passed:
                    results[lang]["hits"] += 1
                    # Save golden response
                    golden_file = GOLDEN_DIR / f"{qid}_{lang}.json"
                    with open(golden_file, "w", encoding="utf-8") as gf:
                        json.dump(card.model_dump(), gf, ensure_ascii=False, indent=2)
                else:
                    misses.append({"qid": qid, "lang": lang, "query": query, "checks": checks})

                status_mark = "PASS" if passed else "FAIL"
                print(f"[{status_mark}] {qid} ({lang}): {card.title}")
            except Exception as e:
                misses.append({"qid": qid, "lang": lang, "query": query, "error": str(e)})
                print(f"[ERROR] {qid} ({lang}): {e}")

    print("\n=== EVALUATION SUMMARY ===")
    overall_hits = 0
    overall_total = 0
    for l in langs:
        h = results[l]["hits"]
        t = results[l]["total"]
        overall_hits += h
        overall_total += t
        pct = (h / t) * 100 if t else 0
        print(f"Language: {l.upper()} -> {h}/{t} hits ({pct:.1f}%)")

    total_pct = (overall_hits / overall_total) * 100 if overall_total else 0
    print(f"Overall Score: {overall_hits}/{overall_total} ({total_pct:.1f}%)")

    if misses:
        print(f"\nMisses ({len(misses)}):")
        for m in misses:
            print(m)
    else:
        print("\nAll 30 tests passed with 100% hits and zero misses!")

    return overall_hits == overall_total

if __name__ == "__main__":
    success = run_evaluation()
    exit(0 if success else 1)
