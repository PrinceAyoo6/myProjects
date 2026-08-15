# detector.py

import os

SUSPICIOUS_EXTENSIONS = [
    # Generic / classic
    ".encrypted",
    ".locked",
    ".crypt",
    ".ransom",
    ".crypto",
    # WannaCry / WannaCrypt
    ".wncry",
    ".wncryt",
    ".wncrypt",
    # Locky / Jaff
    ".locky",
    ".zepto",
    ".odin",
    ".shit",
    ".thor",
    ".aesir",
    ".zzzzz",
    ".jaff",
    # Dharma / CrySiS
    ".dharma",
    ".phobos",
    ".wallet",
    ".onion",
    # STOP / DJVU (most common 2023-2025)
    ".stop",
    ".djvu",
    ".djvus",
    ".djvuu",
    ".udjvu",
    ".rumba",
    ".shadow",
    # REvil / Sodinokibi
    ".revil",
    ".sodinokibi",
    # Ryuk
    ".ryk",
    ".ryuk",
    # LockBit
    ".lockbit",
    # Misc common
    ".enc",
    ".ezz",
    ".ecc",
    ".exx",
    ".7z.encrypted",
    ".crypted",
    ".cerber",
    ".cerber2",
    ".cerber3",
    ".vault",
    ".kimcil",
    ".pay2key",
]


def analyze_file(file_path):
    """
    Analyzes a file path for ransomware indicators.
    Handles direct extensions (.encrypted) and appended extensions (.encrypted.txt from Windows hidden extension feature).
    Returns (True, extension) if suspicious, or (False, None) if clean.
    """
    file_path_lower = file_path.lower()
    filename = os.path.basename(file_path_lower)

    # 1. Direct extension match (e.g. sample.encrypted)
    for ext in SUSPICIOUS_EXTENSIONS:
        if filename.endswith(ext):
            return True, ext

    # 2. Appended extension match (e.g. sample.encrypted.txt when Windows hides extensions)
    for ext in SUSPICIOUS_EXTENSIONS:
        if f"{ext}." in filename or f"{ext}_" in filename or f"{ext}-" in filename:
            return True, ext

    return False, None
