# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
from enum import Enum
from typing import Any, Optional

from manifest_generator import ManifestMarker
from pydantic import BaseModel, Field, RootModel


class TargetAudience(Enum):
    general = 'general'
    technical = 'technical'
    business = 'business'
    academic = 'academic'

@ManifestMarker.input
class EmailReviewerInput(BaseModel):
    email: str = Field(
        ..., description='The email content to be reviewed and corrected'
    )
    target_audience: TargetAudience = Field(
        ...,
        description='The target audience for the email, affecting the style of review',
    )

@ManifestMarker.output
class EmailReview(BaseModel):
    correct: bool = Field(
        ...,
        description='Indicates whether the email is correct and requires no changes',
    )
    corrected_email: Optional[str] = Field(
        None,
        description='The corrected version of the email, if changes were necessary',
    )

@ManifestMarker.config
class ConfigSchema(RootModel[Any]):
    root: Any