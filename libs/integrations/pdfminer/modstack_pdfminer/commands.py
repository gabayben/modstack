from pdfminer.layout import LAParams

from modstack.commands import PDFToText

class PDFMinerToText(PDFToText):
    layout_params: LAParams | None = None