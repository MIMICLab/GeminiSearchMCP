"""Login-based Gemini client that reuses Gemini CLI OAuth credentials."""

from __future__ import annotations

import json
import time
import uuid
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.genai import types as genai_types

GEMINI_DIR = Path.home() / ".gemini"
OAUTH_CREDS_PATH = GEMINI_DIR / "oauth_creds.json"
PROJECT_CACHE_PATH = GEMINI_DIR / "project_cache.json"

CLIENT_ID_ENV = "GEMINI_MCP_CLIENT_ID"
CLIENT_SECRET_ENV = "GEMINI_MCP_CLIENT_SECRET"
TOKEN_URI = "https://oauth2.googleapis.com/token"
DEFAULT_LOCATION = "us-central1"

CODE_ASSIST_ENDPOINT = "https://cloudcode-pa.googleapis.com"
CODE_ASSIST_VERSION = "v1internal"

OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


class LoginClientError(RuntimeError):
    """Raised when login-based authentication fails."""


def _get_client_credentials() -> tuple[str, str]:
    client_id = os.environ.get(CLIENT_ID_ENV)
    client_secret = os.environ.get(CLIENT_SECRET_ENV)
    if client_id and client_secret:
        return client_id, client_secret
    raise LoginClientError(
        "Login authentication requires Google OAuth client credentials. "
        f"Set {CLIENT_ID_ENV} and {CLIENT_SECRET_ENV} in your environment "
        "using the same values that the Gemini CLI relies on."
    )


def _snake_to_camel(name: str) -> str:
    if "_" not in name:
        return name
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() or "_" for part in rest)


def _convert_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {_snake_to_camel(k): _convert_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_keys(item) for item in value]
    return value


def _normalise_contents(contents: Any) -> list[dict[str, Any]]:
    def ensure_content(item: Any) -> dict[str, Any]:
        if isinstance(item, str):
            return {"role": "user", "parts": [{"text": item}]}
        if hasattr(item, "model_dump"):
            return _convert_keys(item.model_dump(exclude_none=True))
        if isinstance(item, dict):
            return _convert_keys(item)
        raise LoginClientError(f"Unsupported content item type: {type(item)!r}")

    if isinstance(contents, str):
        return [ensure_content(contents)]
    if isinstance(contents, Iterable):
        converted = []
        for item in contents:  # type: ignore[arg-type]
            converted.append(ensure_content(item))
        return converted
    raise LoginClientError(f"Unsupported contents type: {type(contents)!r}")


def _build_generation_payload(config: genai_types.GenerateContentConfig | None) -> tuple[dict[str, Any], dict[str, Any]]:
    if config is None:
        return {}, {}

    raw = config.model_dump(exclude_none=True)
    generation_keys = {
        "temperature",
        "top_p",
        "top_k",
        "candidate_count",
        "max_output_tokens",
        "stop_sequences",
        "response_logprobs",
        "logprobs",
        "presence_penalty",
        "frequency_penalty",
        "seed",
        "response_mime_type",
        "response_schema",
        "response_json_schema",
        "routing_config",
        "model_selection_config",
        "response_modalities",
        "media_resolution",
        "speech_config",
        "audio_timestamp",
        "thinking_config",
        "automatic_function_calling",
    }

    request_section: dict[str, Any] = {}
    generation_section: dict[str, Any] = {}

    for key, value in raw.items():
        if key in generation_keys:
            generation_section[_snake_to_camel(key)] = _convert_keys(value)
            continue
        if key == "tools":
            request_section["tools"] = _convert_keys(value)
            continue
        if key == "tool_config":
            request_section["toolConfig"] = _convert_keys(value)
            continue
        if key == "labels":
            request_section["labels"] = value
            continue
        if key == "safety_settings":
            request_section["safetySettings"] = _convert_keys(value)
            continue
        if key == "cached_content":
            request_section["cachedContent"] = value
            continue
        if key == "system_instruction":
            request_section["systemInstruction"] = _convert_keys(value)
            continue
        request_section[_snake_to_camel(key)] = _convert_keys(value)

    return request_section, generation_section


def _load_credentials() -> tuple[Credentials, dict[str, Any]]:
    if not OAUTH_CREDS_PATH.exists():
        raise LoginClientError(
            f"OAuth credentials not found at {OAUTH_CREDS_PATH}. "
            "Run `gemini auth login` to create login credentials."
        )
    data = json.loads(OAUTH_CREDS_PATH.read_text(encoding="utf-8"))
    client_id, client_secret = _get_client_credentials()
    scopes = data.get("scope", "")
    scope_list = [scope for scope in scopes.split() if scope] or OAUTH_SCOPES
    creds = Credentials(
        token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scope_list,
    )
    if not creds.valid:
        creds.refresh(Request())
        data = _persist_credentials(creds, data)
    return creds, data


