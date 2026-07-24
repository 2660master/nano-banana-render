"""
Beta API client for Nanode Blender addon.
Communicates with the Nanode Beta Server instead of Google API directly.
No Google API key is stored or used on the client side.
"""

import json
import base64
import os
import tempfile
from typing import Optional, Tuple
from urllib.parse import urlencode
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError


def _get_server_url() -> str:
    """Get the production server URL."""
    return "https://api.nanode.tech"


def _get_token() -> str:
    """Get the beta token from addon preferences."""
    import bpy
    prefs = bpy.context.preferences.addons.get("nano_banana_render")
    if prefs and hasattr(prefs.preferences, "beta_token"):
        return prefs.preferences.beta_token.strip()
    return ""


def _get_hwid() -> str:
    """Get the hardware ID from addon preferences."""
    import bpy
    prefs = bpy.context.preferences.addons.get("nano_banana_render")
    if prefs and hasattr(prefs.preferences, "hwid"):
        val = prefs.preferences.hwid
        if not val:
            from . import get_hwid_stable
            val = get_hwid_stable()
            prefs.preferences.hwid = val
        return val
    from . import get_hwid_stable
    return get_hwid_stable()


def _get_eu_format() -> bool:
    """Check if the user consented to European format data collection."""
    import bpy
    prefs = bpy.context.preferences.addons.get("nano_banana_render")
    if prefs and hasattr(prefs.preferences, "eu_format"):
        return prefs.preferences.eu_format
    return True


