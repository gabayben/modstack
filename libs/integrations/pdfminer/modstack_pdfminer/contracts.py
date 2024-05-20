from pdfminer.layout import LAParams

from modstack.contracts import PDFToText

class PDFMinerToText(PDFToText):
    layout_params: LAParams | None = None