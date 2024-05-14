from typing import override

from modstack.contracts import PDFToText
from modstack_pypdf import PyPDFConverter

class PyPDFToText(PDFToText):
    converter: PyPDFConverter | None = None

    @classmethod
    @override
    def name(cls) -> str:
        return 'pypdf_to_text'