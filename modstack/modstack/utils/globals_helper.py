"""
Credit to LlamaIndex - https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/utils.py
"""

import os
from typing import List, Optional

class GlobalsHelper:
    """Helper to retrieve globals.

    Helpful for global caching of certain variables that can be expensive to load.
    (e.g. tokenization)

    """

    _stopwords: Optional[List[str]] = None
    _nltk_data_dir: Optional[str] = None

    def __init__(self) -> None:
        """Initialize NLTK stopwords and punkt."""
        import nltk

        self._nltk_data_dir = os.environ.get(
            "NLTK_DATA",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "_static/nltk_cache",
            ),
        )

        if self._nltk_data_dir not in nltk.data.path:
            nltk.data.path.append(self._nltk_data_dir)

        # ensure access to data is there
        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords", download_dir=self._nltk_data_dir)

        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt", download_dir=self._nltk_data_dir)

    @property
    def stopwords(self) -> List[str]:
        """Get stopwords."""
        if self._stopwords is None:
            try:
                import nltk
                from nltk.corpus import stopwords
            except ImportError:
                raise ImportError(
                    "`nltk` package not found, please run `pip install nltk`"
                )

            try:
                nltk.data.find("corpora/stopwords", paths=[self._nltk_data_dir])
            except LookupError:
                nltk.download("stopwords", download_dir=self._nltk_data_dir)
            self._stopwords = stopwords.words("english")
        return self._stopwords

globals_helper = GlobalsHelper()