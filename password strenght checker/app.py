"""
Password Strength Checker — Flask backend.

Scores a password on length, character variety, entropy, and common
patterns (dictionary words, sequences, repeats), then returns a
verdict of Weak / Moderate / Good / Strong plus actionable feedback.
"""

import math
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# A small seed list of very common passwords / words. Not exhaustive —
# just enough to catch the obvious offenders and demonstrate the check.
COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty", "abc123", "letmein",
    "monkey", "dragon", "football", "iloveyou", "admin", "welcome",
    "login", "princess", "solo", "master", "sunshine", "passw0rd",
    "trustno1", "starwars", "hello", "freedom", "whatever", "qazwsx",
    "123123", "000000", "111111", "password1", "1234567", "12345678",
    "michael", "shadow", "superman", "batman", "michelle", "jennifer",
}

SEQUENTIAL_RUNS = [
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
]


def find_sequential_run(password: str, min_run: int = 4) -> bool:
    """Detect ascending/descending runs like 'abcd' or '4321' or 'qwer'."""
    lowered = password.lower()
    for run in SEQUENTIAL_RUNS:
        for i in range(len(run) - min_run + 1):
            chunk = run[i:i + min_run]
            if chunk in lowered or chunk[::-1] in lowered:
                return True
    return False


def find_repeated_chars(password: str, min_run: int = 4) -> bool:
    """Detect a single character repeated min_run+ times, e.g. 'aaaa'."""
    return bool(re.search(r"(.)\1{" + str(min_run - 1) + ",}", password))


def calculate_entropy(password: str) -> float:
    """Rough Shannon-style entropy estimate in bits, based on pool size."""
    pool = 0
    if re.search(r"[a-z]", password):
        pool += 26
    if re.search(r"[A-Z]", password):
        pool += 26
    if re.search(r"[0-9]", password):
        pool += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        pool += 32
    if pool == 0:
        return 0.0
    return round(len(password) * math.log2(pool), 1)


def analyze_password(password: str) -> dict:
    if not password:
        return {
            "score": 0,
            "label": "Empty",
            "entropy": 0,
            "criteria": {
                "length": False,
                "uppercase": False,
                "lowercase": False,
                "number": False,
                "symbol": False,
            },
            "warnings": [],
            "suggestions": ["Start typing a password to see its strength."],
        }

    criteria = {
        "length": len(password) >= 8,
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "number": bool(re.search(r"[0-9]", password)),
        "symbol": bool(re.search(r"[^a-zA-Z0-9]", password)),
    }

    entropy = calculate_entropy(password)

    warnings = []
    is_common = password.lower() in COMMON_PASSWORDS
    if is_common:
        warnings.append("This is one of the most commonly used passwords.")

    has_seq = find_sequential_run(password)
    if has_seq:
        warnings.append("Contains an easy-to-guess sequence (e.g. 'abcd', '1234', 'qwerty').")

    has_repeat = find_repeated_chars(password)
    if has_repeat:
        warnings.append("Contains a character repeated many times in a row.")

    # --- Scoring: start from entropy, then apply bonuses/penalties -----
    score = entropy

    variety_count = sum(criteria[k] for k in ("uppercase", "lowercase", "number", "symbol"))
    score += variety_count * 4  # reward mixing character classes

    if len(password) >= 12:
        score += 8
    if len(password) >= 16:
        score += 8
    if len(password) < 8:
        score -= 20

    if is_common:
        score -= 45
    if has_seq:
        score -= 15
    if has_repeat:
        score -= 15

    score = max(0, min(100, round(score)))

    if is_common or score < 30:
        label = "Weak"
    elif score < 55:
        label = "Moderate"
    elif score < 80:
        label = "Good"
    else:
        label = "Strong"

    suggestions = []
    if not criteria["length"]:
        suggestions.append("Use at least 8 characters (12+ is even better).")
    if not criteria["uppercase"]:
        suggestions.append("Add an uppercase letter.")
    if not criteria["lowercase"]:
        suggestions.append("Add a lowercase letter.")
    if not criteria["number"]:
        suggestions.append("Add a number.")
    if not criteria["symbol"]:
        suggestions.append("Add a symbol, e.g. ! @ # $ %.")
    if is_common:
        suggestions.append("Avoid well-known passwords — pick something unique to you.")
    if has_seq:
        suggestions.append("Avoid keyboard or alphabetic sequences like '1234' or 'qwerty'.")
    if has_repeat:
        suggestions.append("Avoid repeating the same character many times.")
    if not suggestions:
        suggestions.append("Great work — this password looks solid.")

    return {
        "score": score,
        "label": label,
        "entropy": entropy,
        "criteria": criteria,
        "warnings": warnings,
        "suggestions": suggestions,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    # Cap length defensively; nobody needs to send megabytes of text.
    password = password[:256]
    return jsonify(analyze_password(password))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
