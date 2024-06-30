from typing import NotRequired, TypedDict

class PartitionOptions(TypedDict):
    content_source: NotRequired[str]

def default_partition_options(options: PartitionOptions) -> PartitionOptions:
    options.setdefault('content_source', 'text/html')
    return options