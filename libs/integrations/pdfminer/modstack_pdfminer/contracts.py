from pdfminer.layout import LAParams

from modstack.contracts import ToText

class PDFMinerToText(ToText):
    layout_params: LAParams | None = None