def _persist_credentials(creds: Credentials, original_payload: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(creds.to_json())
    # Preserve id_token if it existed originally, since Credentials.to_json may omit it.
    if original_payload.get("id_token") and "id_token" not in payload:
        payload["id_token"] = original_payload["id_token"]
    payload.setdefault("scope", original_payload.get("scope", ""))
    OAUTH_CREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    OAUTH_CREDS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _authorised_session(creds: Credentials) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"})
    return session


def _request(
    session: requests.Session,
    method: str,
    *,
    payload: dict[str, Any] | None = None,
    stream: bool = False,
) -> requests.Response:
    url = f"{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_VERSION}:{method}"
    response = session.post(url, json=payload, stream=stream, timeout=60)
    if response.status_code == 401:
        raise LoginClientError("Authentication failed when calling Gemini Code Assist API.")
    if response.status_code >= 400:
        message = response.text
        raise LoginClientError(f"Gemini Code Assist API error ({response.status_code}): {message}")
    return response


def _load_project_id(session: requests.Session, creds: Credentials) -> str:
    if PROJECT_CACHE_PATH.exists():
        try:
            cached = json.loads(PROJECT_CACHE_PATH.read_text(encoding="utf-8"))
            project = cached.get("project")
            if project:
                return project
        except json.JSONDecodeError:
            pass

    payload = {
        "cloudaicompanionProject": None,
        "metadata": {
            "ideType": "IDE_UNSPECIFIED",
            "platform": "PLATFORM_UNSPECIFIED",
            "pluginType": "GEMINI",
        },
    }
    load_response = _request(session, "loadCodeAssist", payload=payload).json()
    project = load_response.get("cloudaicompanionProject")
    if project:
        PROJECT_CACHE_PATH.write_text(json.dumps({"project": project}), encoding="utf-8")
        return project

    allowed = load_response.get("allowedTiers", [])
    tier = next((item for item in allowed if item.get("isDefault")), allowed[0] if allowed else None)
    if not tier:
        raise LoginClientError("Unable to determine onboarding tier for Gemini Code Assist.")

    metadata = {
        "ideType": "IDE_UNSPECIFIED",
        "platform": "PLATFORM_UNSPECIFIED",
        "pluginType": "GEMINI",
    }
    env_project_value = os.environ.get("GOOGLE_CLOUD_PROJECT")
    project_value = None
    if tier.get("userDefinedCloudaicompanionProject") and env_project_value:
        project_value = env_project_value
        metadata["duetProject"] = env_project_value

    onboard_payload = {
        "tierId": tier["id"],
        "cloudaicompanionProject": project_value,
        "metadata": metadata,
    }

    for _ in range(60):
        onboard_response = _request(session, "onboardUser", payload=onboard_payload).json()
        if onboard_response.get("done"):
            break
        time.sleep(5)
    else:
        raise LoginClientError("Timed out waiting for Gemini onboarding to complete.")

    response_payload = onboard_response.get("response", {})
    project = response_payload.get("cloudaicompanionProject", {}).get("id") or project_value
    if not project:
        raise LoginClientError(
            "Gemini onboarding completed but no project was returned. "
            "Set GOOGLE_CLOUD_PROJECT to your Cloud project and retry."
        )
    PROJECT_CACHE_PATH.write_text(json.dumps({"project": project}), encoding="utf-8")
    return project


@dataclass(slots=True)
class _ModelInvoker:
    credentials: Credentials
    project: str
    credential_payload: dict[str, Any]
    location: str = DEFAULT_LOCATION

    def generate_content(
        self,
        *,
        model: str,
        contents: Any,
        config: genai_types.GenerateContentConfig | None = None,
        **_: Any,
    ) -> genai_types.GenerateContentResponse:
        if not self.credentials.valid:
            self.credentials.refresh(Request())
            self.credential_payload = _persist_credentials(self.credentials, self.credential_payload)

        session = _authorised_session(self.credentials)
        request_payload, generation_payload = _build_generation_payload(config)
        request_payload["contents"] = _normalise_contents(contents)
        if generation_payload:
            request_payload["generationConfig"] = generation_payload

        user_prompt_id = uuid.uuid4().hex
        body = {
            "model": model,
            "project": self.project,
            "user_prompt_id": user_prompt_id,
            "request": request_payload,
        }

        response = _request(session, "generateContent", payload=body)
        data = response.json()
        try:
            return genai_types.GenerateContentResponse.model_validate(data["response"])
        except Exception as exc:  # noqa: BLE001
            raise LoginClientError(f"Failed to parse Gemini response: {exc}") from exc


class LoginGeminiClient:
    """Mimics the public interface of google-genai Client.models for login auth."""

    def __init__(self) -> None:
        creds, payload = _load_credentials()
        session = _authorised_session(creds)
        project = _load_project_id(session, creds)
        self._credentials = creds
        self._project = project
        self.models = _ModelInvoker(self._credentials, self._project, payload)


def create_login_client() -> LoginGeminiClient:
    """Factory returning a login-auth Gemini client."""
    return LoginGeminiClient()


__all__ = ["LoginGeminiClient", "LoginClientError", "create_login_client"]
