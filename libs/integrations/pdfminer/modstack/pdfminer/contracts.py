from pdfminer.layout import LAParams

from modstack.modules import ToText

class PDFMinerToText(ToText):
    layout_params: LAParams | None = None