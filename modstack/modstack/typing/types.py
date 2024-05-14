import typing
from typing import Annotated, Iterable

from docarray import (
    BaseDoc as DocArrayBaseDoc,
    DocList as DocArrayDocList,
    DocVec as DocArrayDocVec
)
from docarray.typing import (
    AnyUrl,
    TextUrl as DocArrayTextUrl,
    ImageUrl as DocArrayImageUrl,
    VideoUrl as DocArrayVideoUrl,
    AudioUrl as DocArrayAudioUrl,
    Mesh3DUrl as DocArrayMesh3DUrl,
    PointCloud3DUrl as DocArrayPointCloud3DUrl,
    ImageBytes as DocArrayImageBytes,
    VideoBytes as DocArrayVideoBytes,
    AudioBytes as DocArrayAudioBytes
)
from docarray.typing.bytes.base_bytes import BaseBytes as DocArrayBaseBytes
from numpy import ndarray

from modstack.constants import VARIADIC_TYPE

_T = typing.TypeVar('_T')

Variadic = Annotated[Iterable[_T], VARIADIC_TYPE]
StreamingChunk = tuple[str, dict[str, typing.Any]]
StreamingCallback = typing.Callable[[str, dict[str, typing.Any]], None]

BaseDoc = DocArrayBaseDoc
DocList = DocArrayDocList
DocVec = DocArrayDocVec

BaseUrl = AnyUrl
TextUrl = DocArrayTextUrl
ImageUrl = DocArrayImageUrl
VideoUrl = DocArrayVideoUrl
AudioUrl = DocArrayAudioUrl
Mesh3DUrl = DocArrayMesh3DUrl
PointCloud3DUrl = DocArrayPointCloud3DUrl

BaseBytes = DocArrayBaseBytes
ImageBytes = DocArrayImageBytes
VideoBytes = DocArrayVideoBytes
AudioBytes = DocArrayAudioBytes

Embedding = ndarray