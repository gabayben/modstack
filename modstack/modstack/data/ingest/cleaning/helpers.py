from modstack.utils.regex import *

def clean_non_ascii_chars(text: str) -> str:
    return text.encode('ascii', 'ignore').decode()

def clean_extra_whitespace(text: str) -> str:
    text = re.sub(r'[\xa0\n]', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()