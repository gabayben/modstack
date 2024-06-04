import enum
import typing

import docarray
import docarray.typing as docarray_typing
import docarray.documents as docarray_documents
from docarray.typing.bytes.base_bytes import BaseBytes as DocArrayBaseBytes
from numpy import ndarray
import tenacity

from modstack.utils.constants import VARIADIC_TYPE

_T = typing.TypeVar('_T')

class SchemaType(enum.StrEnum):
    PYDANTIC = 'pydantic'
    TYPED_DICT = 'typed_dict'
    NAMED_TUPLE = 'named_tuple'
    VALUE = 'value'

CallableType = typing.Literal['invoke', 'ainvoke', 'iter', 'aiter', 'effect']
Variadic = typing.Annotated[typing.Iterable[_T], VARIADIC_TYPE]
StreamingChunk = tuple[str, dict[str, typing.Any]]
StreamingCallback = typing.Callable[[str, dict[str, typing.Any]], None]

BaseDoc = docarray.BaseDoc
DocList = docarray.DocList
DocVec = docarray.DocVec

BaseUrl = docarray_typing.AnyUrl
TextUrl = docarray_typing.TextUrl
ImageUrl = docarray_typing.ImageUrl
AudioUrl = docarray_typing.AudioUrl
VideoUrl = docarray_typing.VideoUrl
Mesh3DUrl = docarray_typing.Mesh3DUrl
PointCloud3DUrl = docarray_typing.PointCloud3DUrl

BaseBytes = DocArrayBaseBytes
ImageBytes = docarray_typing.ImageBytes
AudioBytes = docarray_typing.AudioBytes
VideoBytes = docarray_typing.VideoBytes

BaseTensor = docarray_typing.AnyTensor
ImageTenser = docarray_typing.ImageTensor
AudioTensor = docarray_typing.AudioTensor
VideoTensor = docarray_typing.VideoTensor
VerticesAndFaces = docarray_documents.VerticesAndFaces
PointsAndColors = docarray_documents.PointsAndColors

Embedding = ndarray

RetryStrategy = tenacity.retry_base | typing.Callable[[tenacity.RetryCallState], bool]
StopStrategy = tenacity.stop.stop_base | typing.Callable[[tenacity.RetryCallState], bool]
WaitStrategy = tenacity.wait.wait_base | typing.Callable[[tenacity.RetryCallState], int | float]
AfterRetryFailure = typing.Callable[[tenacity.RetryCallState], None]