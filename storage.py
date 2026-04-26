"""
Persistence layer — history, favorites, translation cache, and settings.
All data stored as JSON in a local 'data/' directory.
"""

import json, csv, os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "data"


class Storage:
    """Manages all persistent application state."""

    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self.history_file = DATA_DIR / "history.json"
        self.favorites_file = DATA_DIR / "favorites.json"
        self.cache_file = DATA_DIR / "cache.json"
        self.settings_file = DATA_DIR / "settings.json"

        self.history = self._load(self.history_file, [])
        self.favorites = self._load(self.favorites_file, [])
        self.cache = self._load(self.cache_file, {})
        self.settings = self._load(self.settings_file, self._defaults())

    # ── helpers ──────────────────────────────────────────────
    @staticmethod
    def _defaults():
        return {
            "theme": "dark",
            "font_size": 13,
            "src_lang": "en",
            "tgt_lang": "hi",
            "real_time": False,
            "privacy_mode": False,
            "tts_rate": 160,
            "mode": "general",
            "geometry": "1050x720",
        }

    def _load(self, path, default):
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return default

    def _save(self, path, data):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    # ── history ─────────────────────────────────────────────
    def add_history(self, src, tgt, sl, tl, mode="general"):
        if self.settings.get("privacy_mode"):
            return None
        entry = {
            "src_text": src, "tgt_text": tgt,
            "src_lang": sl, "tgt_lang": tl,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
        }
        self.history.insert(0, entry)
        self.history = self.history[:500]
        self._save(self.history_file, self.history)
        return entry

    def search_history(self, q):
        q = q.lower()
        return [h for h in self.history
                if q in h["src_text"].lower() or q in h["tgt_text"].lower()]

    def clear_history(self):
        self.history = []
        self._save(self.history_file, self.history)

    def delete_history(self, idx):
        if 0 <= idx < len(self.history):
            self.history.pop(idx)
            self._save(self.history_file, self.history)

    # ── favorites ───────────────────────────────────────────
    def toggle_favorite(self, entry):
        for i, f in enumerate(self.favorites):
            if f["src_text"] == entry["src_text"] and f["tgt_lang"] == entry["tgt_lang"]:
                self.favorites.pop(i)
                self._save(self.favorites_file, self.favorites)
                return False
        self.favorites.insert(0, entry)
        self._save(self.favorites_file, self.favorites)
        return True

    def is_favorite(self, src, tl):
        return any(f["src_text"] == src and f["tgt_lang"] == tl for f in self.favorites)

    # ── cache ───────────────────────────────────────────────
    def get_cached(self, text, sl, tl, mode="general"):
        return self.cache.get(f"{sl}|{tl}|{mode}|{text}")

    def set_cached(self, text, result, sl, tl, mode="general"):
        self.cache[f"{sl}|{tl}|{mode}|{text}"] = result
        if len(self.cache) > 2000:
            for k in list(self.cache.keys())[:400]:
                del self.cache[k]
        self._save(self.cache_file, self.cache)

    def cache_size(self):
        return len(self.cache)

    def clear_cache(self):
        self.cache = {}
        self._save(self.cache_file, self.cache)

    # ── settings ────────────────────────────────────────────
    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self._save(self.settings_file, self.settings)

    def save_settings(self):
        self._save(self.settings_file, self.settings)

    # ── export ──────────────────────────────────────────────
    def export_txt(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("TRANSLATION HISTORY\n" + "=" * 50 + "\n\n")
            for e in self.history:
                ts = datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%d %H:%M")
                f.write(f"[{ts}] {e['src_lang']} → {e['tgt_lang']}\n")
                f.write(f"  {e['src_text']}\n  → {e['tgt_text']}\n\n")

    def export_csv(self, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Timestamp", "From", "To", "Source", "Translation", "Mode"])
            for e in self.history:
                w.writerow([e["timestamp"], e["src_lang"], e["tgt_lang"],
                            e["src_text"], e["tgt_text"], e.get("mode", "")])

    def export_json(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
