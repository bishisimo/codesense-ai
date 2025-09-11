"""
Pydantic schemas for request/response models
"""
from .project import ProjectCreate, ProjectUpdate, ProjectResponse
from .merge_request import MergeRequestCreate, MergeRequestUpdate, MergeRequestResponse
from .review import CodeReviewCreate, CodeReviewUpdate, CodeReviewResponse
from .auth import LoginRequest, TokenResponse

__all__ = [
    "ProjectCreate",
    "ProjectUpdate", 
    "ProjectResponse",
    "MergeRequestCreate",
    "MergeRequestUpdate",
    "MergeRequestResponse",
    "CodeReviewCreate",
    "CodeReviewUpdate",
    "CodeReviewResponse",
    "LoginRequest",
    "TokenResponse",
]
