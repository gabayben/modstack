from pdfminer.layout import LAParams

from modstack.core.modules.converters import ToText

class PDFMinerToText(ToText):
    layout_params: LAParams | None = None