import re
from typing import Optional

import pandas as pd

from modstack.ai import LLMPrompt, PredictedLabel, ZeroShotClassifierInput
from modstack.artifacts import Artifact
from modstack.artifacts.messages import MessageArtifact
from modstack.core import Module, Modules, module
from modstack.query.common.utils import expand_tokens_with_subtokens
from modstack.utils.globals_helper import globals_helper

@module
def simple_keyword_extractor(
    artifact: Artifact,
    max_keywords: Optional[int] = None,
    filter_stopwords: bool = True,
    **kwargs
) -> set[str]:
    """Extract keywords using nltk and pandas."""
    tokens = [t.strip().lower() for t in re.findall(r'\w+', str(artifact))]
    if filter_stopwords:
        tokens = [t for t in tokens if t not in globals_helper.stopwords]
    value_counts = pd.Series(tokens).value_counts()
    return set(value_counts.index.tolist()[:max_keywords])

@module
def rake_keyword_extractor(
    artifact: Artifact,
    max_keywords: Optional[int] = None,
    expand_with_subtokens: bool = True,
    **kwargs
) -> set[str]:
    """Extract keywords with RAKE."""
    try:
        import nltk
    except ImportError:
        raise ImportError("Please install nltk: `pip install nltk`")
    try:
        from rake_nltk import Rake
    except ImportError:
        raise ImportError("Please install rake_nltk: `pip install rake_nltk`")

    r = Rake(
        sentence_tokenizer=nltk.tokenize.sent_tokenize,
        word_tokenizer=nltk.tokenize.wordpunct_tokenize
    )
    r.extract_keywords_from_text(str(artifact))
    keywords = set(r.get_ranked_phrases()[:max_keywords])
    if expand_with_subtokens:
        keywords = expand_tokens_with_subtokens(keywords)
    return keywords

class ZeroShotKeywordExtractor(Modules.Sync[Artifact, set[str]]):
    """Extract keywords with a zero-shot classifier."""

    def __init__(
        self,
        classifier: Module[ZeroShotClassifierInput, list[PredictedLabel]],
        **kwargs
    ):
        super().__init__(**kwargs)
        self._classifier = classifier

    def _invoke(self, artifact: Artifact, **kwargs) -> set[str]:
        pass

class LLMKeywordExtractor(Modules.Sync[Artifact, set[str]]):
    """Extract keywords with an LLM."""

    def __init__(
        self,
        llm: Module[LLMPrompt, list[MessageArtifact]],
        **kwargs
    ):
        super().__init__(**kwargs)
        self._llm = llm

    def _invoke(self, artifact: Artifact, **kwargs) -> set[str]:
        pass