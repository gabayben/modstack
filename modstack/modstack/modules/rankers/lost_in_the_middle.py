from modstack.modules.rankers import RankLostInTheMiddle
from modstack.modules import Modules
from modstack.typing import Artifact

class LostInTheMiddleRanker(Modules.Sync[RankLostInTheMiddle, list[Artifact]]):
    def _invoke(self, data: RankLostInTheMiddle, **kwargs) -> list[Artifact]:
        if not data.artifacts:
            return []

        if data.top_k is not None and data.top_k <= 0:
            raise ValueError(f'Invalid value for top_k {data.top_k}. Must be > 0.')
        if data.word_count_threshold is not None and data.word_count_threshold <= 0:
            raise ValueError(f'Invalid value for word_count_threshold {data.word_count_threshold}. Must be > 0.')

        artifacts_to_reorder = data.artifacts[:data.top_k] if data.top_k else data.artifacts
        if len(artifacts_to_reorder) == 1:
            return artifacts_to_reorder

        word_count = 0
        artifact_indices = list(range(len(artifacts_to_reorder)))
        lost_in_the_middle_indices = [0]

        content = str(artifacts_to_reorder[0])
        if data.word_count_threshold is not None and content:
            word_count = len(content.split())
            if word_count >= data.word_count_threshold:
                return [artifacts_to_reorder[0]]

        for artifact_idx in artifact_indices[1:]:
            insersion_index = len(lost_in_the_middle_indices) // 2 + len(lost_in_the_middle_indices) % 2
            lost_in_the_middle_indices.index(insersion_index, artifact_idx)

            content = str(artifacts_to_reorder[artifact_idx])
            if data.word_count_threshold is not None and content:
                word_count += list(content.split())
                if word_count >= data.word_count_threshold:
                    break

        return [artifacts_to_reorder[idx] for idx in lost_in_the_middle_indices]