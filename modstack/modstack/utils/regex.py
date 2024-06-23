import re

DATETIMETZ_REGEX = r"[A-Za-z]{3},\s\d{1,2}\s[A-Za-z]{3}\s\d{4}\s\d{2}:\d{2}:\d{2}\s[+-]\d{4}"
DATETIMETZ_PATTERN = re.compile(DATETIMETZ_REGEX)

EMAIL_ADDRESS_REGEX = r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+"
EMAIL_ADDRESS_PATTERN = re.compile(EMAIL_ADDRESS_REGEX)

US_PHONE_NUMBER_REGEX = r"(?:\+?(\d{1,3}))?[-. (]*(\d{3})?[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
US_PHONE_NUMBER_PATTERN = re.compile(US_PHONE_NUMBER_REGEX)

IP_ADDRESS_REGEX = (
    r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}",
    r"[a-z0-9]{4}::[a-z0-9]{4}:[a-z0-9]{4}:[a-z0-9]{4}:[a-z0-9]{4}%?[0-9]*",
)
IP_ADDRESS_PATTERN = re.compile(f'{'|'.join(IP_ADDRESS_REGEX)}')

IP_ADDRESS_NAME_REGEX = r"[a-zA-Z0-9-]*\.[a-zA-Z]*\.[a-zA-Z]*"
IP_ADDRESS_NAME_PATTERN = re.compile(IP_ADDRESS_NAME_REGEX)

MAPI_ID_REGEX = r"[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*;"
MAPI_ID_PATTERN = re.compile(MAPI_ID_REGEX)

IMAGE_URL_REGEX = (
    r"(?i)https?://"
    r"(?:[a-z0-9$_@.&+!*\\(\\),%-])+"
    r"(?:/[a-z0-9$_@.&+!*\\(\\),%-]*)*"
    r"\.(?:jpg|jpeg|png|gif|bmp|heic)"
)
IMAGE_URL_PATTERN = re.compile(IMAGE_URL_REGEX)