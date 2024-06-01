from modstack.core.modules.converters import ToText
from modstack.pypdf import PyPDFConverter

class PyPDFToText(ToText):
    converter: PyPDFConverter | None = None