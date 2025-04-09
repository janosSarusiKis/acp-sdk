# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from manifest_generator import ManifestMarker


class Type(Enum):
    human = 'human'
    assistant = 'assistant'
    ai = 'ai'


class Message(BaseModel):
    type: Type = Field(
        ...,
        description='indicates the originator of the message, a human or an assistant',
    )
    content: str = Field(..., description='the content of the message')


@ManifestMarker.config
class ConfigSchema(BaseModel):
    test: bool


@ManifestMarker.input
class AgentState(BaseModel):
    messages: Optional[list[Message]] = None
    is_completed: Optional[bool] = None

@ManifestMarker.output
class OutputState(AgentState):
    final_email: Optional[str] = Field(default=None, description="Final email produced by the mail composer")
