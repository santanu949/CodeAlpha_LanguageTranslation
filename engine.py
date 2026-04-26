"""
Translation engine — async translation, auto-detect, caching, retry logic.
"""

import threading
from deep_translator import GoogleTranslator

# ── language data ───────────────────────────────────────────
_FALLBACK = {
    "english": "en", "hindi": "hi", "french": "fr", "spanish": "es",
    "german": "de", "italian": "it", "portuguese": "pt", "russian": "ru",
    "japanese": "ja", "korean": "ko", "chinese (simplified)": "zh-CN",
    "chinese (traditional)": "zh-TW", "arabic": "ar", "bengali": "bn",
    "tamil": "ta", "telugu": "te", "marathi": "mr", "urdu": "ur",
    "dutch": "nl", "turkish": "tr", "swedish": "sv", "polish": "pl",
    "greek": "el", "thai": "th",
}

try:
    LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)
except Exception:
    LANGUAGES = _FALLBACK

LANG_CODES = {v: k.title() for k, v in LANGUAGES.items()}
LANG_CODES["auto"] = "Auto-Detect"

MODES = {
    "general":   "General",
    "formal":    "Formal",
    "casual":    "Casual",
    "technical": "Technical",
    "business":  "Business",
    "academic":  "Academic",
}


class TranslationEngine:
    """Thread-safe translation engine with caching and retry."""

    def __init__(self, storage):
        self.storage = storage
        self._lock = threading.Lock()

    # ── async translate ─────────────────────────────────────
    def translate(self, text, sl, tl, mode="general", on_done=None, on_error=None):
        if not text.strip():
            if on_done:
                on_done("")
            return

        def _work():
            # check cache
            cached = self.storage.get_cached(text, sl, tl, mode)
            if cached:
                if on_done:
                    on_done(cached)
                return
            # try up to 2 times
            for attempt in range(2):
                try:
                    with self._lock:
                        result = GoogleTranslator(source=sl, target=tl).translate(text)
                    if result:
                        self.storage.set_cached(text, result, sl, tl, mode)
                        if on_done:
                            on_done(result)
                        return
                except Exception as e:
                    if attempt == 1:
                        if on_error:
                            on_error(str(e))
                        return

        threading.Thread(target=_work, daemon=True).start()

    # ── sync translate ──────────────────────────────────────
    def translate_sync(self, text, sl, tl):
        if not text.strip():
            return "", None
        try:
            r = GoogleTranslator(source=sl, target=tl).translate(text)
            return (r or ""), None
        except Exception as e:
            return "", str(e)

    # ── detect language ─────────────────────────────────────
    def detect(self, text):
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            return "en"

    # ── helpers ─────────────────────────────────────────────
    def lang_name(self, code):
        return LANG_CODES.get(code, code)

    def lang_code(self, name):
        return LANGUAGES.get(name.lower(), name)

    def all_languages(self):
        return LANGUAGES

    def language_list(self):
        """Return sorted list of 'Name (code)' strings for dropdowns."""
        items = sorted(LANGUAGES.items())
        return [f"{name.title()} ({code})" for name, code in items]

    def parse_lang_selection(self, display):
        """Extract code from 'Name (code)' string."""
        if "(" in display and display.endswith(")"):
            return display.rsplit("(", 1)[1].rstrip(")")
        return display
