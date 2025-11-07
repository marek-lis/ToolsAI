#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for
import json
import os
import html
import re

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
WEIGHTS_FILE = os.path.join(CONFIG_DIR, "weights.json")

# Domyślne wagi (char -> float)
DEFAULT_WEIGHTS = {
    "–": 3.0,  # półpauza
    "—": 4.0,  # pauza (ustawiona wyżej — silny wskaźnik)
    "“": 1.0, "”": 1.0,  # cudzysłowy angielskie
    "„": 1.0, "‟": 1.0,  # polskie
    "‘": 0.8, "’": 0.8, "‚": 0.8,  # pojedyncze
    "…": 1.5,  # wielokropek
    "\u00A0": 1.5,  # spacja niełamliwa
    "\u2009": 1.0,  # wąska spacja
    "\u202F": 1.0,  # wąska niełamliwa spacja
    "•": 0.7,  # punktor
    "→": 1.2,
    "←": 1.2,
}

# Opisy — zgodne z Twoimi komentarzami
CHAR_DESCRIPTIONS = {
    "–": "półpauza",
    "—": "pauza",
    "“": "cudzysłowy angielskie otwierające",
    "”": "cudzysłowy angielskie zamykające",
    "„": "polskie otwierające",
    "‟": "polskie zamykające",
    "‘": "pojedyncze otwierające",
    "’": "pojedyncze zamykające",
    "‚": "cudzysłów dolny",
    "…": "wielokropek",
    "\u00A0": "spacja niełamliwa",
    "\u2009": "wąska spacja",
    "\u202F": "wąska niełamliwa spacja",
    "•": "punktor / bullet",
    "→": "strzałka w prawo",
    "←": "strzałka w lewo",
}

def load_weights():
    # Zwraca dict char -> float
    try:
        if not os.path.exists(WEIGHTS_FILE):
            save_weights(DEFAULT_WEIGHTS)
            return DEFAULT_WEIGHTS.copy()
        with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # jeśli format starej wersji (char->{"w":..., "desc":...}) – obsłuż to
            if data and isinstance(next(iter(data.values())), dict):
                processed = {k: float(v.get("w", DEFAULT_WEIGHTS.get(k, 0))) for k,v in data.items()}
                return processed
            # normalny format char->number
            return {k: float(v) for k,v in data.items()}
    except (json.JSONDecodeError, FileNotFoundError, StopIteration):
        save_weights(DEFAULT_WEIGHTS)
        return DEFAULT_WEIGHTS.copy()

def save_weights(weights_map):
    # weights_map: dict char->float
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump({k: float(v) for k,v in weights_map.items()}, f, ensure_ascii=False, indent=4)

def reset_weights_to_default():
    save_weights(DEFAULT_WEIGHTS)

