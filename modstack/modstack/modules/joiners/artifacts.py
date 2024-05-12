from collections import defaultdict
from enum import StrEnum
import logging
from math import inf
from typing import Iterable

from modstack.commands import JoinArtifacts, command
from modstack.modules import Module
from modstack.typing import Artifact, Variadic
from modstack.utils.func import chain_iterables, tzip

logger = logging.getLogger(__name__)

class ArtifactJoiner(Module):
    class Mode(StrEnum):
        Concatenate = 'concatenate',
        Merge = 'merge',
        ReciprocalRankFusion = 'reciprocal_rank_fusion'

    @command(JoinArtifacts, name=Mode.Concatenate)
    def concatenate(
        self,
        artifacts: Variadic[list[Artifact]],
        weights: list[float] | None = None,
        top_k: int | None = None,
        sort_by_score: bool = True,
        **kwargs
    ) -> list[Artifact]:
        joined_artifacts: list[Artifact] = []
        artifacts_by_id: dict[str, list[Artifact]] = defaultdict(list)
        for artifact in chain_iterables(artifacts):
            artifacts_by_id[artifact.id].append(artifact)
        for group in artifacts_by_id.values():
            artifact_with_best_score = max(group, key=lambda artifact: artifact.score if artifact.score else -inf)
            joined_artifacts.append(artifact_with_best_score)
        return self._sort_and_filter_artifacts(
            joined_artifacts,
            weights,
            top_k,
            sort_by_score
        )

    @command(JoinArtifacts, name=Mode.Merge)
    def merge(
        self,
        artifacts: Variadic[list[Artifact]],
        weights: list[float] | None = None,
        top_k: int | None = None,
        sort_by_score: bool = True,
        **kwargs
    ) -> list[Artifact]:
        artifacts = list(artifacts)
        artifact_map: dict[str, Artifact] = {}
        scores_by_id: dict[str, float] = defaultdict(float)
        weights = weights if weights else [1 / len(artifacts)] * len(artifacts)
        for artifact_list, weight in tzip(artifacts, weights):
            for artifact in artifact_list:
                artifact_map[artifact.id] = artifact
                scores_by_id[artifact.id] += (artifact.score if artifact.score else 0) * weight
        for artifact in artifact_map.values():
            artifact.score = scores_by_id[artifact.id]
        return self._sort_and_filter_artifacts(
            artifact_map.values(),
            weights,
            top_k,
            sort_by_score
        )

    @command(JoinArtifacts, name=Mode.ReciprocalRankFusion)
    def reciprocal_rank_fusion(
        self,
        artifacts: Variadic[list[Artifact]],
        weights: list[float] | None = None,
        top_k: int | None = None,
        sort_by_score: bool = True,
        **kwargs
    ) -> list[Artifact]:
        artifacts = list(artifacts)
        artifact_map: dict[str, Artifact] = {}
        scores_by_id: dict[str, float] = defaultdict(float)
        weights = weights if weights else [1 / len(artifacts)] * len(artifacts)
        k = 61
        for artifact_list, weight in tzip(artifacts, weights):
            for rank, artifact in enumerate(artifact_list):
                artifact_map[artifact.id] = artifact
                scores_by_id[artifact.id] += (weight * len(artifacts)) / (k + rank)
        for _id in scores_by_id:
            scores_by_id[_id] /= len(artifacts) / k
        for artifact in artifact_map.values():
            artifact.score = scores_by_id[artifact.id]
        return self._sort_and_filter_artifacts(
            artifact_map.values(),
            weights,
            top_k,
            sort_by_score
        )

    def _sort_and_filter_artifacts(
        self,
        artifacts: Iterable[Artifact],
        weights: list[float],
        top_k: int | None,
        sort_by_score: bool
    ) -> list[Artifact]:
        if sort_by_score:
            artifacts = sorted(
                artifacts,
                key=lambda artifact: artifact.score if artifact.score is not None else -inf
            )
            if any(artifact.score is None for artifact in artifacts):
                logger.info(
                    'Some of the Artifacts ArtifactJoiner got have score=None. It was configured to sort Artifacts by '
                    'score, so those with score=None were sorted as if they had a score of -inf.'
                )
        if top_k:
            artifacts = artifacts[:top_k]
        return artifacts