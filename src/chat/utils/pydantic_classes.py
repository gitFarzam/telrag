from pydantic import BaseModel,Field
from typing import Literal,List

class CategorzingModel(BaseModel):
    result: Literal[0, 1, 2, 3]

class KeywordModel(BaseModel):
    result: List[str] = Field(
        ...,
        min_length=2,
        max_length=5
    )

class BooleanModel(BaseModel):
    result : bool