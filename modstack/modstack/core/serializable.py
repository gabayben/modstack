from pydantic import BaseModel

class Serializable(BaseModel):
    class Config:
        extra = 'allow'
        arbitrary_types_allowed = True