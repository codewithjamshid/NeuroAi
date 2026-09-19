"""TTS on demand: any authenticated user turns a short Uzbek text into a cached Navoiy wav.

The web client calls this whenever it has text but no `tts_url` (face-exercise instructions,
API replies whose TTS failed), so the browser's speechSynthesis stays a last resort.
"""
