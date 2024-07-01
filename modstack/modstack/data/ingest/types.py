from enum import StrEnum
from typing import NotRequired, TypedDict

class IngestFileType(StrEnum):
    CSV = 'csv'
    DOC = 'doc'
    DOCX = 'docx'
    EMAIL = 'eml'
    EPUB = 'epub'
    HEIC = 'heic'
    HTML = 'html'
    JPG = 'jpg'
    MESSAGE = 'msg'
    ODT = 'odt'
    PDF = 'pdf'
    PNG = 'png'
    PPT = 'ppt'
    PPTX = 'pptx'
    RTF = 'rtf'
    TEXT = 'txt'
    TSV = 'tsv'
    XLSX = 'xlsx'
    XML = 'xml'

class PartitionOptions(TypedDict):
    content_source: NotRequired[str]

def default_partition_options(options: PartitionOptions) -> PartitionOptions:
    options.setdefault('content_source', 'text/html')
    return options