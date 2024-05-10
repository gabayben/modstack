from typing import Literal

from modstack.commands import HtmlToText

ExtractorType = Literal[
    'DefaultExtractor',
    'ArticleExtractor',
    'ArticleSentencesExtractor',
    'LargestContentExtractor',
    'CanolaExtractor',
    'KeepEverythingExtractor',
    'NumWordsRulesExtractor',
]

class BoilerToText(HtmlToText):
    extractor_type: ExtractorType = 'DefaultExtractor'
    try_others: bool = True