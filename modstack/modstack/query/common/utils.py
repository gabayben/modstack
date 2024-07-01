import re

from modstack.utils.globals_helper import globals_helper

def expand_tokens_with_subtokens(tokens: set[str]) -> set[str]:
    """Get subtokens from a list of tokens, filtering for stopwords."""
    results = set()
    for token in tokens:
        results.add(token)
        subtokens = re.findall(r'\w+', token)
        if len(subtokens) > 1:
            results.update({st for st in subtokens if st not in globals_helper.stopwords})
    return results