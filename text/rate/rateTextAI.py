from flask import Flask, render_template, request
import re
import html

app = Flask(__name__)

# --- Funkcja czyszcząca tekst ---
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


# --- Funkcja analizy tekstu ---
def analyze_text(text: str):
    # Wagi dla podejrzanych znaków
    suspicious_char_weights = {
        '–': 5,   # półpauza
        '—': 5,   # pauza
        '„': 3, '”': 3, '«': 3, '»': 3,
        '‘': 2, '’': 2, '‚': 2,
        '•': 1,
        '…': 1,
        '\u00A0': 2,   # niełamliwa spacja
        '\u2009': 2,   # wąska spacja
        '\u202F': 2,   # wąska niełamliwa spacja
    }

    allowed_chars = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")

    total_chars = len(text)
    suspicious_score = 0
    suspicious_count = 0

    for c in text:
        if c in suspicious_char_weights:
            suspicious_score += suspicious_char_weights[c]
            suspicious_count += 1

    non_ascii_count = sum(1 for c in text if ord(c) > 127 and c not in allowed_chars)

    # Statystyka językowa
    import re, html
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

    commas = text.count(',')
    semicolons = text.count(';')
    dashes = text.count('-') + text.count('–') + text.count('—')
    punctuation_density = (commas + semicolons + dashes) / max(1, total_chars) * 100

    # Nowy wzór na wskaźnik AI – silniej reaguje na znaki o wysokiej wadze
    ai_score = (
        suspicious_score * 1.5 +
        non_ascii_count * 0.5 +
        (avg_sentence_length - 18) * 0.3 +
        punctuation_density * 0.8
    ) / max(1, total_chars / 100)

    if ai_score > 1.5:
        verdict = "❗ Możliwe, że tekst został wygenerowany przez AI"
        color = "red"
    elif ai_score > 0.5:
        verdict = "⚠️ Tekst może mieć elementy charakterystyczne dla AI"
        color = "orange"
    else:
        verdict = "✅ Tekst wygląda na pisany przez człowieka"
        color = "green"

    # Podświetlanie podejrzanych znaków
    highlighted = ""
    for c in text:
        escaped = html.escape(c)
        if c in suspicious_char_weights:
            highlighted += f"<span style='background-color: yellow; color: red;' title='Podejrzany znak (waga {suspicious_char_weights[c]})'>{escaped}</span>"
        elif ord(c) > 127 and c not in allowed_chars:
            highlighted += f"<span style='background-color: #ffe6b3;' title='Znak spoza ASCII'>{escaped}</span>"
        else:
            highlighted += escaped

    return {
        "length": total_chars,
        "suspicious_chars": suspicious_count,
        "non_ascii_chars": non_ascii_count,
        "avg_sentence_length": avg_sentence_length,
        "punctuation_density": punctuation_density,
        "ai_score": ai_score,
        "verdict": verdict,
        "color": color,
        "highlighted_text": highlighted
    }

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    text = request.form.get("text", "")

    if request.method == "POST":
        if "analyze" in request.form:
            result = analyze_text(text)
        elif "clean" in request.form:
            text = clean_text(text)
            result = analyze_text(text)

    return render_template("index.html", result=result, text=text)


if __name__ == "__main__":
    app.run(debug=True)
