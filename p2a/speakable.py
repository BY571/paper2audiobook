"""Rewrite things a TTS voice reads letter by letter into words: 2.2M -> 2.2 million, 50 Hz -> 50 hertz."""
from __future__ import annotations

import re

NUM = r"(\d[\d,]*(?:\.\d+)?)"

UNITS = {  # suffix -> (singular, plural); matched case-sensitively right after a number
    "kHz": ("kilohertz", "kilohertz"), "MHz": ("megahertz", "megahertz"), "GHz": ("gigahertz", "gigahertz"), "Hz": ("hertz", "hertz"),
    "ms": ("millisecond", "milliseconds"), "μs": ("microsecond", "microseconds"), "µs": ("microsecond", "microseconds"), "ns": ("nanosecond", "nanoseconds"),
    "sec": ("second", "seconds"), "min": ("minute", "minutes"), "hrs": ("hour", "hours"),
    "TB": ("terabyte", "terabytes"), "GB": ("gigabyte", "gigabytes"), "MB": ("megabyte", "megabytes"), "KB": ("kilobyte", "kilobytes"), "kB": ("kilobyte", "kilobytes"),
    "fps": ("frame per second", "frames per second"), "px": ("pixel", "pixels"),
    "mm": ("millimeter", "millimeters"), "cm": ("centimeter", "centimeters"), "km": ("kilometer", "kilometers"), "kg": ("kilogram", "kilograms"),
}
MAGNITUDES = {"k": "thousand", "K": "thousand", "M": "million", "B": "billion"}
SYMBOLS = {
    "\xa0": " ", "±": " plus or minus ", "−": " minus ", "→": " to ", "←": " from ", "≥": " at least ", "≤": " at most ", "≈": " approximately ",
    "π": " pi ", "σ": " sigma ", "α": " alpha ", "β": " beta ", "γ": " gamma ", "δ": " delta ", "ε": " epsilon ", "θ": " theta ",
    "λ": " lambda ", "τ": " tau ", "φ": " phi ", "Δ": " delta ", "Σ": " sigma ",
}


def _is_one(num: str) -> bool:
    return num.replace(",", "") in ("1", "1.0")


def speakable(text: str) -> str:
    for sym, word in SYMBOLS.items():
        text = text.replace(sym, word)
    # units: "0.29 ms", "50Hz", "40 GB"; longest suffix first so kHz wins over Hz
    for suffix in sorted(UNITS, key=len, reverse=True):
        sing, plur = UNITS[suffix]
        text = re.sub(rf"{NUM}\s?{re.escape(suffix)}\b", lambda m: f"{m.group(1)} {sing if _is_one(m.group(1)) else plur}", text)
    # magnitudes: "2.2M", "400M", "3.6 B-parameter", "20k"
    text = re.sub(rf"{NUM}\s?([kKMB])(?=\b|-)", lambda m: f"{m.group(1)} {MAGNITUDES[m.group(2)]}", text)
    # dimensions written with x: 84x84, 224×224
    text = re.sub(rf"{NUM}[x×]{NUM}", r"\1 by \2", text)
    # comparison signs before a number
    text = re.sub(rf">\s?=?\s?(?={NUM})", "more than ", text)
    text = re.sub(rf"<\s?=?\s?(?={NUM})", "less than ", text)
    text = re.sub(rf"~\s?(?={NUM})", "about ", text)
    return re.sub(r"[ ]{2,}", " ", text).strip()
