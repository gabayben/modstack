from enum import StrEnum
from typing import Any, Literal, Optional, TypedDict, Union

from modstack.modules import ModuleLike

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

class PartitionOptions(TypedDict, total=False):
    encoding: Optional[str]
    detection_origin: Optional[str]
    metadata_filename: Optional[str]
    metadata_last_modified: Optional[str]
    include_metadata: Optional[bool]
    languages: Optional[list[str]]
    detect_language_per_artifact: Optional[bool]
    min_partition: Optional[int]
    max_partition: Optional[int]
    date_from_artifact: Optional[bool]
    chunking_strategy: Optional[str]
    paragraph_grouper: Optional[Union[ModuleLike[str, str], Literal[False]]]

def default_partition_options(options: Union[dict[str, Any], PartitionOptions]) -> PartitionOptions:
    options = options if isinstance(options, PartitionOptions) else PartitionOptions(**options)
    options.setdefault('detection_origin', 'text')
    options.setdefault('include_metadata', True)
    options.setdefault('languages', ['auto'])
    options.setdefault('detect_language_per_artifact', False)
    options.setdefault('min_partition', 0)
    options.setdefault('max_partition', 1500)
    options.setdefault('date_from_artifact', False)
    return options