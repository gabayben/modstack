"""
Credit to Unstructured - https://github.com/Unstructured-IO/unstructured/blob/main/unstructured/file_utils/encoding.py
"""

from typing import Optional

import chardet

from modstack.artifacts import Artifact, ArtifactSource, ByteStream

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

def detect_encoding(source: ArtifactSource) -> tuple[str, bytes]:
    bytes_ = bytes(ByteStream.from_source(source))
    result = chardet.detect(bytes_)
    encoding = result['encoding']
    confidence = result['confidence']

    if encoding is None or confidence < ENCODE_REC_THRESHOLD:
        for enc in COMMON_ENCODINGS:
            try:
                if isinstance(source, Artifact):
                    _ = bytes_.decode(enc)
                else:
                    with open(source, encoding=enc) as f:
                        _ = f.read()
                encoding = enc
            except UnicodeError:
                continue
        else:
            raise UnicodeDecodeError(
                'Unable to determine the encoding of the source '
                'or match it with any of the specified encodings.',
                bytes_,
                0,
                len(bytes_),
                'Invalid encoding'
            )

    return format_encoding_str(encoding), bytes_

def read_text_file(
    source: ArtifactSource,
    encoding: Optional[str] = None
) -> tuple[str, str]:
    """
    Extracts document metadata from a plain text document.
    """
    if encoding:
        formatted_encoding = format_encoding_str(encoding)
        bytes_ = bytes(ByteStream.from_source(source))
        text = bytes_.decode(formatted_encoding)
    else:
        formatted_encoding, bytes_ = detect_encoding(source)
        text = bytes_.decode(formatted_encoding)
    return formatted_encoding, text