from typing import override

from pdfminer.layout import LAParams

from modstack.contracts import PDFToText

class PDFMinerToText(PDFToText):
    layout_params: LAParams | None = None

    @classmethod
    @override
    def name(cls) -> str:
        return 'pdfminer_to_text'