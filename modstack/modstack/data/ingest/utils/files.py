import chardet

ENCODE_REC_THRESHOLD = 0.8
COMMON_ENCODINGS = [
    "utf_8",
    "iso_8859_1",
    "iso_8859_6",
    "iso_8859_8",
    "ascii",
    "big5",
    "utf_16",
    "utf_16_be",
    "utf_16_le",
    "utf_32",
    "utf_32_be",
    "utf_32_le",
    "euc_jis_2004",
    "euc_jisx0213",
    "euc_jp",
    "euc_kr",
    "gb18030",
    "shift_jis",
    "shift_jis_2004",
    "shift_jisx0213"
]

def format_encoding_str(encoding: str) -> str:
    """
    Format input encoding string (e.g., `utf-8`, `iso-8859-1`, etc).
    Parameters
    ----------
    encoding
        The encoding string to be formatted (e.g., `UTF-8`, `utf_8`, `ISO-8859-1`, `iso_8859_1`,
        etc).
    """
    formatted_encoding = encoding.lower().replace('_', '-')
    # Special case for Hebrew charsets with directional annotations
    annotated_encodings = ["iso-8859-6-i", "iso-8859-6-e", "iso-8859-8-i", "iso-8859-8-e"]
    if formatted_encoding in annotated_encodings:
        formatted_encoding = formatted_encoding[:-2]
    return formatted_encoding

def validate_encoding(encoding: str) -> bool:
    """
    Checks if an encoding string is valid. Helps to avoid errors in cases where
    invalid encodings are extracted from malformed documents.
    """
    for common_encoding in COMMON_ENCODINGS:
        if format_encoding_str(encoding) == format_encoding_str(common_encoding):
            return True
    return False