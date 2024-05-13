from typing import Literal, override

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

    @classmethod
    @override
    def name(cls) -> str:
        return 'boiler_to_text'