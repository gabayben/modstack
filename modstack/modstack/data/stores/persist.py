from typing import Optional, Protocol

import fsspec

class StorePersist(Protocol):
    def persist(
        self,
        path: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        **kwargs
    ) -> None:
        pass