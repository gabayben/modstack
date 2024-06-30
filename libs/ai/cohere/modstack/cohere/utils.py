from typing import Any

import cohere

def build_cohore_metadata(metadata: dict[str, Any], response: cohere.StreamedChatResponse | cohere.NonStreamedChatResponse) -> None:
    if response:
        if response.meta:
            if response.meta.billed_units:
                in_tokens = response.meta.billed_units.prompt_tokens or -1
                out_tokens = response.meta.billed_units.completion_tokens or -1
                metadata['in_tokens'] = in_tokens
                metadata['out_tokens'] = out_tokens
                metadata['usage'] = in_tokens + out_tokens
        metadata.update({
            'index': 0,
            'documents': response.documents,
            'citations': response.citations,
            'finish_reason': response.finish_reason
        })