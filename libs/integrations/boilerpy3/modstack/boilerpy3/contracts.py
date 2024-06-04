from typing import Literal

from modstack.modules import ToText

ExtractorType = Literal[
    'DefaultExtractor',
    'KeepEverythingExtractor',
    'ArticleExtractor',
    'ArticleSentencesExtractor',
    'LargestContentExtractor',
    'CanolaExtractor',
    'NumWordsRulesExtractor',
]

class BoilerToText(ToText):
    extractor_type: ExtractorType = 'DefaultExtractor'
    try_others: bool = True