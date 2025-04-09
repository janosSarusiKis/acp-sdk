# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Optional, TypedDict

from pydantic import BaseModel, Field

from manifest_generator import ManifestMarker


class MsgType(Enum):
    human = "human"
    assistant = "assistant"


class Message(BaseModel):
    type: MsgType = Field(
        ...,
        description="indicates the originator of the message, a human or an assistant",
    )
    content: str = Field(..., description="the content of the message")

@ManifestMarker.config
class ConfigSchema(TypedDict):
    to_upper: bool
    to_lower: bool

@ManifestMarker.input
class InputState(BaseModel):
    messages: Optional[list[Message]] = None

@ManifestMarker.output
class OutputState(BaseModel):
    messages: Optional[list[Message]] = None


class AgentState(BaseModel):
    echo_input: InputState
    echo_output: Optional[OutputState] = None
