from typing import Iterable

def zip2[F, S](iter1: Iterable[F], iter2: Iterable[S]) -> Iterable[tuple[F, S]]:
    return zip(iter1, iter2)