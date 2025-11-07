import tkinter as tk
from tkinter import filedialog, messagebox
import os

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

def process_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        cleaned = clean_text(text)

        base, ext = os.path.splitext(file_path)
        output_path = base + "_clean.txt"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned)

        messagebox.showinfo("Gotowe", f"✅ Plik został oczyszczony:\n\n{output_path}")

    except Exception as e:
        messagebox.showerror("Błąd", f"❌ Wystąpił problem:\n{str(e)}")

def choose_file():
    file_path = filedialog.askopenfilename(
        title="Wybierz plik tekstowy",
        filetypes=[("Pliki tekstowe", "*.txt")]
    )
    if file_path:
        process_file(file_path)

def on_drop(event):
    file_path = event.data.strip("{}")  # usuwa klamry w ścieżkach z spacjami
    if os.path.isfile(file_path) and file_path.lower().endswith(".txt"):
        process_file(file_path)
    else:
        messagebox.showwarning("Nieprawidłowy plik", "Upuść plik .txt")

# --- GUI ---
root = tk.Tk()
root.title("AI Text Cleaner")
root.geometry("340x180")
root.resizable(False, False)

label = tk.Label(root, text="Oczyść tekst AI z nietypowych znaków", pady=15)
label.pack()

button = tk.Button(root, text="Wybierz plik", command=choose_file, width=20, height=2)
button.pack(pady=5)

drop_label = tk.Label(root, text="\nLub przeciągnij plik .txt tutaj", fg="gray")
drop_label.pack()

info = tk.Label(root, text="\nZapisze wynik jako *_clean.txt", fg="gray")
info.pack()

# --- Drag & Drop ---
try:
    # import dopiero przy uruchomieniu — nie psuje na macOS
    from tkinterdnd2 import TkinterDnD, DND_FILES
    root.destroy()
    root = TkinterDnD.Tk()
    root.title("AI Text Cleaner")
    root.geometry("340x180")
    root.resizable(False, False)

    label = tk.Label(root, text="Oczyść tekst AI z nietypowych znaków", pady=15)
    label.pack()

    button = tk.Button(root, text="Wybierz plik", command=choose_file, width=20, height=2)
    button.pack(pady=5)

    drop_label = tk.Label(root, text="\nLub przeciągnij plik .txt tutaj", fg="gray")
    drop_label.pack()

    info = tk.Label(root, text="\nZapisze wynik jako *_clean.txt", fg="gray")
    info.pack()

    drop_label.drop_target_register(DND_FILES)
    drop_label.dnd_bind('<<Drop>>', on_drop)

except ImportError:
    # Jeśli brak tkinterdnd2, po prostu działa bez drag&drop
    pass

root.mainloop()
