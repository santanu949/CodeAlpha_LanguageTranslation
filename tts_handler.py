"""
Text-to-Speech wrapper using pyttsx3 (offline, cross-platform).
"""

import threading

_engine = None
_lock = threading.Lock()


def _get_engine():
    global _engine
    if _engine is None:
        try:
            import pyttsx3
            _engine = pyttsx3.init()
        except Exception:
            _engine = None
    return _engine


def speak(text, rate=160):
    """Speak text asynchronously."""
    def _work():
        with _lock:
            eng = _get_engine()
            if eng is None:
                return
            try:
                eng.setProperty("rate", rate)
                eng.say(text)
                eng.runAndWait()
            except Exception:
                pass
    threading.Thread(target=_work, daemon=True).start()


def stop():
    """Stop current speech."""
    with _lock:
        eng = _get_engine()
        if eng:
            try:
                eng.stop()
            except Exception:
                pass


def available():
    """Check if TTS is available."""
    return _get_engine() is not None
