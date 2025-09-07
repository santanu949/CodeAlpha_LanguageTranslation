import tkinter as tk
from deep_translator import GoogleTranslator

def translate_text():
    src_text = input_text.get("1.0", "end-1c")
    src_lang = src_lang_var.get()
    tgt_lang = tgt_lang_var.get()
    try:
        translated = GoogleTranslator(source=src_lang, target=tgt_lang).translate(src_text)
    except Exception as e:
        translated = "Error: " + str(e)
    output_text.delete("1.0", "end")
    output_text.insert("end", translated)

root = tk.Tk()
root.title("Language Translation Tool")
root.geometry("400x400")

tk.Label(root, text="Enter Text:").pack()
input_text = tk.Text(root, height=5)
input_text.pack()

src_lang_var = tk.StringVar(value='en')
tgt_lang_var = tk.StringVar(value='hi')

tk.Label(root, text="Source Language (eg: en, fr, hi):").pack()
tk.Entry(root, textvariable=src_lang_var).pack()

tk.Label(root, text="Target Language (eg: hi, en, fr):").pack()
tk.Entry(root, textvariable=tgt_lang_var).pack()

tk.Button(root, text="Translate", command=translate_text).pack()

tk.Label(root, text="Translated Text:").pack()
output_text = tk.Text(root, height=5)
output_text.pack()

root.mainloop()
