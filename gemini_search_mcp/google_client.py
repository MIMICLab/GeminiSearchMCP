"""Helpers for constructing Gemini API clients."""

from __future__ import annotations

import functools
import os
from typing import Any

from google import genai
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

from .config import GOOGLE_API_KEY_ENV
from .login_client import LoginClientError, create_login_client


class GeminiClientError(RuntimeError):
    """Raised when a Gemini client cannot be constructed."""


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "t", "yes", "on"}


@functools.lru_cache(maxsize=1)
def get_gemini_client(**kwargs: Any) -> genai.Client:
    api_key = kwargs.pop("api_key", None) or os.environ.get(GOOGLE_API_KEY_ENV)
    if api_key:
        return genai.Client(api_key=api_key, **kwargs)

    requested_vertex = kwargs.pop("vertexai", None)
    env_vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI")
    use_vertex = requested_vertex if requested_vertex is not None else _is_truthy(env_vertex)

    credentials = kwargs.pop("credentials", None)
    project = kwargs.pop("project", None) or os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = kwargs.pop("location", None) or os.environ.get("GOOGLE_CLOUD_LOCATION")

    try:
        if credentials is None:
            credentials, default_project = google_auth_default()
        else:
            default_project = None
    except DefaultCredentialsError:
        credentials = None
        default_project = None

    if credentials is not None:
        project = project or default_project
        if use_vertex or project:
            if not location:
                location = "us-central1"
            try:
                return genai.Client(
                    vertexai=True,
                    project=project,
                    location=location,
                    credentials=credentials,
                    **kwargs,
                )
            except Exception:
                # Fall back to login client below.
                pass

    if kwargs:
        raise GeminiClientError(f"Unsupported arguments for login authentication: {', '.join(kwargs.keys())}")

    try:
        return create_login_client()
    except LoginClientError as exc:
        raise GeminiClientError(
            f"Google API key missing; set {GOOGLE_API_KEY_ENV} or configure login auth via `gemini auth login`."
        ) from exc


__all__ = ["get_gemini_client", "GeminiClientError"]
