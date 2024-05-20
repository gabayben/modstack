from enum import StrEnum
from typing import Literal

class HFGenerationApiType(StrEnum):
    TEXT_GENERATION_INFERENCE = 'text_generation_inference'
    INFERENCE_ENDPOINTS = 'inference_endpoints'
    SERVERLESS_INFERENCE_API = 'serverless_inference_api'

class HFModelType(StrEnum):
    EMBEDDING = 'embedding',
    GENERATION = 'generation'

HFTextGenerationTask = Literal['text-generation', 'text2text-generation']