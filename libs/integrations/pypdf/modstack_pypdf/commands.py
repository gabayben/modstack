from modstack.commands import PDFToText
from modstack_pypdf import PyPDFConverter

class PyPDFToText(PDFToText):
    converter: PyPDFConverter | None = None