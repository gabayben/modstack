from typing import Literal

from modstack.contracts import HtmlToText

ExtractorType = Literal[
    'DefaultExtractor',
    'KeepEverythingExtractor',
    'ArticleExtractor',
    'ArticleSentencesExtractor',
    'LargestContentExtractor',
    'CanolaExtractor',
    'NumWordsRulesExtractor',
]

class BoilerToText(HtmlToText):
    extractor_type: ExtractorType = 'DefaultExtractor'
    try_others: bool = True