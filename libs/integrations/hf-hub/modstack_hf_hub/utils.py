from huggingface_hub import HfApi
from huggingface_hub.utils import RepositoryNotFoundError

from modstack.auth import Secret
from modstack_hf_hub import HFModelType

def validate_hf_model(
    model_id: str,
    model_type: HFModelType,
    secret: Secret | None
) -> None:
    api = HfApi()
    try:
        model_info = api.model_info(model_id, token=secret.resolve_value() if secret else None)
    except RepositoryNotFoundError as e:
        raise ValueError(
            f'Model {model_id} not found on HuggingFace Hub. Please provide a valid HuggingFace model_id.'
        ) from e
    if model_type == HFModelType.EMBEDDING:
        allowed_model = model_info.pipeline_tag in ['sentence-similarity', 'feature-extraction']
        error_msg = f'Model {model_id} is not an embedding model. Please provide a valid embedding model.'
    else:
        allowed_model = model_info.pipeline_tag in ['text-generation', 'text2text-generation']
        error_msg = f'Model {model_id} is not a text generation model. Please provide a valid text generation model.'
    if not allowed_model:
        raise ValueError(error_msg)