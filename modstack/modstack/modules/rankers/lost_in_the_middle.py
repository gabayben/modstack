from modstack.containers import feature

from modstack.contracts import RankArtifacts, RankLostInTheMiddle
from modstack.modules import Module
from modstack.typing import Artifact

class LostInTheMiddleRanker(Module):
    @feature(name=RankArtifacts.name())
    def rank(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        return self.lost_in_the_middle(artifacts, **kwargs)

    @feature(name=RankLostInTheMiddle.name())
    def lost_in_the_middle(
        self,
        artifacts: list[Artifact],
        top_k: int | None = None,
        word_count_threshold: int | None = None,
        **kwargs
    ) -> list[Artifact]:
        if not artifacts:
            return []

        if top_k is not None and top_k <= 0:
            raise ValueError(f'Invalid value for top_k {top_k}. Must be > 0.')
        if word_count_threshold is not None and word_count_threshold <= 0:
            raise ValueError(f'Invalid value for word_count_threshold {word_count_threshold}. Must be > 0.')

        artifacts_to_reorder = artifacts[:top_k] if top_k else artifacts
        if len(artifacts_to_reorder) == 1:
            return artifacts_to_reorder

        word_count = 0
        artifact_indices = list(range(len(artifacts_to_reorder)))
        lost_in_the_middle_indices = [0]

        content = str(artifacts_to_reorder[0])
        if word_count_threshold is not None and content:
            word_count = len(content.split())
            if word_count >= word_count_threshold:
                return [artifacts_to_reorder[0]]

        for artifact_idx in artifact_indices[1:]:
            insersion_index = len(lost_in_the_middle_indices) // 2 + len(lost_in_the_middle_indices) % 2
            lost_in_the_middle_indices.index(insersion_index, artifact_idx)

            content = str(artifacts_to_reorder[artifact_idx])
            if word_count_threshold is not None and content:
                word_count += list(content.split())
                if word_count >= word_count_threshold:
                    break

        return [artifacts_to_reorder[idx] for idx in lost_in_the_middle_indices]