"""
nlp_pipeline.py
---------------
Turns the raw stream of fingerspelled letters (with explicit space tokens
inserted whenever the signer pauses / drops their hand) into clean,
spell-checked English text, with optional Bengali translation.

Uses only FOSS libraries: `pyspellchecker` for spelling correction and
`deep-translator` (free, no API key) for English -> Bengali translation.
"""

import re
from spellchecker import SpellChecker
from deep_translator import GoogleTranslator

_spell = SpellChecker()


def letters_to_raw_text(letter_buffer):
    """
    letter_buffer: list of single-character strings, where ' ' (space)
    marks a detected word boundary (a pause in signing).
    Returns a raw (uncorrected) lowercase string, e.g. "hwllo wrold".
    """
    raw = "".join(letter_buffer)
    # collapse multiple consecutive spaces into one, strip leading/trailing
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw.lower()


def spell_correct(raw_text):
    """
    Word-boundary + spelling correction step.
    Splits raw_text on whitespace, spell-checks each token individually,
    and rejoins into a clean sentence. Unknown short tokens (<=1 char)
    are passed through untouched (likely a single confirmed letter,
    e.g. 'I' or 'A').
    """
    if not raw_text:
        return ""

    words = raw_text.split(" ")
    corrected_words = []

    for w in words:
        w = w.strip()
        if not w:
            continue
        if len(w) <= 1:
            corrected_words.append(w.upper() if w.lower() in ("a", "i") else w)
            continue

        correction = _spell.correction(w)
        corrected_words.append(correction if correction else w)

    corrected_text = " ".join(corrected_words)
    # Capitalize first letter of the sentence for a cleaner caption
    if corrected_text:
        corrected_text = corrected_text[0].upper() + corrected_text[1:]
    return corrected_text


def translate_to_bengali(english_text):
    """
    Free, open-source translation via deep-translator's GoogleTranslator
    wrapper (no API key required). Returns the Bengali translation, or the
    original text if translation fails for any reason (e.g. no internet).
    """
    if not english_text:
        return ""
    try:
        return GoogleTranslator(source="en", target="bn").translate(english_text)
    except Exception as e:
        return f"[Translation unavailable: {e}]"


def run_pipeline(letter_buffer, translate=False):
    """
    Full pipeline entry point used by the Streamlit app.
    Returns a dict with raw, english (corrected), and optionally bengali text.
    """
    raw = letters_to_raw_text(letter_buffer)
    english = spell_correct(raw)
    result = {"raw": raw, "english": english, "bengali": None}
    if translate and english:
        result["bengali"] = translate_to_bengali(english)
    return result
