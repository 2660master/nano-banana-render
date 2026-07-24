#!/usr/bin/env python3
"""Check whether a Google Gemini credential works with the Generative Language API."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    status: int
    body: dict[str, Any] | None
    text: str


def redact(value: str) -> str:
    value = value.strip()
    if len(value) <= 12:
        return "***"
    return f"{value[:6]}...{value[-4:]}"


def looks_like_ai_studio_key(value: str) -> bool:
    return value.startswith(("AIza", "AQ.")) and len(value) >= 20


def load_credential() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    return getpass.getpass("Paste Gemini credential (hidden): ").strip()


def parse_json(data: bytes) -> tuple[dict[str, Any] | None, str]:
    text = data.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None, text
    return parsed, text


def call_google(
    credential: str,
    model: str,
    *,
    oauth_token: bool,
    quota_project: str,
    timeout: int,
) -> ApiResult:
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": "Return exactly: OK"}],
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 8,
        },
    }

    if oauth_token:
        url = f"{API_BASE}/models/{urllib.parse.quote(model)}:generateContent"
    else:
        query = urllib.parse.urlencode({"key": credential})
        url = f"{API_BASE}/models/{urllib.parse.quote(model)}:generateContent?{query}"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Client": "nanode-key-checker",
    }
    if oauth_token:
        headers["Authorization"] = f"Bearer {credential}"
        if quota_project:
            headers["X-Goog-User-Project"] = quota_project

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body, text = parse_json(response.read())
            return ApiResult(True, response.status, body, text)
    except urllib.error.HTTPError as exc:
        body, text = parse_json(exc.read())
        return ApiResult(False, exc.code, body, text)
    except urllib.error.URLError as exc:
        return ApiResult(False, 0, None, str(exc.reason))


def extract_error(result: ApiResult) -> str:
    if result.body:
        error = result.body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message:
                return message
        return json.dumps(result.body, ensure_ascii=False)[:500]
    return result.text[:500]


def extract_response_text(result: ApiResult) -> str:
    if not result.body:
        return ""
    candidates = result.body.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""
    content = candidates[0].get("content")
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""
    texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    return " ".join(text.strip() for text in texts if text.strip())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Google Gemini API key or OAuth token without storing it.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Text model used for the smoke test. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--oauth-token",
        action="store_true",
        help="Treat the credential as an OAuth bearer token instead of an API key.",
    )
    parser.add_argument(
        "--quota-project",
        default=os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT", "").strip(),
        help="Optional quota project for OAuth bearer-token checks.",
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    credential = load_credential()
    if not credential:
        print("FAIL: empty credential")
        return 2

    is_ai_studio_key = looks_like_ai_studio_key(credential)
    mode = "OAuth bearer token" if args.oauth_token else "API key"

    print(f"Credential: {redact(credential)}")
    print(f"Mode: {mode}")
    print(f"Addon personal Google key format: {'yes' if is_ai_studio_key else 'no'}")
    if not args.oauth_token and not is_ai_studio_key:
        print("Note: Nanode recognizes Google AI Studio keys that start with AIza or AQ.")

    result = call_google(
        credential,
        args.model,
        oauth_token=args.oauth_token,
        quota_project=args.quota_project,
        timeout=args.timeout,
    )

    if result.ok:
        response_text = extract_response_text(result)
        print(f"Google API smoke test: OK HTTP {result.status}")
        if response_text:
            print(f"Model response: {response_text}")
        return 0

    print(f"Google API smoke test: FAIL HTTP {result.status}")
    print(f"Error: {extract_error(result)}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
