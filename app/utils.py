import re


def clean_phone(raw):
    """Return a normalised phone number, or None if invalid."""
    p = re.sub(r"[\s\-()]", "", raw or "")
    return p if re.fullmatch(r"\+?\d{10,13}", p) else None