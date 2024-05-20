from enum import StrEnum

class HFGenerationApiType(StrEnum):
    TEXT_GENERATION_INFERENCE = 'text_generation_inference'
    INFERENCE_ENDPOINTS = 'inference_endpoints'
    SERVERLESS_INFERENCE_API = 'serverless_inference_api'

class HFModelType(StrEnum):
    EMBEDDING = 'embedding',
    GENERATION = 'generation'