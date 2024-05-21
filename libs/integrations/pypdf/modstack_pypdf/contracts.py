from modstack.contracts import ToText
from modstack_pypdf import PyPDFConverter

class PyPDFToText(ToText):
    converter: PyPDFConverter | None = None