# --- clean_text zgodnie z Twoją funkcją ---
def clean_text(text: str) -> str:
    replacements = {
        "–": "-",  # półpauza
        "—": "-",  # pauza
        "“": "\"", "”": "\"",  # cudzysłowy angielskie
        "„": "\"", "‟": "\"",  # polskie otwierające
        "‘": "'", "’": "'", "‚": "'",  # pojedyncze cudzysłowy
        "…": "...",  # wielokropek
        "\u00A0": " ",  # spacja niełamliwa
        '\u2009': " ",  # wąska spacja
        '\u202F': " ",  # wąska niełamliwa spacja
        "•": "-",  # punktory
        "→": "->",
        "←": "<-",
        "’": "'",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# --- analiza (używa wag) ---
def analyze_text(text: str, weights_map):
    import html, re

    allowed_chars = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
    total_chars = len(text)

    # --- Podejrzane znaki typograficzne ---
    suspicious_counts = {}
    weighted_score = 0.0
    for ch, w in weights_map.items():
        if ch in text:  # tylko jeśli znak występuje
            cnt = text.count(ch)
            suspicious_counts[ch] = cnt
            weighted_score += cnt * float(w)

    # --- Znaki spoza ASCII (niepolskie) ---
    non_ascii_chars = [
        c for c in text
        if ord(c) > 127 and c not in allowed_chars and c not in weights_map
    ]
    non_ascii_count = len(non_ascii_chars)

    # --- Średnia długość zdania ---
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

    # --- Gęstość interpunkcji ---
    commas = text.count(',')
    semicolons = text.count(';')
    dashes = text.count('-') + text.count('–') + text.count('—')
    punctuation_density = (commas + semicolons + dashes) / max(1, total_chars) * 100

    # --- Wynik AI ---
    ai_score = (
        weighted_score * 1.8 +
        non_ascii_count * 0.5 +
        max(0, (avg_sentence_length - 18)) * 0.3 +
        punctuation_density * 0.7
    ) / max(1, total_chars / 100)

    if ai_score > 2.0:
        verdict = "❗ Bardzo możliwe, że tekst został wygenerowany przez AI"
        color = "red"
    elif ai_score > 0.7:
        verdict = "⚠️ Tekst posiada elementy charakterystyczne dla AI"
        color = "orange"
    else:
        verdict = "✅ Tekst wygląda na pisany przez człowieka"
        color = "green"

    # --- Podświetlenia ---
    highlighted = ""
    for c in text:
        esc = html.escape(c)
        if c in weights_map:
            w = float(weights_map[c])
            if w >= 4.0:
                bg = "#ffd6d6"
            elif w >= 2.0:
                bg = "#fff4cc"
            else:
                bg = "#ffffe6"
            highlighted += f"<span class='sus' style='background:{bg}' title='waga: {w}'>{esc}</span>"
        elif ord(c) > 127 and c not in allowed_chars:
            highlighted += f"<span class='nonascii' title='znak spoza ASCII'>{esc}</span>"
        else:
            highlighted += esc

    suspicious_chars_list = list(suspicious_counts.keys())
    suspicious_count = sum(suspicious_counts.values())
    non_ascii_chars_list = sorted(set(non_ascii_chars))

    # --- Tabela: wszystkie znaki ---
    suspicious_summary = []

    # 1️⃣ Typograficzne (z weights_map)
    for ch, count in suspicious_counts.items():
        suspicious_summary.append({
            "char": ch,
            "count": count,
            "desc": "Podejrzany znak typograficzny",
            "weight": weights_map.get(ch, 0),
            "type": "typograficzny"
        })

    # 2️⃣ Znaki spoza ASCII
    for ch in non_ascii_chars_list:
        suspicious_summary.append({
            "char": ch,
            "count": non_ascii_chars.count(ch),
            "desc": "Znak spoza ASCII (niepolski)",
            "weight": 0,
            "type": "spoza ASCII"
        })

    # Sortuj dla spójności (np. typograficzne najpierw)
    suspicious_summary.sort(key=lambda x: (x["type"], -x["count"]))

    return {
        "length": total_chars,
        "suspicious_counts": suspicious_counts,
        "weighted_score": round(weighted_score, 3),
        "non_ascii_count": non_ascii_count,
        "non_ascii_chars_list": non_ascii_chars_list,
        "suspicious_count": suspicious_count,
        "suspicious_chars_list": suspicious_chars_list,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "punctuation_density": round(punctuation_density, 3),
        "ai_score": round(ai_score, 3),
        "verdict": verdict,
        "color": color,
        "highlighted_text": highlighted,
        "suspicious_summary": suspicious_summary
    }

# --- ROUTES ---

@app.route("/", methods=["GET", "POST"])
def index():
    weights = load_weights()
    result = None
    text = request.form.get("text", "") if request.method == "POST" else ""
    if request.method == "POST":
        if "clean" in request.form:
            text = clean_text(text)
        elif "analyze" in request.form:
            result = analyze_text(text, weights)
    return render_template("index.html", result=result, text=text)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    weights = load_weights()
    if request.method == "POST":
        # oczekujemy form z nazwami pól równymi znakom
        for key in list(weights.keys()):
            try:
                val = request.form.get(key, None)
                if val is not None:
                    weights[key] = float(val)
            except ValueError:
                pass
        save_weights(weights)
        return redirect(url_for("settings"))
    # przygotuj listę krotek (char, weight, description) dla widoku
    settings_list = [(ch, weights.get(ch, 0.0), CHAR_DESCRIPTIONS.get(ch, "")) for ch in DEFAULT_WEIGHTS.keys()]
    return render_template("settings.html", settings_list=settings_list)

@app.route("/reset_weights", methods=["POST"])
def reset_weights():
    reset_weights_to_default()
    return redirect(url_for("settings"))

if __name__ == "__main__":
    app.run(debug=True)
