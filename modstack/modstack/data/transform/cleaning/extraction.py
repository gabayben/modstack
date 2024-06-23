import datetime
from typing import Optional

from modstack.utils.regex import *

_OrderedBulletsTuple = tuple[Optional[str], Optional[str], Optional[str]]

def extract_datetimetz(text: str) -> list[datetime.datetime]:
    extractions = re.findall(DATETIMETZ_PATTERN, text)
    return [
        datetime.datetime.strptime('%a, %d %b %y %H:%M:%S %z', extraction)
        for extraction in extractions
    ]

def extract_email_addresses(text: str) -> list[str]:
    return re.findall(EMAIL_ADDRESS_PATTERN, text.lower())

def extract_us_phone_numbers(text: str) -> list[str]:
    return re.findall(US_PHONE_NUMBER_PATTERN, text)

def extract_ip_addresses(text: str) -> list[str]:
    return re.findall(IP_ADDRESS_PATTERN, text)

def extract_ip_address_names(text: str) -> list[str]:
    return re.findall(IP_ADDRESS_NAME_PATTERN, text)

def extract_mapi_ids(text: str) -> list[str]:
    mapi_ids: list[str] = re.findall(MAPI_ID_PATTERN, text)
    return [mapi_id.replace(';', '') for mapi_id in mapi_ids]

def extract_image_urls(text: str) -> list[str]:
    return re.findall(IMAGE_URL_PATTERN, text)

def extract_ordered_bullets(text: str) -> _OrderedBulletsTuple:
    a, b, c, temp = None, None, None, None
    split_text = text.split()
    if '.' not in split_text[0] or '..' in split_text[0]:
        return a, b, c
    bullet = re.split(r'[.]', split_text[0])
    if not bullet[-1]:
        del bullet[-1]
    if len(bullet[0]) > 2:
        return a, b, c
    a, *temp = bullet
    if temp:
        try:
            b, c, *_ = temp
        except ValueError:
            b = temp
        b = ''.join(b)
        c = ''.join(c) if c else None
    return a, b, c

def extract_text_before(
    text: str,
    pattern: str,
    index: int = 0,
    strip: bool = True
) -> str:
    regex_match = _get_indexed_match(text, pattern, index=index)
    start, _ = regex_match.span()
    before_match = text[:start]
    return before_match.rstrip() if strip else before_match

def extract_text_after(
    text: str,
    pattern: str,
    index: int = 0,
    strip: bool = True
) -> str:
    regex_match = _get_indexed_match(text, pattern, index=index)
    _, end = regex_match.span()
    after_match = text[end:]
    return after_match.lstrip() if strip else after_match

def _get_indexed_match(text: str, pattern: str, index: int = 0) -> re.Match:
    if index is None or index < 0:
        raise ValueError(f'The index is {index}. Index must be a non-negative integer.')
    regex_match = None
    for i, match in enumerate(re.finditer(pattern, text)):
        if i == index:
            regex_match = match
    if regex_match is None:
        raise ValueError(f'Result with index {index} was not found. The largest index was {i}.')
    return regex_match