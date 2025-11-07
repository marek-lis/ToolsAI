from flask import Flask, render_template_string, request
import re
import html

app = Flask(__name__)

def analyze_text(text: str):
    # Typowe znaki typograficzne, które mogą sugerować generację przez AI lub edytor tekstu
    suspicious_chars = {
        '„', '”', '«', '»', '‘', '’', '‚', '–', '—', '•', '…',
        '\u00A0',  # niełamliwa spacja
        '\u2009',  # wąska spacja
        '\u202F',  # wąska niełamliwa spacja
    }

    allowed_chars = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")

    total_chars = len(text)
    suspicious_count = sum(1 for c in text if c in suspicious_chars)
    non_ascii_count = sum(1 for c in text if ord(c) > 127 and c not in allowed_chars)

    # Statystyka językowa
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

    commas = text.count(',')
    semicolons = text.count(';')
    dashes = text.count('-') + text.count('–') + text.count('—')
    punctuation_density = (commas + semicolons + dashes) / max(1, total_chars) * 100

    # Wskaźnik AI
    ai_score = (
        suspicious_count * 2 +
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
        if c in suspicious_chars:
            highlighted += f"<span style='background-color: yellow; color: red;' title='Podejrzany znak'>{escaped}</span>"
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


TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>AI Text Detector</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #fafafa; }
        h1 { color: #333; }
        textarea { width: 100%; height: 200px; font-size: 1em; padding: 10px; }
        button { padding: 10px 20px; font-size: 1em; margin-top: 10px; cursor: pointer; }
        .result { margin-top: 30px; padding: 20px; border-radius: 8px; background: white; box-shadow: 0 0 6px #ccc; }
        .highlighted { font-family: monospace; white-space: pre-wrap; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #ddd; }
        .legend { margin-top: 10px; font-size: 0.9em; color: #555; }
        .legend span { padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🧠 AI Text Detector</h1>
    <form method="post">
        <label>Wklej tekst do analizy:</label><br>
        <textarea name="text" placeholder="Wklej tutaj tekst...">{{ request.form.text or '' }}</textarea><br>
        <button type="submit">Analizuj</button>
    </form>

    {% if result %}
    <div class="result">
        <h2 style="color: {{ result.color }}">{{ result.verdict }}</h2>
        <ul>
            <li>Długość tekstu: {{ result.length }}</li>
            <li>Podejrzane znaki typograficzne: {{ result.suspicious_chars }}</li>
            <li>Znaki spoza ASCII (niepolskie): {{ result.non_ascii_chars }}</li>
            <li>Średnia długość zdania: {{ "%.2f"|format(result.avg_sentence_length) }} słów</li>
            <li>Gęstość interpunkcji: {{ "%.2f"|format(result.punctuation_density) }}%</li>
            <li>Wskaźnik AI: {{ "%.2f"|format(result.ai_score) }}</li>
        </ul>
        <div class="legend">
            🔶 <span style="background-color: yellow;">żółty</span> – podejrzane znaki typograficzne<br>
            🟧 <span style="background-color: #ffe6b3;">jasnopomarańczowy</span> – inne znaki spoza ASCII
        </div>
        <h3>Podgląd z zaznaczeniem znaków:</h3>
        <div class="highlighted">{{ result.highlighted_text|safe }}</div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        text = request.form.get("text", "")
        result = analyze_text(text)
    return render_template_string(TEMPLATE, result=result, request=request)


if __name__ == "__main__":
    app.run(debug=True)