def _encode_file(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


def _get_addon_versions() -> tuple[str, str]:
    import bpy

    blender_version = bpy.app.version_string
    addon_version = "unknown"
    try:
        import addon_utils
        for mod in addon_utils.modules():
            if mod.__name__ == "nano_banana_render":
                vers = mod.bl_info.get("version", (0, 0, 0))
                addon_version = ".".join(str(v) for v in vers)
                break
    except Exception:
        pass
    return blender_version, addon_version


def _post(endpoint: str, data: dict, timeout: int = 120) -> dict:
    """POST JSON to server endpoint. Returns parsed response."""
    url = f"{_get_server_url()}{endpoint}"
    payload = json.dumps(data).encode("utf-8")

    req = urllib_request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        # Parse server error message
        try:
            body = json.loads(e.read().decode("utf-8"))
            detail = body.get("detail", str(e))
        except ValueError:
            detail = str(e)
        raise BetaAPIError(e.code, detail)
    except URLError as e:
        raise BetaAPIError(0, f"Cannot connect to server: {e.reason}")
    except Exception as e:
        raise BetaAPIError(0, f"Network error: {str(e)}")


def _get(endpoint: str, timeout: int = 10) -> dict:
    """GET from server endpoint. Returns parsed response."""
    url = f"{_get_server_url()}{endpoint}"
    req = urllib_request.Request(url, method="GET")

    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            detail = body.get("detail", str(e))
        except ValueError:
            detail = str(e)
        raise BetaAPIError(e.code, detail)
    except URLError as e:
        raise BetaAPIError(0, f"Cannot connect to server: {e.reason}")
    except Exception as e:
        raise BetaAPIError(0, f"Network error: {str(e)}")


class BetaAPIError(Exception):
    """Error from the beta server."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def is_invalid_token_error(error: BetaAPIError) -> bool:
    message = str(error.message).lower()
    return (
        error.status_code in {401, 403}
        or "invalid api key" in message
        or "invalid beta token" in message
        or "beta token" in message
    )


def validate_nanode_token() -> dict:
    token = _get_token()
    if not token.startswith("nk_"):
        raise BetaAPIError(401, "Nanode login required")
    query = urlencode({"token": token, "hwid": _get_hwid()})
    return _get(f"/api/balance?{query}", timeout=10)


# ─── Public API ───────────────────────────────────────────────

def generate(
    prompt: str,
    model: str,
    input_image_path: str,
    reference_image_path: Optional[str] = None,
    mask_image_path: Optional[str] = None,
    gen_type: str = "render_depth",
    width: int = 1024,
    height: int = 1024,
    user_prompt: Optional[str] = None,
    is_smart_points: bool = False,
) -> Tuple[bytes, int, int]:
    """
    Generate an AI image via the beta server.

    Args:
        prompt: Full system prompt sent to the AI
        model: Model name (e.g. 'gemini-3-pro-image')
        input_image_path: Path to the input render / depth map
        reference_image_path: Optional style reference image path
        mask_image_path: Optional inpaint mask path
        gen_type: 'render_depth', 'render_eevee', or 'inpaint'
        width: Generation width limit
        height: Generation height limit
        user_prompt: The user's original prompt text (before system template)

    Returns:
        (...)
    """
    token = _get_token()
    if not token:
        raise BetaAPIError(401, "No beta token configured. Go to Edit → Preferences → Add-ons → Nano Banana")

    input_b64 = _encode_file(input_image_path)

    ref_b64 = None
    if reference_image_path:
        try:
            ref_b64 = _encode_file(reference_image_path)
        except Exception as e:
            print(f"[BETA API] Failed to read reference image: {e}")

    mask_b64 = None
    if mask_image_path:
        try:
            mask_b64 = _encode_file(mask_image_path)
        except Exception as e:
            print(f"[BETA API] Failed to read mask image: {e}")

    hwid = _get_hwid()

    # Get versions for telemetry
    blender_version, addon_version = _get_addon_versions()

    data = {
        "token": token,
        "prompt": prompt,
        "user_prompt": user_prompt,
        "model": model,
        "input_image": input_b64,
        "reference_image": ref_b64,
        "mask_image": mask_b64,
        "gen_type": gen_type,
        "width": width,
        "height": height,
        "hwid": hwid,
        "eu_format": _get_eu_format(),
        "addon_version": addon_version,
        "blender_version": blender_version,
        "is_smart_points": is_smart_points,
    }

    print(f"[BETA API] Sending generation request ({gen_type}, model={model})")
    resp = _post("/generate", data, timeout=120)

    # Decode the returned image
    image_bytes = base64.b64decode(resp["image"])
    generation_id = resp.get("generation_id", 0)
    balance = resp.get("balance", 0)

    print(f"[BETA API] Generation #{generation_id} received, balance: {balance}")
    return image_bytes, generation_id, balance


def create_video_job(
    prompt: str,
    model: str,
    task: str,
    duration_seconds: int,
    resolution: str,
    aspect_ratio: str = "16:9",
    input_image_path: Optional[str] = None,
    last_frame_image_path: Optional[str] = None,
    reference_image_paths: Optional[list[str]] = None,
    video_path: Optional[str] = None,
    previous_interaction_id: Optional[str] = None,
    request_id: Optional[str] = None,
    match_source_duration: bool = False,
) -> dict:
    """Create a Nanode video job and reserve credits on the server."""
    token = _get_token()
    if not token:
        raise BetaAPIError(401, "No Nanode token configured")

    blender_version, addon_version = _get_addon_versions()
    references = []
    for path in reference_image_paths or []:
        try:
            encoded = _encode_file(path)
            if encoded:
                references.append(encoded)
        except Exception as exc:
            print(f"[BETA API] Failed to read video reference {path}: {exc}")

    data = {
        "token": token,
        "prompt": prompt,
        "model": model,
        "task": task,
        "duration_seconds": int(duration_seconds),
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "input_image": _encode_file(input_image_path),
        "last_frame_image": _encode_file(last_frame_image_path),
        "reference_images": references,
        "video": _encode_file(video_path),
        "previous_interaction_id": previous_interaction_id,
        "request_id": request_id,
        "match_source_duration": bool(match_source_duration),
        "hwid": _get_hwid(),
        "addon_version": addon_version,
        "blender_version": blender_version,
    }

    print(f"[BETA API] Creating video job ({model}, {task}, {resolution}, {duration_seconds}s)")
    return _post("/api/video/jobs", data, timeout=60)


def get_video_job(job_id: int) -> dict:
    token = _get_token()
    if not token:
        raise BetaAPIError(401, "No Nanode token configured")
    query = urlencode({"token": token, "hwid": _get_hwid()})
    return _get(f"/api/video/jobs/{int(job_id)}?{query}", timeout=15)


def list_video_jobs() -> list[dict]:
    token = _get_token()
    if not token or not token.startswith("nk_"):
        return []
    query = urlencode({"token": token, "hwid": _get_hwid()})
    response = _get(f"/api/video/jobs?{query}", timeout=20)
    return list(response.get("jobs") or [])


def download_video_result(output_url: str, job_id: int = 0) -> str:
    if not output_url:
        raise BetaAPIError(404, "Video result URL is empty")

    url = output_url if output_url.startswith("http") else f"{_get_server_url()}{output_url}"
    clean_path = url.split("?", 1)[0]
    ext = os.path.splitext(clean_path)[1].lower()
    if ext not in {".mp4", ".mov", ".mkv", ".webm"}:
        ext = ".mp4"

    output_dir = os.path.join(tempfile.gettempdir(), "nanode_blender", "videos")
    os.makedirs(output_dir, exist_ok=True)
    safe_id = int(job_id or 0)
    if safe_id <= 0:
        safe_id = abs(hash(output_url)) % 100000000
    output_path = os.path.join(output_dir, f"nanode_video_job_{safe_id}{ext}")

    req = urllib_request.Request(url, method="GET")
    try:
        with urllib_request.urlopen(req, timeout=300) as resp:
            data = resp.read()
    except HTTPError as e:
        raise BetaAPIError(e.code, f"Video download failed: HTTP {e.code}")
    except URLError as e:
        raise BetaAPIError(0, f"Video download failed: {e.reason}")
    except Exception as e:
        raise BetaAPIError(0, f"Video download failed: {str(e)}")

    if len(data) < 1024:
        raise BetaAPIError(502, "Downloaded video is empty")

    with open(output_path, "wb") as file:
        file.write(data)
    return output_path


def get_balance() -> int:
    """Fetch remaining generations/credits from server."""
    token = _get_token()
    if not token:
        return -1

    try:
        query = urlencode({"token": token, "hwid": _get_hwid()})
        resp = _get(f"/api/balance?{query}")
        return resp.get("balance", 0)
    except BetaAPIError:
        return -1


def get_balance_info() -> dict:
    """Fetch balance + feedback_given flag from server."""
    token = _get_token()
    if not token:
        return {"balance": -1, "feedback_given": False}

    try:
        query = urlencode({"token": token, "hwid": _get_hwid()})
        resp = _get(f"/api/balance?{query}")
        return {
            "balance": resp.get("balance", 0),
            "feedback_given": resp.get("feedback_given", False),
        }
    except BetaAPIError:
        return {"balance": -1, "feedback_given": False}


def get_credit_info() -> dict:
    """Get full balance info including user_type, pricing, store_url."""
    token = _get_token()
    if not token:
        return {"balance": -1, "user_type": "unknown"}

    try:
        query = urlencode({"token": token, "hwid": _get_hwid()})
        resp = _get(f"/api/balance?{query}")
        return resp
    except BetaAPIError:
        return {"balance": -1, "user_type": "unknown"}


def send_rating(generation_id: int, rating: str) -> bool:
    """Send a like/dislike rating for a generation."""
    token = _get_token()
    if not token:
        return False

    hwid = _get_hwid()

    try:
        _post("/rate", {
            "token": token,
            "generation_id": generation_id,
            "rating": rating,
            "hwid": hwid,
        }, timeout=10)
        print(f"[BETA API] Rated generation #{generation_id}: {rating}")
        return True
    except BetaAPIError as e:
        print(f"[BETA API] Rating failed: {e.message}")
        return False


def send_feedback(text: str) -> int:
    """Submit feedback text. Returns new balance (or -1 on error)."""
    token = _get_token()
    if not token:
        raise BetaAPIError(401, "No beta token configured")

    hwid = _get_hwid()

    resp = _post("/feedback", {
        "token": token,
        "text": text,
        "hwid": hwid,
    }, timeout=10)

    new_balance = resp.get("balance", 0)
    print(f"[BETA API] Feedback submitted, +{resp.get('bonus', 50)} gens, balance: {new_balance}")
    return new_balance
